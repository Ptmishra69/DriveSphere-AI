# sentiment_rules.py

def rule_sentiment(text: str):
    """
    Quick heuristic sentiment detector before LLM refinement.
    """
    text_l = text.lower()

    positive_terms = ["good", "great", "excellent", "satisfied", "happy"]
    negative_terms = ["bad", "poor", "worst", "unhappy", "angry", "slow", "rude"]
    complaint_terms = ["still", "not fixed", "issue", "problem", "noise"]

    score = 0

    for p in positive_terms:
        if p in text_l:
            score += 1
    for n in negative_terms:
        if n in text_l:
            score -= 1

    sentiment = "neutral"
    if score > 0:
        sentiment = "positive"
    elif score < 0:
        sentiment = "negative"

    has_complaint = any(c in text_l for c in complaint_terms)

    return sentiment, has_complaint
