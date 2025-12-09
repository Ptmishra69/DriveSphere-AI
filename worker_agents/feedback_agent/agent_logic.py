import json
import re
from .tools import (
    get_vehicle_profile_tool,
    get_past_feedback_tool,
    store_feedback_tool
)
from .sentiment_rules import rule_sentiment


def extract_issues(feedback_text: str):
    """Simple offline extraction using keyword scanning."""
    issues = []
    fb = feedback_text.lower()

    issue_keywords = [
        "noise", "brake", "engine", "vibration", "oil", "problem",
        "not working", "still", "scratch", "dirty", "leak"
    ]

    for word in issue_keywords:
        if word in fb:
            issues.append(word)

    return list(set(issues))


def rate_service(sentiment: str, issues: list):
    """Offline rating heuristic."""
    if sentiment == "positive" and not issues:
        return 5
    if sentiment == "positive" and issues:
        return 4
    if sentiment == "neutral" and not issues:
        return 3
    if sentiment == "neutral" and issues:
        return 2
    if sentiment == "negative":
        return 1
    return 3


def analyze_feedback(vehicle_id: str, feedback_text: str):
    """
    100% OFFLINE FEEDBACK ANALYZER
    - No LLM
    - No HF model
    - No langchain
    """

    # 1. sentiment analysis (offline)
    sentiment, recurring = rule_sentiment(feedback_text)

    # 2. extract issue keywords
    extracted = extract_issues(feedback_text)

    # 3. compute rating
    rating = rate_service(sentiment, extracted)

    # 4. determine action
    if recurring or rating <= 2:
        action = "Schedule a recheck"
    else:
        action = "None"

    structured = {
        "vehicle_id": vehicle_id,
        "sentiment": sentiment,
        "service_rating": rating,
        "issues_reported": extracted,
        "is_recurring": recurring,
        "recommended_followup_action": action
    }

    # 5. Save to file
    store_feedback_tool(json.dumps(structured))

    return structured
