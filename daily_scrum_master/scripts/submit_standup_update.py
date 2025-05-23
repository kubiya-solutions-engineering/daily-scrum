import sys
import os
import json
from datetime import datetime, timezone

try:
    import argparse
    import requests
    from pyairtable import Api
    import litellm
except ImportError:
    # During discovery phase, these might not be available
    pass

def analyze_blockers_with_llm(yesterday, today, blockers=None):
    """
    Use LiteLLM to analyze if the user has any blockers that need scrum master attention
    
    Args:
        yesterday (str): What the user accomplished yesterday
        today (str): What the user plans to do today
        blockers (str, optional): Any blockers the user mentioned
    
    Returns:
        dict: Analysis result with has_blockers (bool) and summary (str)
    """
    try:
        # Prepare the analysis prompt
        analysis_prompt = f"""
        Analyze this standup update to determine if the user has any blockers that need scrum master attention.

        Yesterday: {yesterday}
        Today: {today}
        Blockers mentioned: {blockers if blockers else "None explicitly mentioned"}

        Please analyze if there are any blockers, impediments, or issues that would require scrum master intervention or team awareness. Look for:
        - Explicit mentions of blockers or impediments
        - Dependencies on other team members
        - Technical issues preventing progress
        - Resource constraints
        - Waiting for external approvals or decisions

        Respond with a JSON object containing:
        - "has_blockers": true/false
        - "summary": brief description of the blockers if any, or "No blockers identified" if none

        Example response:
        {{"has_blockers": true, "summary": "Waiting for DevOps team to provision database access"}}
        """

        messages = [
            {
                "role": "system", 
                "content": "You are a scrum master assistant that analyzes standup updates to identify blockers. Always respond with valid JSON."
            },
            {
                "role": "user", 
                "content": analysis_prompt
            }
        ]

        base_url = os.environ.get("LLM_BASE_URL")
        
        response = litellm.completion(
            messages=messages,
            model="openai/Llama-4-Scout",
            api_key=os.environ.get("LLM_API_KEY"),
            base_url=base_url,
            stream=False,
            user=os.environ.get("KUBIYA_USER_EMAIL"),
            max_tokens=2048,
            temperature=0.7,
            top_p=0.1,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            timeout=30,
        )

        # Parse the LLM response
        llm_response = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            analysis = json.loads(llm_response)
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            has_blockers = "true" in llm_response.lower() and ("blocker" in llm_response.lower() or "impediment" in llm_response.lower())
            return {
                "has_blockers": has_blockers,
                "summary": llm_response if has_blockers else "No blockers identified"
            }

    except Exception as e:
        print(f"Failed to analyze blockers with LLM: {str(e)}")
        # Fallback to simple keyword detection
        blocker_keywords = ["blocked", "blocker", "impediment", "waiting for", "can't", "unable", "stuck", "issue", "problem"]
        text_to_check = f"{yesterday} {today} {blockers or ''}".lower()
        
        has_blockers = any(keyword in text_to_check for keyword in blocker_keywords)
        return {
            "has_blockers": has_blockers,
            "summary": blockers if blockers and has_blockers else "No blockers identified"
        }

def notify_scrum_master_about_blocker(user_email, blocker_summary):
    """
    Send a notification to the scrum master about a team member's blocker
    """
    slack_token = os.environ.get("SLACK_API_TOKEN")
    scrum_master_email = os.environ.get("SCRUM_MASTER_EMAIL")
    
    if not slack_token or not scrum_master_email:
        print("Skipping scrum master notification - SLACK_API_TOKEN or SCRUM_MASTER_EMAIL not provided")
        return

    try:
        # Get scrum master's Slack user ID
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {slack_token}",
        }
        params = {"email": scrum_master_email}
        user_info_response = requests.get(
            "https://slack.com/api/users.lookupByEmail", headers=headers, params=params
        )

        if user_info_response.status_code != 200 or not user_info_response.json().get("ok"):
            print(f"Failed to retrieve scrum master user ID: {user_info_response.text}")
            return

        scrum_master_id = user_info_response.json()["user"]["id"]
        
        # Get team member's name from email
        team_member_name = user_email.split('@')[0].replace('.', ' ').title()

        # Prepare the Block Kit message for scrum master
        message = {
            "channel": scrum_master_id,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":warning: Team Member Has Blocker",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Team Member:* {team_member_name} ({user_email})"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Blocker Summary:*\n{blocker_summary}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":point_right: *Action Required:* Please follow up with the team member to help resolve this blocker."
                    }
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
            print(f"Failed to notify scrum master: {response.text}")
        else:
            print(f"Notified scrum master about blocker from {user_email}")

    except Exception as e:
        print(f"Failed to notify scrum master: {str(e)}")

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
    
    # Analyze for blockers using LLM
    blocker_analysis = analyze_blockers_with_llm(yesterday, today, blockers)
    
    # Check if user already exists in the table
    try:
        existing_records = table.all(formula=f"{{Email}} = '{user_email}'")
        
        record_data = {
            "Yesterday": yesterday,
            "Today": today,
            "Last_Updated": formatted_date,
            "Timestamp": current_time.isoformat(),
            "Has_Blockers": blocker_analysis["has_blockers"],
            "Blocker_Summary": blocker_analysis["summary"]
        }
        
        if blockers:
            record_data["Blockers"] = blockers
        else:
            # Clear blockers if none provided
            record_data["Blockers"] = ""
        
        if existing_records:
            # Update existing user record
            record_id = existing_records[0]['id']
            response = table.update(record_id, record_data)
            print(f"Successfully updated standup for existing user {user_email}")
        else:
            # Create new user record
            record_data["Email"] = user_email
            # Extract name from email for display purposes
            name = user_email.split('@')[0].replace('.', ' ').title()
            record_data["Name"] = name
            
            response = table.create(record_data)
            print(f"Successfully created new user record and standup for {user_email}")
        
        # Notify scrum master if blockers detected
        if blocker_analysis["has_blockers"]:
            notify_scrum_master_about_blocker(user_email, blocker_analysis["summary"])
        
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