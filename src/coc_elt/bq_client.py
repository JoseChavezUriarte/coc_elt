import json
import logging
import tempfile
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BigQueryIngester:
    def __init__(self, project_id: str, dataset_id: str):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id

    def ingest_batch(self, table_name: str, records: List[Dict[str, Any]], extracted_at: datetime) -> None:
        if not records:
            logger.info("Empty batch, skipping ingestion for table %s", table_name)
            return

        if extracted_at.tzinfo is None:
            extracted_at = extracted_at.replace(tzinfo=timezone.utc)
        else:
            extracted_at = extracted_at.astimezone(timezone.utc)

        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"

        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json') as tmp_file:
            for record in records:
                row = {
                    "extracted_at": extracted_at.isoformat(),
                    "payload": record
                }
                tmp_file.write((json.dumps(row) + "\n").encode("utf-8"))
            
            tmp_file.flush()
            tmp_file.seek(0)

            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )

            logger.info(
                "Loading batch into BigQuery",
                extra={
                    "table_name": table_name,
                    "table_id": table_id,
                    "record_count": len(records)
                }
            )

            try:
                job = self.client.load_table_from_file(
                    tmp_file,
                    table_id,
                    job_config=job_config
                )
                job.result()
            except Exception as e:
                logger.error(
                    "BigQuery load job raised exception",
                    exc_info=e,
                    extra={
                        "table_name": table_name,
                        "table_id": table_id
                    }
                )
                raise RuntimeError(f"BigQuery load job failed: {e}") from e

            if job.errors:
                logger.error(
                    "Errors occurred during BigQuery load job",
                    extra={
                        "table_name": table_name,
                        "table_id": table_id,
                        "errors": job.errors
                    }
                )
                raise RuntimeError(f"BigQuery load job failed with errors: {job.errors}")

            logger.info(
                "Successfully loaded batch into BigQuery",
                extra={
                    "table_name": table_name,
                    "table_id": table_id,
                    "record_count": len(records)
                }
            )
