import pytest
from unittest.mock import patch, MagicMock
from coc_elt.main import run_pipeline

@patch("coc_elt.main.settings")
@patch("coc_elt.main.CocApiClient")
@patch("coc_elt.main.BigQueryIngester")
def test_run_pipeline_success(mock_ingester_cls, mock_api_client_cls, mock_settings):
    mock_settings.coc_apikey = "test-key"
    mock_settings.clan_tag = "#TEST"
    mock_settings.data_project_id = "test-project"
    mock_settings.dataset_id = "test_dataset"

    mock_api_client = MagicMock()
    mock_api_client_cls.return_value = mock_api_client
    mock_api_client.fetch_clan.return_value = {"tag": "#CLAN", "name": "Clan Name"}
    mock_api_client.fetch_members.return_value = {"items": [{"tag": "#M1", "name": "M1 Name"}]}
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_members.assert_called_once()
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()

    assert mock_ingester.ingest_batch.call_count == 4

@patch("coc_elt.main.settings")
@patch("coc_elt.main.CocApiClient")
@patch("coc_elt.main.BigQueryIngester")
def test_run_pipeline_partial_success_api_failure(mock_ingester_cls, mock_api_client_cls, mock_settings):
    mock_settings.coc_apikey = "test-key"
    mock_settings.clan_tag = "#TEST"
    mock_settings.data_project_id = "test-project"
    mock_settings.dataset_id = "test_dataset"

    mock_api_client = MagicMock()
    mock_api_client_cls.return_value = mock_api_client
    mock_api_client.fetch_clan.return_value = {"tag": "#CLAN", "name": "Clan Name"}
    mock_api_client.fetch_members.side_effect = Exception("API error")
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_members.assert_called_once()
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()

    assert mock_ingester.ingest_batch.call_count == 3

@patch("coc_elt.main.settings")
@patch("coc_elt.main.CocApiClient")
@patch("coc_elt.main.BigQueryIngester")
def test_run_pipeline_partial_success_validation_failure(mock_ingester_cls, mock_api_client_cls, mock_settings):
    mock_settings.coc_apikey = "test-key"
    mock_settings.clan_tag = "#TEST"
    mock_settings.data_project_id = "test-project"
    mock_settings.dataset_id = "test_dataset"

    mock_api_client = MagicMock()
    mock_api_client_cls.return_value = mock_api_client
    mock_api_client.fetch_clan.return_value = {"tag": "#CLAN"}
    mock_api_client.fetch_members.return_value = {"items": [{"tag": "#M1", "name": "M1 Name"}]}
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_members.assert_called_once()
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()

    assert mock_ingester.ingest_batch.call_count == 3
