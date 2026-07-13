#!/usr/bin/env python
import argparse
import json
import logging
import os
import subprocess
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from pymongo import MongoClient
from bson import ObjectId
from google.cloud import bigquery

from coc_elt.config import settings
from coc_elt.logging_config import setup_logging

logger = logging.getLogger(__name__)

def get_extracted_at(doc: Dict[str, Any]) -> datetime:
    """Resolves the extraction time from a document.
    Prioritizes the 'extracted_at' field (datetime or parsed ISO format string)
    and falls back to BSON 'ObjectId' generation time or current time.
    """
    val = doc.get("extracted_at")
    if val:
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val.astimezone(timezone.utc)
        elif isinstance(val, str):
            try:
                # Handle 'Z' suffix for compatibility
                s = val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception as e:
                logger.warning("Failed to parse extracted_at string '%s': %s", val, e)
    
    # Fallback to ObjectId generation time
    _id = doc.get("_id")
    if isinstance(_id, ObjectId):
        return _id.generation_time.astimezone(timezone.utc)
        
    return datetime.now(timezone.utc)

def clean_mongo_doc(doc: Any) -> Any:
    """Recursively converts MongoDB specific types (like ObjectId and datetime)
    to JSON-compatible types.
    """
    if isinstance(doc, dict):
        return {k: clean_mongo_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [clean_mongo_doc(v) for v in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        if doc.tzinfo is None:
            return doc.replace(tzinfo=timezone.utc).isoformat()
        return doc.astimezone(timezone.utc).isoformat()
    else:
        return doc

def extract_archive(archive_path: str) -> str:
    """Extracts the gzipped tar archive to a temporary directory under /tmp."""
    temp_dir = tempfile.mkdtemp(prefix="coc_mongo_backfill_", dir="/tmp")
    logger.info("Extracting archive '%s' to '%s'...", archive_path, temp_dir)
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Archive path '{archive_path}' does not exist.")
        
    with tarfile.open(archive_path, "r:*") as tar:
        tar.extractall(path=temp_dir)
    return temp_dir

def make_dir_writable_for_docker(path: str) -> None:
    """Recursively chmods directory and its contents to 777."""
    logger.info("Setting permissions 777 on directory '%s'...", path)
    os.chmod(path, 0o777)
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

def run_mongo_container(db_path: str, image: str) -> Tuple[str, int]:
    """Runs a temporary MongoDB container mounting db_path as /data/db.
    Exposes 27017 on a random host port and returns the container name and the host port.
    """
    container_name = f"coc_mongo_backfill_{uuid.uuid4().hex}"
    logger.info("Starting container '%s' using image '%s'...", container_name, image)
    
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-v", f"{db_path}:/data/db",
        "-p", "27017",
        image
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    logger.info("Container started with ID: %s", result.stdout.strip())
    
    host_port = None
    for _ in range(10):
        try:
            inspect_cmd = ["docker", "inspect", container_name]
            inspect_res = subprocess.run(inspect_cmd, capture_output=True, text=True, check=True)
            inspect_data = json.loads(inspect_res.stdout)
            ports = inspect_data[0]["NetworkSettings"]["Ports"]
            port_info = ports.get("27017/tcp")
            if port_info:
                host_port = int(port_info[0]["HostPort"])
                logger.info("Container port 27017 mapped to host port %d", host_port)
                break
        except Exception as e:
            logger.debug("Failed to inspect port mapping: %s. Retrying...", e)
        time.sleep(1)
        
    if not host_port:
        # Stop and remove container if host port cannot be resolved
        stop_and_remove_container(container_name)
        raise RuntimeError("Could not resolve host port mapping for the MongoDB container.")
        
    return container_name, host_port

def stop_and_remove_container(container_id: str) -> None:
    """Stops and removes the specified Docker container."""
    logger.info("Stopping container '%s'...", container_id)
    subprocess.run(["docker", "stop", container_id], capture_output=True)
    logger.info("Removing container '%s'...", container_id)
    subprocess.run(["docker", "rm", container_id], capture_output=True)

def load_table_data(
    bq_client: bigquery.Client,
    table_id: str,
    rows: List[Dict[str, Any]],
    write_disposition: str = bigquery.WriteDisposition.WRITE_APPEND
) -> None:
    """Loads transformed records into a BigQuery table using a single load_table_from_file job."""
    if not rows:
        logger.info("No rows to load for table %s", table_id)
        return
        
    logger.info("Preparing to load %d rows into BigQuery table '%s'", len(rows), table_id)
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as tmp_file:
        tmp_file_path = tmp_file.name
        try:
            for row in rows:
                tmp_file.write((json.dumps(row) + "\n").encode("utf-8"))
            tmp_file.flush()
            tmp_file.close()
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=write_disposition
            )
            
            with open(tmp_file_path, 'rb') as file_obj:
                job = bq_client.load_table_from_file(
                    file_obj,
                    table_id,
                    job_config=job_config
                )
                job.result()
                
            if job.errors:
                logger.error("BigQuery load job errors: %s", job.errors)
                raise RuntimeError(f"BigQuery load job failed with errors: {job.errors}")
                
            logger.info("Successfully loaded %d rows into '%s'", len(rows), table_id)
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

def process_and_backfill(
    mongo_client: MongoClient,
    bq_client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table: str = "all"
) -> None:
    """Discovers the database and processes all Clash of Clans collections,
    then loads the mapped data into BigQuery.
    """
    # Find target database
    target_db_name = None
    for db_name in mongo_client.list_database_names():
        if db_name in ("admin", "config", "local"):
            continue
        try:
            db = mongo_client[db_name]
            cols = db.list_collection_names()
            if 'clan' in cols or 'warlog' in cols:
                target_db_name = db_name
                logger.info("Found Clash of Clans database: '%s'", target_db_name)
                break
        except Exception as e:
            logger.warning("Error checking database '%s': %s", db_name, e)
            
    if not target_db_name:
        raise RuntimeError("Could not find a MongoDB database containing collections 'clan' or 'warlog'.")
        
    db = mongo_client[target_db_name]
    cols = db.list_collection_names()
    
    # Process 'clan' collection
    if 'clan' in cols and table in ("all", "coc_clan", "coc_members"):
        clan_rows: List[Dict[str, Any]] = []
        member_rows: List[Dict[str, Any]] = []
        
        logger.info("Processing collection 'clan'...")
        for doc in db['clan'].find():
            extracted_at_str = get_extracted_at(doc).isoformat()
            
            # coc_clan table payload: strip _id and players
            if table in ("all", "coc_clan"):
                clan_payload = {k: v for k, v in doc.items() if k not in ("_id", "players")}
                clan_rows.append({
                    "extracted_at": extracted_at_str,
                    "payload": clean_mongo_doc(clan_payload)
                })
            
            # coc_members table payload: process players array
            if table in ("all", "coc_members"):
                players = doc.get("players")
                if isinstance(players, list):
                    for player in players:
                        member_rows.append({
                            "extracted_at": extracted_at_str,
                            "payload": clean_mongo_doc(player)
                        })
                    
        if table in ("all", "coc_clan"):
            load_table_data(
                bq_client,
                f"{project_id}.{dataset_id}.coc_clan",
                clan_rows,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
        if table in ("all", "coc_members"):
            load_table_data(
                bq_client,
                f"{project_id}.{dataset_id}.coc_members",
                member_rows,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
        
    # Process 'warlog' collection
    if 'warlog' in cols and table in ("all", "coc_current_war"):
        warlog_rows: List[Dict[str, Any]] = []
        logger.info("Processing collection 'warlog'...")
        for doc in db['warlog'].find():
            extracted_at_str = get_extracted_at(doc).isoformat()
            war_payload = {k: v for k, v in doc.items() if k != "_id"}
            warlog_rows.append({
                "extracted_at": extracted_at_str,
                "payload": clean_mongo_doc(war_payload)
            })
        load_table_data(
            bq_client,
            f"{project_id}.{dataset_id}.coc_current_war",
            warlog_rows,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        
    # Process 'capital_raids' collection
    if 'capital_raids' in cols and table in ("all", "coc_capital_raids"):
        raids_rows: List[Dict[str, Any]] = []
        logger.info("Processing collection 'capital_raids'...")
        for doc in db['capital_raids'].find():
            extracted_at_str = get_extracted_at(doc).isoformat()
            raids_payload = {k: v for k, v in doc.items() if k != "_id"}
            raids_rows.append({
                "extracted_at": extracted_at_str,
                "payload": clean_mongo_doc(raids_payload)
            })
        load_table_data(
            bq_client,
            f"{project_id}.{dataset_id}.coc_capital_raids",
            raids_rows,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )

def main() -> None:
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Backfill Clash of Clans data from historical MongoDB tarball to BigQuery Bronze tables."
    )
    parser.add_argument(
        "--archive-path",
        default="coc_db",
        help="Path to the gzipped tar archive of a MongoDB WiredTiger data directory."
    )
    parser.add_argument(
        "--project-id",
        default=settings.data_project_id or "swift-capsule-492817-a7",
        help="Google Cloud Project ID for BigQuery."
    )
    parser.add_argument(
        "--dataset-id",
        default=settings.dataset_id or "coc_bronze",
        help="BigQuery dataset ID."
    )
    parser.add_argument(
        "--mongo-image",
        default="mongo:latest",
        help="Docker image for MongoDB container."
    )
    parser.add_argument(
        "--table",
        default="all",
        help="Specific target table to backfill (e.g. coc_members), or 'all' to process all tables."
    )
    
    args = parser.parse_args()
    
    temp_dir = None
    container_name = None
    
    try:
        # Extract archive
        temp_dir = extract_archive(args.archive_path)
        
        # Set permissions for Docker container
        make_dir_writable_for_docker(temp_dir)
        
        # Start Docker container
        container_name, host_port = run_mongo_container(temp_dir, args.mongo_image)
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB at localhost:%d...", host_port)
        mongo_client = MongoClient(host="localhost", port=host_port, serverSelectionTimeoutMS=2000)
        
        # Wait until MongoDB is ready
        ready = False
        for i in range(30):
            try:
                mongo_client.admin.command('ping')
                ready = True
                logger.info("MongoDB is ready to accept connections.")
                break
            except Exception as e:
                logger.info("Waiting for MongoDB to start... (%d/30) error: %s", i + 1, e)
                time.sleep(1)
                
        if not ready:
            raise RuntimeError("MongoDB container did not become ready in time.")
            
        # Initialize BigQuery client
        logger.info("Initializing BigQuery client for project '%s'...", args.project_id)
        bq_client = bigquery.Client(project=args.project_id)
        
        # Run process and backfill
        process_and_backfill(
            mongo_client=mongo_client,
            bq_client=bq_client,
            project_id=args.project_id,
            dataset_id=args.dataset_id,
            table=args.table
        )
        
        logger.info("MongoDB backfill process finished successfully.")
        
    except Exception as e:
        logger.exception("Error during MongoDB backfill execution")
        raise
    finally:
        # Cleanup
        if container_name:
            try:
                stop_and_remove_container(container_name)
            except Exception as e:
                logger.warning("Failed to stop and remove container '%s': %s", container_name, e)
        if temp_dir:
            try:
                logger.info("Deleting temporary extraction directory '%s'...", temp_dir)
                subprocess.run(["rm", "-rf", temp_dir], check=True)
            except Exception as e:
                logger.warning("Failed to delete extraction directory '%s': %s", temp_dir, e)

if __name__ == "__main__":
    main()
