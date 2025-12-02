# message_templates.py

def intro_line(model: str, urgency: str):
    if urgency == "high":
        return f"We’ve detected an urgent issue with your {model}."
    elif urgency == "medium":
        return f"We’ve found something on your {model} that needs attention soon."
    return f"Here’s a quick update on your {model}."

def persuasive_line(cost_sensitive: bool, issue: str):
    if cost_sensitive:
        return (
            f"This is a cost-efficient fix now, but delaying may increase repair costs for the {issue}."
        )
    return (
        f"Addressing the {issue} promptly will keep your ride trouble-free and safe."
    )

def safety_line(urgency: str):
    if urgency == "high":
        return "For your safety, we recommend visiting the service center as soon as possible."
    elif urgency == "medium":
        return "It’s best to schedule a quick check-up soon."
    return "This isn’t urgent, but good to keep an eye on."

def closing_line():
    return "Would you like me to help you schedule a service appointment?"
