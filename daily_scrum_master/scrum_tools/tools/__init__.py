from .base import DailyScrumTool


def __getattr__(name):
    if name == "notify_standup_tool":
        from .notify import notify_standup_tool
        return notify_standup_tool
    elif name == "generate_report_tool":
        from .report import generate_report_tool
        return generate_report_tool
    elif name == "submit_standup_tool":
        from .submit import submit_standup_tool
        return submit_standup_tool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "DailyScrumTool",
    "notify_standup_tool",
    "generate_report_tool",
    "submit_standup_tool",
]