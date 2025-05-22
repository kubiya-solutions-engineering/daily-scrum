import sys
import os
import json
from datetime import datetime, timezone

try:
    import argparse
    import requests
    from pyairtable import Api
except ImportError:
    # During discovery phase, these might not be available
    pass

def submit_standup_to_airtable(user_email, yesterday, today, blockers=None):
    """
    Submit a user's standup update to Airtable
    
    Args:
        user_email (str): The email of the user submitting the standup
        yesterday (str): What the user accomplished yesterday
        today (str): What the user plans to do today
        blockers (str, optional): Any blockers the user is facing
    """
    # Get Airtable credentials from environment variables
    airtable_api_key = os.environ["AIRTABLE_API_KEY"]
    airtable_base_id = os.environ["AIRTABLE_BASE_ID"]
    airtable_table_name = os.environ["AIRTABLE_TABLE_NAME"]
    
    # Initialize Airtable API
    api = Api(airtable_api_key)
    table = api.table(airtable_base_id, airtable_table_name)
    
    # Prepare the record data
    current_time = datetime.now(timezone.utc)
    formatted_date = current_time.strftime('%Y-%m-%d')
    
    record = {
        "Email": user_email,
        "Date": formatted_date,
        "Yesterday": yesterday,
        "Today": today,
        "Timestamp": current_time.isoformat(),
    }
    
    if blockers:
        record["Blockers"] = blockers
    
    # Create the record in Airtable
    try:
        response = table.create(record)
        print(f"Successfully submitted standup update for {user_email}")
        return response
    except Exception as e:
        print(f"Failed to submit standup update: {str(e)}")
        sys.exit(1)

def notify_submission_success(user_email):
    """
    Send a confirmation message to the user via Slack
    """
    slack_token = os.environ.get("SLACK_API_TOKEN")
    if not slack_token:
        print("Skipping Slack notification - SLACK_API_TOKEN not provided")
        return
    
    # Translate email to Slack user ID
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {slack_token}",
    }
    params = {"email": user_email}
    user_info_response = requests.get(
        "https://slack.com/api/users.lookupByEmail", headers=headers, params=params
    )

    if user_info_response.status_code != 200 or not user_info_response.json().get("ok"):
        print(f"Failed to retrieve user ID: {user_info_response.text}")
        return

    user_id = user_info_response.json()["user"]["id"]

    # Prepare the Block Kit message
    message = {
        "channel": user_id,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":white_check_mark: Standup Submitted",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Thanks <@{user_id}>! Your standup update has been recorded."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
    }

    # Send the message to Slack
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {slack_token}",
    }
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        data=json.dumps(message),
    )

    if response.status_code != 200 or not response.json().get("ok"):
        print(f"Failed to send confirmation: {response.text}")
    else:
        print(f"Sent confirmation to {user_email}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit a standup update to Airtable")
    parser.add_argument("--yesterday", required=True, help="What was accomplished yesterday")
    parser.add_argument("--today", required=True, help="What is planned for today")
    parser.add_argument("--blockers", help="Any blockers (optional)")
    parser.add_argument("--notify", action="store_true", help="Send a confirmation via Slack")
    
    args = parser.parse_args()
    
    # Get user email from environment variable
    user_email = os.environ.get("KUBIYA_USER_EMAIL")
    if not user_email:
        print("Error: KUBIYA_USER_EMAIL environment variable not set")
        sys.exit(1)
    
    # Submit the standup update to Airtable
    submit_standup_to_airtable(
        user_email, 
        args.yesterday, 
        args.today, 
        args.blockers
    )
    
    # Send confirmation if requested
    if args.notify:
        notify_submission_success(user_email) 