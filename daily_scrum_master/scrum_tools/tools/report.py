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

# Read the generate_standup_report script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "generate_standup_report.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
generate_report_tool = DailyScrumTool(
    name="generate_standup_report",
    description=(
        "Generate a summary report of today's standup submissions from the team.\n"
        "This tool retrieves all standup reports submitted today and provides them in a structured format."
    ),
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install pyairtable==2.1.0 2>&1 | grep -v '[notice]'

    # Run the standup report generation script
    python /opt/scripts/generate_standup_report.py
    """,
    args=[],  # No arguments needed as the script handles everything
    env=[],
    secrets=[
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_TABLE_NAME",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/generate_standup_report.py",
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

        U ->> A: Request Standup Report
        A ->> S: Run Report Tool
        S ->> AT: Fetch Today's Standups
        AT -->> S: Return Standup Data
        S -->> A: Return JSON Data
        A -->> U: Present Formatted Report
    """,
)

# Register the tool
tool_registry.register("scrum_tools", generate_report_tool)

# Export the tool
__all__ = ["generate_report_tool"]

# Make sure the tool is available at module level
globals()["generate_report_tool"] = generate_report_tool
