# Daily Scrum Master

A set of tools to automate and streamline daily scrum processes.

## Features

- **Notify Team Members**: Send automated reminders to team members to submit their daily standup reports
- **Submit Standup Reports**: Allow team members to easily submit their daily updates
- **Generate Reports**: Create summary reports of all standup submissions for the day

## Tools

### Notify Standup Tool

Sends Slack notifications to team members reminding them to submit their daily standup reports.

### Submit Standup Tool

Allows team members to submit their daily standup updates, including:
- What they accomplished yesterday
- What they plan to work on today
- Any blockers they're facing

### Generate Report Tool

Creates a summary report of all standup submissions for the current day, highlighting:
- Team member updates
- Common blockers
- Overall progress

## Setup

1. Configure the required environment variables:
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `AIRTABLE_TABLE_NAME`
   - `SLACK_API_TOKEN`

2. Import the module:
   ```python
   from daily_scrum_master.scrum_tools import notify_standup_tool, submit_standup_tool, generate_report_tool
   ```

3. Use the tools in your workflow as needed.
