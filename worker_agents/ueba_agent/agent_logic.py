# agent_logic.py

import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any
import uuid

from sklearn.ensemble import IsolationForest
import numpy as np
from dateutil.parser import isoparse

from .tools import read_activity_logs, append_alert
from .rules import (
    is_unauthorized_access,
    rate_spike,
    high_error_rate,
    large_payload,
    unusual_endpoint_sequence
)

# ───────────────────────────────────────────────────────────────
# Allowed resource access map (baseline security policy)
# ───────────────────────────────────────────────────────────────
NORMAL_RESOURCE_MAP = {
    "DataAnalysisAgent": ["telematics_api", "vectorstore", "maintenance_db"],
    "DiagnosisAgent": ["vectorstore", "maintenance_db", "rca_db"],
    "SchedulingAgent": ["scheduler_db", "service_center_api"],
    "CustomerEngagementAgent": ["sms_api", "voice_api", "customer_db"],
    "FeedbackAgent": ["feedback_db", "maintenance_db"],
    "RCAAgent": ["rca_db", "vectorstore", "manufacturing_db"],
    "UEBAAgent": ["alert_db"]
}

# Expected endpoint sequences per agent (behavior model)
NORMAL_SEQUENCES = {
    "DataAnalysisAgent": ["/ingest", "/analyze", "/report"],
    "DiagnosisAgent": ["/analyze", "/search_rca", "/report"],
    "SchedulingAgent": ["/availability", "/book_slot", "/confirm"]
}

# Global ML model cache
_ml_model = None


# ───────────────────────────────────────────────────────────────
# Feature Extraction for ML Anomaly Detection
# ───────────────────────────────────────────────────────────────
def _extract_features_for_agent(records: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Builds feature vectors per-minute for an agent:
    [
        requests_per_minute,
        avg_payload_size,
        avg_latency_ms,
        error_ratio,
        unique_endpoints_count
    ]
    """
    if not records:
        return []

    # Group logs by minute
    buckets = {}
    for r in records:
        try:
            t = isoparse(r["timestamp"])
        except Exception:
            continue
        key = t.replace(second=0, microsecond=0).isoformat()
        buckets.setdefault(key, []).append(r)

    features = []
    for minute, recs in buckets.items():
        count = len(recs)
        payloads = [int(r.get("payload_size", 0)) for r in recs]
        latencies = [int(r.get("latency_ms", 0)) for r in recs]
        errors = sum(1 for r in recs if int(r.get("status_code", 200)) >= 400)
        endpoints = set(r.get("endpoint") for r in recs)

        feat = [
            count,
            statistics.mean(payloads) if payloads else 0,
            statistics.mean(latencies) if latencies else 0,
            errors / count if count else 0,
            len(endpoints)
        ]
        features.append(feat)

    return features


# ───────────────────────────────────────────────────────────────
# ML Model Training
# ───────────────────────────────────────────────────────────────
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
    Returns anomaly scores from IsolationForest.
    More negative → more anomalous.
    """
    global _ml_model
    if _ml_model is None or not features:
        return [0.0] * len(features)

    X_arr = np.array(features)
    scores = _ml_model.decision_function(X_arr)
    return scores.tolist()


# ───────────────────────────────────────────────────────────────
# Alert Composition
# ───────────────────────────────────────────────────────────────
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


# ───────────────────────────────────────────────────────────────
# Main UEBA Logic: Rule-Based + ML + Sequence Analysis
# ───────────────────────────────────────────────────────────────
def scan_and_detect(window_minutes: int = 15) -> List[Dict[str, Any]]:
    """
    Main UEBA process:
    1. Filter logs for recent activity
    2. Build ML baseline using *all* logs
    3. Run rule-based detections
    4. Run ML anomaly scoring
    5. Return all alerts
    """

    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=window_minutes)

    logs = read_activity_logs()

    # Filter logs within window
    recent = []
    for r in logs:
        try:
            if isoparse(r["timestamp"]) >= cutoff:
                recent.append(r)
        except Exception:
            continue

    # Group by agent
    agents_map = defaultdict(list)
    for r in recent:
        agents_map[r["agent_name"]].append(r)

    # ───────────────────────────────────────────────────────────────
    # Train ML Baseline on ALL logs (past behavior)
    # ───────────────────────────────────────────────────────────────
    full_logs = read_activity_logs()
    all_by_agent = defaultdict(list)
    for r in full_logs:
        all_by_agent[r["agent_name"]].append(r)

    features_all = []
    for agent, recs in all_by_agent.items():
        feats = _extract_features_for_agent(recs)
        features_all.extend(feats)

    _train_isolation_forest(features_all)

    # ───────────────────────────────────────────────────────────────
    # Detection Phase
    # ───────────────────────────────────────────────────────────────
    alerts = []

    for agent_name, recs in agents_map.items():

        # Rule-based checks (per record)
        for rec in recs:

            if is_unauthorized_access(rec, NORMAL_RESOURCE_MAP):
                alerts.append(_compose_alert(rec, "unauthorized_resource_access", "high"))

            if large_payload(rec):
                alerts.append(_compose_alert(rec, "large_payload_possible_exfiltration", "high"))

        # Rate spike detection
        if rate_spike(recs, threshold_per_minute=120):
            alerts.append(_compose_alert(recs[-1], "rate_spike", "high"))

        # High error rate detection
        if high_error_rate(recs, error_ratio_threshold=0.25):
            alerts.append(_compose_alert(recs[-1], "high_error_rate", "medium"))

        # Endpoint sequence anomaly
        if unusual_endpoint_sequence(recs, NORMAL_SEQUENCES):
            alerts.append(_compose_alert(recs[-1], "unusual_endpoint_sequence", "medium"))

        # ML anomaly detection
        feats = _extract_features_for_agent(recs)
        scores = _score_features(feats)

        for i, score in enumerate(scores):
            if score < -0.15:  # anomaly threshold (tunable)
                ev = recs[i] if i < len(recs) else recs[-1]
                alerts.append(_compose_alert(ev, f"ml_anomaly_score={score:.3f}", "medium"))

    return alerts
