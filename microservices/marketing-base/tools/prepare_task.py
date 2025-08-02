#!/usr/bin/env python3
"""
Task Preparation Tool for Campaign Processing

This script prepares and submits a campaign processing task to the task repository.
It loads campaign data and recipient data from JSON files and creates a properly
formatted task for processing by the campaign processor service.

Usage:
    python prepare_task.py --campaign-file sample_campaign.json --recipients-file sample_recipients.json [--task-id unique_task_id]
"""

import argparse
import datetime
import json
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

# Allow importing modules from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.repositories.mongodb_repository import MongoDBTaskRepository
from src.config import get_settings


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict containing the parsed JSON data
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path}: {e}")
        sys.exit(1)


def prepare_task(campaign_data: Dict[str, Any], 
                 recipients_data: List[Dict[str, Any]], 
                 task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare a task object for submission to the task repository.
    
    Args:
        campaign_data: Campaign configuration data
        recipients_data: List of recipient data objects
        task_id: Optional task identifier (generated if not provided)
        
    Returns:
        Dict containing the task data ready for submission
    """
    if task_id is None:
        task_id = f"task_{uuid.uuid4().hex}"
    
    # Ensure template HTML is included directly in campaign data
    if not campaign_data.get("template_html"):
        # Check if there are templates defined in the campaign
        templates = campaign_data.get("templates", {})
        if templates:
            # Look for email templates
            email_templates = {k: v for k, v in templates.items() 
                              if isinstance(v, dict) and v.get('content_type') == 'email'}
            
            if email_templates:
                # Use the first email template found
                template_key = next(iter(email_templates))
                template_data = email_templates[template_key]
                
                # Copy template content to campaign level
                campaign_data["template_html"] = template_data.get("body", "")
                if not campaign_data.get("subject") and template_data.get("subject"):
                    campaign_data["subject"] = template_data.get("subject")
                    
                print(f"Extracted template content from template: {template_key}")
    
    # Create task object
    task = {
        "task_id": task_id,
        "campaign_id": campaign_data.get("id", f"camp_{uuid.uuid4().hex}"),
        "campaign_name": campaign_data.get("name", "Unnamed Campaign"),
        "task_type": "campaign",
        "status": "PENDING",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "priority": int(campaign_data.get("custom_attributes", {}).get("priority", "medium") == "high"),
        "campaign_template": {
            "name": campaign_data.get("name", "Unnamed Campaign"),
            "subject": campaign_data.get("subject", ""),
            "from_email": campaign_data.get("from_email", ""),
            "reply_to": campaign_data.get("reply_to", ""),
            "template_html": campaign_data.get("template_html", ""),
            "template_text": campaign_data.get("template_text", ""),
            "description": campaign_data.get("description", ""),
            "tags": campaign_data.get("tags", []),
            "track_opens": campaign_data.get("track_opens", True),
            "track_clicks": campaign_data.get("track_clicks", True),
            "custom_attributes": campaign_data.get("custom_attributes", {})
        },
        "recipients": recipients_data,
        "batch_size": 100,  # Number of emails to send in each batch
        "retry_config": {
            "max_retries": 3,
            "retry_delay_seconds": 300  # 5 minutes
        }
    }
    
    return task


def submit_task(task: Dict[str, Any]) -> str:
    """
    Submit a task to the MongoDB task repository.
    
    Args:
        task: The task data to submit
        
    Returns:
        The ID of the submitted task
    """
    # Get configuration settings
    config = get_settings()
    
    # Create repository instance
    repository = MongoDBTaskRepository(
        connection_string=config.mongodb_connection_string,
        database_name=config.mongodb_database,
        collection_name=config.mongodb_tasks_collection
    )
    
    # Submit task
    task_id = repository.create_task(task)
    return task_id


def main():
    """Main function to parse arguments and execute the task preparation."""
    parser = argparse.ArgumentParser(description='Prepare and submit a campaign processing task.')
    parser.add_argument('--campaign-file', required=True, help='Path to the campaign JSON file')
    parser.add_argument('--recipients-file', required=True, help='Path to the recipients JSON file')
    parser.add_argument('--task-id', help='Optional unique task ID (will be generated if not provided)')
    parser.add_argument('--dry-run', action='store_true', help='Preview the task without submitting it')
    
    args = parser.parse_args()
    
    # Load campaign and recipients data
    campaign_data = load_json_file(args.campaign_file)
    recipients_data = load_json_file(args.recipients_file)
    
    # Prepare task
    task = prepare_task(campaign_data, recipients_data, args.task_id)
    
    # Print preview
    print(f"Task Preview:")
    print(f"  Task ID: {task['task_id']}")
    print(f"  Campaign: {task['campaign_name']}")
    print(f"  Recipients: {len(task['recipients'])}")
    print(f"  Template ID: {task['campaign_template']['name']}")
    
    # Submit if not a dry run
    if not args.dry_run:
        try:
            submitted_task_id = submit_task(task)
            print(f"\nTask successfully submitted with ID: {submitted_task_id}")
        except Exception as e:
            print(f"\nError submitting task: {e}")
    else:
        print("\nDry run - task not submitted.")
        print(f"To submit this task, run the command without the --dry-run flag.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 