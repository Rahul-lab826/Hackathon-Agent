"""
MCP Registry — gathers all 40 CRUD tool functions for the 10 services
and exposes them as a single list of callable Python tools.
"""
from app.services.mcp.workspace_tools import (
    read_calendar_event, write_calendar_event, update_calendar_event, delete_calendar_event,
    read_google_doc, write_google_doc, update_google_doc, delete_google_doc,
    read_google_sheet, write_google_sheet_row, update_google_sheet_row, delete_google_sheet_row,
    read_google_drive_file, write_google_drive_file, update_google_drive_file, delete_google_drive_file,
    read_gmail_message, write_gmail_draft, update_gmail_draft, delete_gmail_draft
)
from app.services.mcp.communication_tools import (
    read_slack_channel, write_slack_message, update_slack_message, delete_slack_message,
    read_discord_messages, write_discord_message, update_discord_message, delete_discord_message,
    read_github_issue, write_github_issue, update_github_issue, delete_github_issue
)
from app.services.mcp.productivity_tools import (
    read_notion_page, write_notion_page, update_notion_page, delete_notion_page,
    read_figma_file, write_figma_comment, update_figma_comment, delete_figma_comment
)

ALL_MCP_TOOLS = [
    # Google Calendar
    read_calendar_event, write_calendar_event, update_calendar_event, delete_calendar_event,
    # Google Docs
    read_google_doc, write_google_doc, update_google_doc, delete_google_doc,
    # Google Sheets
    read_google_sheet, write_google_sheet_row, update_google_sheet_row, delete_google_sheet_row,
    # Google Drive
    read_google_drive_file, write_google_drive_file, update_google_drive_file, delete_google_drive_file,
    # Gmail
    read_gmail_message, write_gmail_draft, update_gmail_draft, delete_gmail_draft,
    # Slack
    read_slack_channel, write_slack_message, update_slack_message, delete_slack_message,
    # Discord
    read_discord_messages, write_discord_message, update_discord_message, delete_discord_message,
    # GitHub
    read_github_issue, write_github_issue, update_github_issue, delete_github_issue,
    # Notion
    read_notion_page, write_notion_page, update_notion_page, delete_notion_page,
    # Figma
    read_figma_file, write_figma_comment, update_figma_comment, delete_figma_comment
]
