import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from coc_elt.bq_client import BigQueryIngester

@patch("google.cloud.bigquery.Client")
def test_ingest_record_timezone_localization(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    mock_bq_client.insert_rows_json.return_value = []

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    naive_dt = datetime(2026, 7, 11, 12, 0, 0)
    payload = {"key": "val"}
    ingester.ingest_record("coc_clan", payload, naive_dt)
    
    expected_table_id = "test-project.test_dataset.coc_clan"
    expected_row = {
        "extracted_at": "2026-07-11T12:00:00+00:00",
        "payload": payload
    }
    mock_bq_client.insert_rows_json.assert_called_with(expected_table_id, [expected_row])

    from datetime import timedelta
    tz = timezone(timedelta(hours=2))
    aware_dt = datetime(2026, 7, 11, 14, 0, 0, tzinfo=tz)
    ingester.ingest_record("coc_clan", payload, aware_dt)
    
    mock_bq_client.insert_rows_json.assert_called_with(expected_table_id, [expected_row])

@patch("google.cloud.bigquery.Client")
def test_ingest_record_insertion_error(mock_bq_client_cls):
    mock_bq_client = MagicMock()
    mock_bq_client_cls.return_value = mock_bq_client
    mock_bq_client.insert_rows_json.return_value = [{"error": "some bigquery error"}]

    ingester = BigQueryIngester(project_id="test-project", dataset_id="test_dataset")
    
    dt = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError, match="BigQuery insertion failed"):
        ingester.ingest_record("coc_clan", {}, dt)
