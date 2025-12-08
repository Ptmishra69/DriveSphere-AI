# worker_agents/customer_engagement_agent/message_templates.py

def intro_line(model, urgency):
    if urgency == "high":
        return f"We’ve found an urgent issue with your {model}."
    if urgency == "medium":
        return f"Your {model} needs attention soon."
    return f"We have a quick update about your {model}."

def persuasive_line(cost_sensitive, issue):
    if cost_sensitive:
        return f"Fixing the {issue} now will save costs compared to delaying repairs."
    return f"Addressing the {issue} promptly keeps your ride smooth and safe."

def safety_line(urgency):
    if urgency == "high":
        return "For your safety, we recommend scheduling service immediately."
    if urgency == "medium":
        return "It's a good idea to plan a check-up soon."
    return "This isn't urgent, but good to keep an eye on."

def closing_line():
    return "Would you like me to help schedule a service appointment?"

def push_notification_line(issue, urgency):
    if urgency == "high":
        return f"Urgent: {issue} detected. Service needed now."
    if urgency == "medium":
        return f"Attention: {issue} requires servicing soon."
    return f"Update: {issue} found. Not urgent."

def voice_script_line(model, component, issue, urgency):
    urgency_phrase = {
        "high": "This needs immediate attention.",
        "medium": "We recommend getting it checked soon.",
        "low": "This is not urgent, but worth monitoring."
    }.get(urgency, "Worth checking.")

    return (
        f"Hello! This is your Hero service assistant. "
        f"We found an issue with the {component} of your {model}. "
        f"The specific concern is: {issue}. "
        f"{urgency_phrase} Please let me know if you'd like to schedule a service appointment."
    )
