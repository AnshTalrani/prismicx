#!/usr/bin/env python3
"""
Campaign Task Submission Tool.

This tool simulates an agent submitting a campaign task to the central repository.
It can be used for testing the marketing-base microservice.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class TaskSubmitter:
    """Tool for submitting campaign tasks to the central repository."""
    
    def __init__(self, mongo_uri: str, database: str, collection: str):
        """
        Initialize the task submitter.
        
        Args:
            mongo_uri: MongoDB connection URI
            database: Database name
            collection: Collection name
        """
        self.mongo_uri = mongo_uri
        self.database = database
        self.collection = collection
        self.client = None
        self.db = None
        self.coll = None
    
    def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database]
            self.coll = self.db[self.collection]
            logger.info(f"Connected to MongoDB: {self.database}.{self.collection}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    def submit_task(self, campaign_template: Dict[str, Any], recipients: List[Dict[str, Any]]) -> str:
        """
        Submit a campaign task to the central repository.
        
        Args:
            campaign_template: Campaign template in campaign_marketing.json format
            recipients: List of recipient data
            
        Returns:
            Task ID if successful
            
        Raises:
            Exception: If submission fails
        """
        task_id = str(ObjectId())
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"
        
        task = {
            "_id": ObjectId(task_id),
            "task_type": "campaign",
            "status": "pending",
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
            "created_by": "task-submitter-tool",
            "campaign_template": campaign_template,
            "recipients": recipients
        }
        
        try:
            self.coll.insert_one(task)
            logger.info(f"Submitted task {task_id} with batch ID {batch_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise


def load_json_file(file_path: str) -> Any:
    """
    Load JSON from a file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        Exception: If file cannot be loaded or parsed
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        raise


def load_recipients(file_path: str, count: int = None) -> List[Dict[str, Any]]:
    """
    Load recipient data from a JSON file.
    
    Args:
        file_path: Path to JSON file with recipients
        count: Maximum number of recipients to return
        
    Returns:
        List of recipient data
        
    Raises:
        Exception: If file cannot be loaded or parsed
    """
    recipients = load_json_file(file_path)
    
    if not isinstance(recipients, list):
        raise ValueError("Recipients file must contain a JSON array")
    
    if count and len(recipients) > count:
        logger.info(f"Limiting recipients to {count} (from {len(recipients)})")
        recipients = recipients[:count]
    
    logger.info(f"Loaded {len(recipients)} recipients")
    return recipients


def main():
    """Main entry point for the task submission tool."""
    parser = argparse.ArgumentParser(description="Submit a campaign task to the central repository")
    
    parser.add_argument(
        "--mongo-uri", 
        default=os.environ.get("CENTRAL_TASK_REPO_URI", "mongodb://taskadmin:taskpassword@localhost:27018/"),
        help="MongoDB connection URI"
    )
    parser.add_argument(
        "--database", 
        default=os.environ.get("CENTRAL_TASK_REPO_DB", "agent_tasks"),
        help="MongoDB database name"
    )
    parser.add_argument(
        "--collection", 
        default=os.environ.get("CENTRAL_TASK_COLLECTION", "marketing_tasks"),
        help="MongoDB collection name"
    )
    parser.add_argument(
        "--template", 
        required=True,
        help="Path to campaign template JSON file"
    )
    parser.add_argument(
        "--recipients", 
        required=True,
        help="Path to recipients JSON file"
    )
    parser.add_argument(
        "--count", 
        type=int, 
        default=None,
        help="Maximum number of recipients to include"
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        campaign_template = load_json_file(args.template)
        recipients = load_recipients(args.recipients, args.count)
        
        # Submit task
        submitter = TaskSubmitter(args.mongo_uri, args.database, args.collection)
        if submitter.connect():
            task_id = submitter.submit_task(campaign_template, recipients)
            logger.info(f"Task submitted successfully with ID: {task_id}")
            submitter.close()
        else:
            logger.error("Failed to connect to MongoDB")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 