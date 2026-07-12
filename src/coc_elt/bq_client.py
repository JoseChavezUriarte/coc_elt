import logging
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BigQueryIngester:
    def __init__(self, project_id: str, dataset_id: str):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id

    def ingest_record(self, table_name: str, payload: Dict[str, Any], extracted_at: datetime) -> None:
        """
        Ingests a JSON payload and its extraction timestamp into a partitioned table.
        """
        if extracted_at.tzinfo is None:
            extracted_at = extracted_at.replace(tzinfo=timezone.utc)
        else:
            extracted_at = extracted_at.astimezone(timezone.utc)

        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"

        row = {
            "extracted_at": extracted_at.isoformat(),
            "payload": payload
        }

        errors = self.client.insert_rows_json(table_id, [row])
        if errors:
            logger.error(
                "Errors occurred during BigQuery insertion",
                extra={
                    "table_name": table_name,
                    "table_id": table_id,
                    "errors": errors
                }
            )
            raise RuntimeError(f"BigQuery insertion failed: {errors}")

        logger.info(
            "Successfully ingested record into BigQuery",
            extra={
                "table_name": table_name,
                "table_id": table_id,
                "record_count": 1
            }
        )
