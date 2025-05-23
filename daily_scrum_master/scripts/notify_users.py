import sys
import os
import json
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    # During discovery phase, requests might not be available
    pass

def notify_user(user_email):
    """
    Notify a user to submit their standup report via Slack
    """
    slack_token = os.environ["SLACK_API_TOKEN"]

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
        sys.exit(1)

    user_id = user_info_response.json()["user"]["id"]

    # Prepare the Block Kit message
    message = {
        "channel": user_id,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":memo: Daily Standup Reminder",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi <@{user_id}> :wave:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "It's time for your daily standup report! Please share what you've been working on."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":rocket: *Ready to submit your standup?*\nClick the button below to start your standup report!"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Submit Standup Report",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": json.dumps({
                            "agent_uuid": os.environ.get("KUBIYA_AGENT_UUID", ""),
                            "message": "I would like to submit my standup report"
                        }),
                        "action_id": "agent.process_message_1"
                    }
                ]
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
        print(f"Failed to send notification: {response.text}")
        sys.exit(1)
    
    print(f"Successfully sent standup reminder to {user_email}")

def notify_team(team_emails):
    """
    Notify a list of team members to submit their standup reports
    """
    for email in team_emails:
        try:
            notify_user(email)
        except Exception as e:
            print(f"Failed to notify {email}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: notify_users.py <comma_separated_emails>")
        sys.exit(1)

    # Parse comma-separated emails from the first argument
    emails_string = sys.argv[1]
    user_emails = [email.strip() for email in emails_string.split(',') if email.strip()]
    
    if not user_emails:
        print("No valid email addresses provided")
        sys.exit(1)
    
    notify_team(user_emails)