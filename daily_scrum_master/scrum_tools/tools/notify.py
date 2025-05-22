import inspect
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools.models import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

from .base import DailyScrumTool

# Read the collect_user_standup script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "notify_users.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
notify_standup_tool = DailyScrumTool(
    name="notify_standup",
    description=(
        "Send standup report reminders to team members via Slack.\n"
        "This tool notifies users with a button they can click to submit their standup report."
    ),
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'

    # Run the standup notification script
    python /opt/scripts/notify_users.py {{ range .team_emails }}"{{ . }}" {{ end }}
    """,
    args=[
        Arg(
            name="team_emails",
            description=(
                "List of email addresses of team members to notify for standup reports.\n"
                "*Example*: `[\"user1@example.com\", \"user2@example.com\"]`"
            ),
            required=True,
            is_array=True,
        ),
    ],
    env=[
        "KUBIYA_AGENT_UUID",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/notify_users.py",
            content=script_content,
        ),
    ],
    long_running=False,
    mermaid="""
    sequenceDiagram
        participant A as Agent
        participant S as System
        participant U as Users

        A ->> S: Send Standup Reminders
        S ->> Slack: Send Notifications
        S -->> U: Deliver Reminders
        U ->> A: Submit Standup Reports
    """,
)

# Register the tool
tool_registry.register("scrum_tools", notify_standup_tool)

# Export the tool
__all__ = ["notify_standup_tool"]

# Make sure the tool is available at module level
globals()["notify_standup_tool"] = notify_standup_tool