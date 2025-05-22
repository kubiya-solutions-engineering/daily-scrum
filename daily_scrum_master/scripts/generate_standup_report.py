import sys
import os
import json
from datetime import datetime, timezone

try:
    from pyairtable import Api
except ImportError:
    # During discovery phase, these might not be available
    pass

def get_todays_standup_reports():
    """
    Retrieve today's standup reports from Airtable
    
    Returns:
        list: A list of standup report records for today
    """
    # Get Airtable credentials from environment variables
    airtable_api_key = os.environ["AIRTABLE_API_KEY"]
    airtable_base_id = os.environ["AIRTABLE_BASE_ID"]
    airtable_table_name = os.environ["AIRTABLE_TABLE_NAME"]
    
    # Initialize Airtable API
    api = Api(airtable_api_key)
    table = api.table(airtable_base_id, airtable_table_name)
    
    # Get today's date in the format used in Airtable
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Query Airtable for records with today's date
    try:
        records = table.all(formula=f"Date = '{today}'")
        print(f"Retrieved {len(records)} standup reports for today ({today})")
        return records
    except Exception as e:
        print(f"Failed to retrieve standup reports: {str(e)}")
        sys.exit(1)

def get_standup_data_as_json():
    """
    Get today's standup data in a simplified JSON format for AI processing
    
    Returns:
        str: JSON string with standup data
    """
    records = get_todays_standup_reports()
    
    # Transform the records into a simpler format
    standup_data = {
        "date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "reports": [],
        "has_blockers": False
    }
    
    for record in records:
        fields = record['fields']
        email = fields.get('Email', 'Unknown')
        name = email.split('@')[0]  # Extract name from email
        
        report = {
            "name": name,
            "email": email,
            "yesterday": fields.get('Yesterday', 'No update provided'),
            "today": fields.get('Today', 'No update provided'),
            "blockers": fields.get('Blockers', None)
        }
        
        if report["blockers"]:
            standup_data["has_blockers"] = True
            
        standup_data["reports"].append(report)
    
    return json.dumps(standup_data, indent=2)

if __name__ == "__main__":
    # Get and print the standup data as JSON
    print(get_standup_data_as_json()) 