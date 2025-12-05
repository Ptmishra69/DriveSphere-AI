# agent_logic.py
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any
import uuid
import json

from sklearn.ensemble import IsolationForest
import numpy as np

from tools import read_activity_logs, append_alert
from rules import (
    is_unauthorized_access,
    rate_spike,
    high_error_rate,
    large_payload,
    unusual_endpoint_sequence
)

# baseline config - define allowed resources & normal sequences per agent
NORMAL_RESOURCE_MAP = {
    "DataAnalysisAgent": ["telematics_api", "vectorstore", "maintenance_db"],
    "DiagnosisAgent": ["vectorstore", "maintenance_db", "rca_db"],
    "SchedulingAgent": ["scheduler_db", "service_center_api"],
    "CustomerEngagementAgent": ["sms_api", "voice_api", "customer_db"],
    "FeedbackAgent": ["feedback_db", "maintenance_db"],
    "RCAAgent": ["rca_db", "vectorstore", "manufacturing_db"],
    "UEBAAgent": ["alert_db"]
}

# normal endpoint sequences (example)
NORMAL_SEQUENCES = {
    "DataAnalysisAgent": ["/ingest", "/analyze", "/report"],
    "SchedulingAgent": ["/availability", "/book_slot", "/confirm"],
    "DiagnosisAgent": ["/analyze", "/search_rca", "/report"]
}

# ML model cache (kept in memory)
_ml_model = None

def _extract_features_for_agent(records: List[Dict[str, Any]]) -> List[List[float]]:
    """
    For each sliding window (e.g., last N records grouped by minute),
    extract numerical features:
      - requests_per_minute (approx)
      - avg_payload_size
      - avg_latency_ms
      - error_ratio
      - unique_endpoints_count
    We will aggregate per agent for training / anomaly detection.
    """
    if not records:
        return []
    # group by minute
    buckets = {}
    from dateutil.parser import isoparse
    for r in records:
        t = isoparse(r["timestamp"])
        key = t.replace(second=0, microsecond=0).isoformat()
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(r)

    features = []
    for minute, recs in buckets.items():
        count = len(recs)
        payloads = [int(r.get("payload_size", 0)) for r in recs]
        latencies = [int(r.get("latency_ms", 0)) for r in recs]
        errors = sum(1 for r in recs if int(r.get("status_code", 200)) >= 400)
        endpoints = set(r.get("endpoint") for r in recs)
        f = [
            count,  # reqs per minute
            statistics.mean(payloads) if payloads else 0,
            statistics.mean(latencies) if latencies else 0,
            errors / count if count else 0,
            len(endpoints)
        ]
        features.append(f)
    return features

def _train_isolation_forest(X: List[List[float]]):
    global _ml_model
    if not X:
        _ml_model = None
        return None
    X_arr = np.array(X)
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_arr)
    _ml_model = model
    return model

def _score_features(features: List[List[float]]) -> List[float]:
    """
    Return anomaly scores: negative -> anomaly in sklearn's IsolationForest decision_function.
    """
    global _ml_model
    if _ml_model is None:
        return [0.0] * len(features)
    X_arr = np.array(features)
    scores = _ml_model.decision_function(X_arr)
    return scores.tolist()

def _compose_alert(record: Dict[str, Any], reason: str, severity: str = "medium") -> Dict[str, Any]:
    alert = {
        "alert_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_name": record.get("agent_name"),
        "agent_id": record.get("agent_id"),
        "reason": reason,
        "severity": severity,
        "evidence": record
    }
    append_alert(alert)
    return alert

def scan_and_detect(window_minutes: int = 15) -> List[Dict[str, Any]]:
    """
    Main entrypoint: scans recent logs (last window_minutes) and runs rules + ML anomaly detection.
    Returns list of alerts raised.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=window_minutes)

    logs = read_activity_logs()
    from dateutil.parser import isoparse
    recent = [r for r in logs if isoparse(r["timestamp"]) >= cutoff]

    # group by agent
    agents_map = defaultdict(list)
    for r in recent:
        agents_map[r["agent_name"]].append(r)

    alerts = []

    # Train per-agent ML baseline using last 24 hours logs (if available)
    # For simplicity we train on all historical logs (could be windowed)
    historical_features = []
    # build features for all agents combined (could be improved per-agent)
    full_logs = read_activity_logs()
    for agent, recs in defaultdict(list, {r["agent_name"]: [] for r in full_logs}).items():
        pass  # placeholder if needed

    # For this implementation, create features globally (all logs)
    features_all = []
    all_by_agent = defaultdict(list)
    for r in full_logs:
        all_by_agent[r["agent_name"]].append(r)
    for agent, recs in all_by_agent.items():
        feats = _extract_features_for_agent(recs)
        features_all.extend(feats)
    _train_isolation_forest(features_all)

    # Now run detection per agent
    for agent, recs in agents_map.items():
        # rule checks
        # unauthorized access detection: check each record
        for rec in recs:
            if is_unauthorized_access(rec, NORMAL_RESOURCE_MAP):
                alerts.append(_compose_alert(rec, "unauthorized_resource_access", "high"))

            if large_payload(rec):
                alerts.append(_compose_alert(rec, "large_payload_possible_exfiltration", "high"))

        # rate spike check
        if rate_spike(recs, threshold_per_minute=120):
            alerts.append(_compose_alert(recs[-1], "rate_spike", "high"))

        # high error rate
        if high_error_rate(recs, error_ratio_threshold=0.25):
            alerts.append(_compose_alert(recs[-1], "high_error_rate", "medium"))

        # unusual endpoint sequence
        if unusual_endpoint_sequence(recs, NORMAL_SEQUENCES):
            alerts.append(_compose_alert(recs[-1], "unusual_endpoint_sequence", "medium"))

        # ML anomaly detection on features for this agent
        feats = _extract_features_for_agent(recs)
        scores = _score_features(feats)
        # lower score -> more anomalous (IsolationForest returns higher for normal, lower for anomalies)
        for i, s in enumerate(scores):
            if s < -0.15:  # threshold; tune in production
                # pick an evidence record from that minute (any)
                ev = recs[0] if recs else {}
                alerts.append(_compose_alert(ev, f"ml_anomaly_score={s:.3f}", "medium"))

    return alerts
