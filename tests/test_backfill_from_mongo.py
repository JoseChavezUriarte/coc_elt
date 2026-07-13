import json
import os
import subprocess
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from google.cloud import bigquery

from scripts.backfill_from_mongo import (
    clean_mongo_doc,
    extract_archive,
    get_extracted_at,
    load_table_data,
    make_dir_writable_for_docker,
    process_and_backfill,
    run_mongo_container,
    stop_and_remove_container,
)

# Test get_extracted_at
def test_get_extracted_at_datetime():
    dt = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
    doc = {"extracted_at": dt}
    assert get_extracted_at(doc) == dt

    naive_dt = datetime(2026, 7, 13, 12, 0, 0)
    doc_naive = {"extracted_at": naive_dt}
    assert get_extracted_at(doc_naive) == datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)

def test_get_extracted_at_string():
    doc = {"extracted_at": "2026-07-13T12:00:00Z"}
    assert get_extracted_at(doc) == datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)

    doc_tz = {"extracted_at": "2026-07-13T14:00:00+02:00"}
    assert get_extracted_at(doc_tz) == datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)

def test_get_extracted_at_objectid():
    # ObjectId('64afe3108c4e402ea29b8c00') generation time is 2023-07-13 11:42:08 UTC
    obj_id = ObjectId("64afe3108c4e402ea29b8c00")
    doc = {"_id": obj_id}
    res = get_extracted_at(doc)
    assert res == datetime(2023, 7, 13, 11, 42, 8, tzinfo=timezone.utc)

def test_get_extracted_at_fallback():
    doc = {}
    res = get_extracted_at(doc)
    assert isinstance(res, datetime)
    assert res.tzinfo == timezone.utc

# Test clean_mongo_doc
def test_clean_mongo_doc():
    dt = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
    obj_id = ObjectId("64afe3108c4e402ea29b8c00")
    doc = {
        "id": obj_id,
        "date": dt,
        "nested": {
            "id": obj_id
        },
        "list": [obj_id, dt, "string"]
    }
    cleaned = clean_mongo_doc(doc)
    assert cleaned["id"] == "64afe3108c4e402ea29b8c00"
    assert cleaned["date"] == "2026-07-13T12:00:00+00:00"
    assert cleaned["nested"]["id"] == "64afe3108c4e402ea29b8c00"
    assert cleaned["list"][0] == "64afe3108c4e402ea29b8c00"
    assert cleaned["list"][1] == "2026-07-13T12:00:00+00:00"
    assert cleaned["list"][2] == "string"

# Test extract_archive
@patch("tarfile.open")
@patch("os.path.exists", return_value=True)
@patch("tempfile.mkdtemp", return_value="/tmp/test_dir")
def test_extract_archive(mock_mkdtemp, mock_exists, mock_tarfile):
    mock_tar = MagicMock()
    mock_tarfile.return_value.__enter__.return_value = mock_tar
    
    res = extract_archive("some_path.tar")
    
    assert res == "/tmp/test_dir"
    mock_tar.extractall.assert_called_once_with(path="/tmp/test_dir")

# Test make_dir_writable_for_docker
@patch("os.chmod")
@patch("os.walk")
def test_make_dir_writable_for_docker(mock_walk, mock_chmod):
    mock_walk.return_value = [
        ("/tmp/test_dir", ["sub_dir"], ["file.txt"]),
    ]
    make_dir_writable_for_docker("/tmp/test_dir")
    assert mock_chmod.call_count == 3  # root dir, sub_dir, file.txt

# Test run_mongo_container and stop_and_remove_container
@patch("subprocess.run")
def test_run_mongo_container(mock_run):
    # Mock docker run stdout container ID
    run_proc = MagicMock()
    run_proc.stdout = "mock_container_id\n"
    
    # Mock docker inspect stdout mapped port
    inspect_proc = MagicMock()
    inspect_proc.stdout = json.dumps([
        {
            "NetworkSettings": {
                "Ports": {
                    "27017/tcp": [{"HostPort": "32876"}]
                }
            }
        }
    ])
    
    mock_run.side_effect = [run_proc, inspect_proc]
    
    container_name, port = run_mongo_container("/tmp/db", "mongo:latest")
    
    assert container_name.startswith("coc_mongo_backfill_")
    assert port == 32876
    assert mock_run.call_count == 2

@patch("subprocess.run")
def test_stop_and_remove_container(mock_run):
    stop_and_remove_container("mock_container")
    assert mock_run.call_count == 2
    mock_run.assert_any_call(["docker", "stop", "mock_container"], capture_output=True)
    mock_run.assert_any_call(["docker", "rm", "mock_container"], capture_output=True)

# Test load_table_data
def test_load_table_data():
    mock_bq_client = MagicMock()
    mock_job = MagicMock()
    mock_job.errors = None
    mock_bq_client.load_table_from_file.return_value = mock_job
    
    rows = [
        {"extracted_at": "2026-07-13T12:00:00+00:00", "payload": {"foo": "bar"}}
    ]
    
    captured_data = []
    def mock_load(file_obj, table_id, job_config):
        content = file_obj.read()
        captured_data.append(content)
        return mock_job
        
    mock_bq_client.load_table_from_file.side_effect = mock_load
    
    load_table_data(mock_bq_client, "project.dataset.table", rows)
    
    mock_bq_client.load_table_from_file.assert_called_once()
    assert len(captured_data) == 1
    parsed = json.loads(captured_data[0].decode("utf-8").strip())
    assert parsed["extracted_at"] == "2026-07-13T12:00:00+00:00"
    assert parsed["payload"] == {"foo": "bar"}

# Test process_and_backfill mapping logic
def test_process_and_backfill_mapping():
    mock_mongo = MagicMock()
    mock_bq = MagicMock()
    
    mock_mongo.list_database_names.return_value = ["admin", "local", "coc_db"]
    mock_db = MagicMock()
    mock_mongo.__getitem__.return_value = mock_db
    mock_db.list_collection_names.return_value = ["clan", "warlog", "capital_raids"]
    
    mock_clan_col = MagicMock()
    mock_warlog_col = MagicMock()
    mock_raids_col = MagicMock()
    
    collections_map = {
        "clan": mock_clan_col,
        "warlog": mock_warlog_col,
        "capital_raids": mock_raids_col
    }
    mock_db.__getitem__.side_effect = lambda key: collections_map[key]
    
    # Mock data for collections
    dt = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
    clan_doc = {
        "_id": ObjectId("64afe3108c4e402ea29b8c00"),
        "extracted_at": dt,
        "tag": "#CLAN1",
        "name": "Test Clan",
        "players": [
            {
                "tag": "#PLAYER1",
                "name": "Test Player",
                "role": "member",
                "townHallLevel": 14,
                "extra_field": "discard"
            }
        ]
    }
    
    war_doc = {
        "_id": ObjectId("64afe3108c4e402ea29b8c01"),
        "extracted_at": dt,
        "war_id": "war123"
    }
    
    raid_doc = {
        "_id": ObjectId("64afe3108c4e402ea29b8c02"),
        "extracted_at": dt,
        "raid_id": "raid123"
    }
    
    mock_clan_col.find.return_value = [clan_doc]
    mock_warlog_col.find.return_value = [war_doc]
    mock_raids_col.find.return_value = [raid_doc]
    
    # Track load jobs
    loaded_data = {}
    def mock_load(file_obj, table_id, job_config):
        content = file_obj.read()
        loaded_data[table_id] = [json.loads(line) for line in content.decode("utf-8").strip().split("\n") if line]
        mock_job = MagicMock()
        mock_job.errors = None
        return mock_job
        
    mock_bq.load_table_from_file.side_effect = mock_load
    
    process_and_backfill(mock_mongo, mock_bq, "test-project", "test_dataset")

    # Validate coc_clan
    assert "test-project.test_dataset.coc_clan" in loaded_data
    clan_loaded = loaded_data["test-project.test_dataset.coc_clan"]
    assert len(clan_loaded) == 1
    assert clan_loaded[0]["extracted_at"] == "2026-07-13T12:00:00+00:00"
    assert clan_loaded[0]["payload"]["tag"] == "#CLAN1"
    assert "players" not in clan_loaded[0]["payload"]
    assert "_id" not in clan_loaded[0]["payload"]
    
    # Validate coc_members
    assert "test-project.test_dataset.coc_members" in loaded_data
    members_loaded = loaded_data["test-project.test_dataset.coc_members"]
    assert len(members_loaded) == 1
    assert members_loaded[0]["extracted_at"] == "2026-07-13T12:00:00+00:00"
    assert members_loaded[0]["payload"]["tag"] == "#PLAYER1"
    assert members_loaded[0]["payload"]["name"] == "Test Player"
    assert members_loaded[0]["payload"]["role"] == "member"
    assert members_loaded[0]["payload"]["townHallLevel"] == 14
    assert "extra_field" not in members_loaded[0]["payload"]
    
    # Validate coc_current_war
    assert "test-project.test_dataset.coc_current_war" in loaded_data
    war_loaded = loaded_data["test-project.test_dataset.coc_current_war"]
    assert len(war_loaded) == 1
    assert war_loaded[0]["extracted_at"] == "2026-07-13T12:00:00+00:00"
    assert war_loaded[0]["payload"]["war_id"] == "war123"
    assert "_id" not in war_loaded[0]["payload"]
    
    # Validate coc_capital_raids
    assert "test-project.test_dataset.coc_capital_raids" in loaded_data
    raid_loaded = loaded_data["test-project.test_dataset.coc_capital_raids"]
    assert len(raid_loaded) == 1
    assert raid_loaded[0]["extracted_at"] == "2026-07-13T12:00:00+00:00"
    assert raid_loaded[0]["payload"]["raid_id"] == "raid123"
    assert "_id" not in raid_loaded[0]["payload"]
