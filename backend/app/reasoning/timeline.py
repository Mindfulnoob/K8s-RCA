"""Incident Timeline Normalizer."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.models.timeline import TimelineEvent, EventSource, Severity
from backend.app.models.evidence import Evidence


class TimelineNormalizer:
    """Consolidates and chronologically sorts multi-source observability events into a unified incident timeline."""

    @classmethod
    def build_timeline(cls, evidence_list: List[Evidence]) -> List[TimelineEvent]:
        events: List[TimelineEvent] = []
        event_counter = 1

        for ev in evidence_list:
            source = EventSource.KUBERNETES
            if ev.source == "Prometheus":
                source = EventSource.PROMETHEUS
            elif ev.source == "Loki":
                source = EventSource.LOKI
            elif ev.source == "Jaeger":
                source = EventSource.JAEGER
            elif "deployment" in ev.query:
                source = EventSource.DEPLOYMENT

            severity = Severity.INFO
            summary_lower = ev.observation.summary.lower()
            if "fail" in summary_lower or "oom" in summary_lower or "panic" in summary_lower or "fatal" in summary_lower or "error" in summary_lower:
                severity = Severity.CRITICAL
            elif "warn" in summary_lower or "exhaust" in summary_lower or "restart" in summary_lower or "timeout" in summary_lower:
                severity = Severity.WARNING

            # Check if raw_data contained multiple timestamped events (e.g. k8s events or logs)
            raw = ev.raw_data
            if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], dict) and "timestamp" in raw[0]:
                for item in raw:
                    try:
                        ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    except Exception:
                        ts = ev.timestamp
                    
                    msg = item.get("message") or item.get("reason") or ev.observation.summary
                    title = item.get("reason") or item.get("level") or f"{source} Event"
                    
                    events.append(TimelineEvent(
                        id=f"evt-{event_counter}",
                        timestamp=ts,
                        source=source,
                        component=item.get("object") or ev.source_component or "cluster",
                        title=str(title),
                        description=str(msg),
                        severity=severity,
                        related_evidence_id=ev.id,
                        metadata=item
                    ))
                    event_counter += 1
            else:
                events.append(TimelineEvent(
                    id=f"evt-{event_counter}",
                    timestamp=ev.timestamp,
                    source=source,
                    component=ev.source_component or "cluster",
                    title=f"{source}: {ev.observation.summary[:40]}",
                    description=ev.observation.summary,
                    severity=severity,
                    related_evidence_id=ev.id,
                    metadata=ev.observation.details
                ))
                event_counter += 1

        # Sort chronologically
        events.sort(key=lambda e: e.timestamp)
        return events
