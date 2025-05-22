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

# Read the submit_standup_update script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "submit_standup_update.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
submit_standup_tool = DailyScrumTool(
    name="submit_standup",
    description=(
        "Submit a standup update to be recorded in the team's Airtable database.\n"
        "This tool allows team members to submit what they did yesterday, what they plan to do today, and any blockers they're facing."
    ),
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 pyairtable==2.1.0 2>&1 | grep -v '[notice]'

    # Run the standup submission script
    python /opt/scripts/submit_standup_update.py --yesterday "{{ .yesterday }}" --today "{{ .today }}" {{ if .blockers }}--blockers "{{ .blockers }}"{{ end }} --notify
    """,
    args=[
        Arg(
            name="yesterday",
            description=(
                "What the user accomplished yesterday.\n"
                "*Example*: `Completed the API integration and fixed two bugs in the authentication flow.`"
            ),
            required=True,
        ),
        Arg(
            name="today",
            description=(
                "What the user plans to work on today.\n"
                "*Example*: `Working on the frontend components and starting the documentation.`"
            ),
            required=True,
        ),
        Arg(
            name="blockers",
            description=(
                "Any blockers or issues preventing progress (optional).\n"
                "*Example*: `Waiting for DevOps to provision the new database.`"
            ),
            required=False,
        ),
    ],
    env=[
        "KUBIYA_USER_EMAIL",
    ],
    secrets=[
        "SLACK_API_TOKEN",
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_TABLE_NAME",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/submit_standup_update.py",
            content=script_content,
        ),
    ],
    long_running=False,
    mermaid="""
    sequenceDiagram
        participant U as User
        participant A as Agent
        participant S as System
        participant AT as Airtable
        participant SL as Slack

        U ->> A: Submit Standup Update
        A ->> S: Process Standup Data
        S ->> AT: Store in Database
        S ->> SL: Send Confirmation
        SL -->> U: Notify Success
    """,
)

# Register the tool
tool_registry.register("scrum_tools", submit_standup_tool)

# Export the tool
__all__ = ["submit_standup_tool"]

# Make sure the tool is available at module level
globals()["submit_standup_tool"] = submit_standup_tool
