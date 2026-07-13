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
    mock_api_client.fetch_clan.return_value = {
        "tag": "#CLAN",
        "name": "Clan Name",
        "memberList": [{"tag": "#M1", "name": "M1 Name"}]
    }
    mock_api_client.fetch_player.return_value = {"tag": "#M1", "name": "M1 Name"}
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}
    mock_api_client.fetch_league_group.return_value = {
        "state": "inWar",
        "season": "2026-07",
        "rounds": [{"warTags": ["#WAR1", "#0"]}]
    }
    mock_api_client.fetch_warleague_war.return_value = {"state": "warEnded"}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_player.assert_called_once_with("#M1")
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()
    mock_api_client.fetch_league_group.assert_called_once()
    mock_api_client.fetch_warleague_war.assert_called_once_with("#WAR1")

    # Ingests: clan, members, current_war, capital_raids, league_group, warleague_war
    assert mock_ingester.ingest_batch.call_count == 6

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
    mock_api_client.fetch_clan.return_value = {
        "tag": "#CLAN",
        "name": "Clan Name",
        "memberList": [{"tag": "#M1", "name": "M1 Name"}]
    }
    # Fail the player fetch API call
    mock_api_client.fetch_player.side_effect = Exception("API error")
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}
    mock_api_client.fetch_league_group.return_value = {
        "state": "inWar",
        "season": "2026-07",
        "rounds": [{"warTags": ["#WAR1"]}]
    }
    mock_api_client.fetch_warleague_war.return_value = {"state": "warEnded"}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_player.assert_called_once_with("#M1")
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()
    mock_api_client.fetch_league_group.assert_called_once()

    # Ingests: clan, current_war, capital_raids, league_group, warleague_war (members fails)
    assert mock_ingester.ingest_batch.call_count == 5

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
    # Clan step fails because tag or name is missing
    mock_api_client.fetch_clan.return_value = {"tag": "#CLAN"}  # missing name
    mock_api_client.fetch_player.return_value = {"tag": "#M1", "name": "M1 Name"}
    mock_api_client.fetch_current_war.return_value = {"state": "inWar"}
    mock_api_client.fetch_capital_raids.return_value = {"items": [{"state": "ongoing", "startTime": "2026-07-10T12:00:00Z"}]}
    mock_api_client.fetch_league_group.return_value = {
        "state": "inWar",
        "season": "2026-07",
        "rounds": [{"warTags": ["#WAR1"]}]
    }
    mock_api_client.fetch_warleague_war.return_value = {"state": "warEnded"}

    mock_ingester = MagicMock()
    mock_ingester_cls.return_value = mock_ingester

    with patch("coc_elt.main.is_capital_raid_day", return_value=True):
        run_pipeline()

    # fetch_clan is called once: for Clan step (it succeeds in fetching raw data, although validation fails, so it's not None and does not need to be refetched)
    mock_api_client.fetch_clan.assert_called_once()
    mock_api_client.fetch_current_war.assert_called_once()
    mock_api_client.fetch_capital_raids.assert_called_once()
    mock_api_client.fetch_league_group.assert_called_once()

    # Ingests: members (empty list), current_war, capital_raids, league_group, warleague_war (clan fails validation)
    assert mock_ingester.ingest_batch.call_count == 5
