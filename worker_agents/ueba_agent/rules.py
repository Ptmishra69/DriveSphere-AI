# rules.py
from typing import Dict, Any
from datetime import datetime, timedelta

def is_unauthorized_access(record: Dict[str, Any], normal_resource_map: Dict[str, list]) -> bool:
    """
    normal_resource_map: { "SchedulingAgent": ["scheduler_api", ...], ... }
    If agent accessed a resource not in its normal list => suspicious
    """
    agent = record.get("agent_name")
    resource = record.get("target_resource")
    allowed = normal_resource_map.get(agent, [])
    return resource not in allowed

def rate_spike(recent_records: list, threshold_per_minute: float = 60.0) -> bool:
    """
    recent_records: list of records for single agent for the last N minutes
    threshold_per_minute: maximum allowed avg requests per minute
    """
    if not recent_records:
        return False
    # compute time window minutes
    times = [r.get("timestamp") for r in recent_records]
    # parse timestamps (assume ISO)
    from dateutil.parser import isoparse
    parsed = [isoparse(t) for t in times]
    window_min = (max(parsed) - min(parsed)).total_seconds() / 60.0
    window_min = max(window_min, 1/60)  # avoid division by zero
    rate = len(parsed) / window_min
    return rate > threshold_per_minute

def high_error_rate(records: list, error_ratio_threshold: float = 0.2) -> bool:
    if not records:
        return False
    errors = sum(1 for r in records if int(r.get("status_code", 200)) >= 400)
    ratio = errors / len(records)
    return ratio >= error_ratio_threshold

def large_payload(record: Dict[str, Any], payload_threshold_bytes: int = 200000) -> bool:
    return int(record.get("payload_size", 0)) > payload_threshold_bytes

def unusual_endpoint_sequence(agent_history: list, normal_sequences: dict) -> bool:
    """
    agent_history: chronological list of endpoints
    normal_sequences: { "AgentName": [ "endpointA", "endpointB", ... ] }
    We flag if current last N endpoints deviate significantly.
    """
    agent = agent_history[0].get("agent_name") if agent_history else None
    if not agent:
        return False
    normal = normal_sequences.get(agent, [])
    seq = [r.get("endpoint") for r in agent_history[-len(normal):]] if normal else []
    # simple mismatch percentage
    mismatch = sum(1 for a, b in zip(seq, normal) if a != b) if seq else 0
    if normal:
        return (mismatch / len(normal)) > 0.5
    return False
