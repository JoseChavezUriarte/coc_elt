import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from coc_elt.bq_client import BigQueryIngester

@patch("google.cloud.bigquery.Client")
def test_ingest_batch_success(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    
    mock_job = MagicMock()
    mock_job.errors = None
    
    captured_content = None
    def save_content(file_obj, *args, **kwargs):
        nonlocal captured_content
        file_obj.seek(0)
        captured_content = file_obj.read()
        return mock_job
        
    mock_bq_client.load_table_from_file.side_effect = save_content

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    naive_dt = datetime(2026, 7, 11, 12, 0, 0)
    records = [{"key": "val"}]
    ingester.ingest_batch("coc_clan", records, naive_dt)
    
    expected_table_id = "test-project.test_dataset.coc_clan"
    
    mock_bq_client.load_table_from_file.assert_called_once()
    args, kwargs = mock_bq_client.load_table_from_file.call_args
    
    parsed = json.loads(captured_content.decode("utf-8").strip())
    assert parsed["extracted_at"] == "2026-07-11T12:00:00+00:00"
    assert parsed["payload"] == {"key": "val"}
    
    assert args[1] == expected_table_id
    assert kwargs["job_config"].source_format == "NEWLINE_DELIMITED_JSON"
    assert kwargs["job_config"].write_disposition == "WRITE_APPEND"
    
    mock_job.result.assert_called_once()

@patch("google.cloud.bigquery.Client")
def test_ingest_batch_timezone_localization(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    mock_job = MagicMock()
    mock_job.errors = None
    
    captured_content = None
    def save_content(file_obj, *args, **kwargs):
        nonlocal captured_content
        file_obj.seek(0)
        captured_content = file_obj.read()
        return mock_job
        
    mock_bq_client.load_table_from_file.side_effect = save_content

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    from datetime import timedelta
    tz = timezone(timedelta(hours=2))
    aware_dt = datetime(2026, 7, 11, 14, 0, 0, tzinfo=tz)
    records = [{"key": "val"}]
    ingester.ingest_batch("coc_clan", records, aware_dt)
    
    parsed = json.loads(captured_content.decode("utf-8").strip())
    assert parsed["extracted_at"] == "2026-07-11T12:00:00+00:00"

@patch("google.cloud.bigquery.Client")
def test_ingest_batch_load_job_exception(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    
    mock_job = MagicMock()
    mock_job.result.side_effect = Exception("Google Cloud error")
    mock_bq_client.load_table_from_file.return_value = mock_job

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    dt = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError, match="BigQuery load job failed"):
        ingester.ingest_batch("coc_clan", [{"key": "val"}], dt)

@patch("google.cloud.bigquery.Client")
def test_ingest_batch_load_job_errors(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    
    mock_job = MagicMock()
    mock_job.errors = [{"message": "some insertion error"}]
    mock_bq_client.load_table_from_file.return_value = mock_job

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    dt = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError, match="BigQuery load job failed with errors"):
        ingester.ingest_batch("coc_clan", [{"key": "val"}], dt)
