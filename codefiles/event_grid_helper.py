"""
Event Grid Helper Module
Provides functions to publish security risk events to Azure Event Grid.
"""

from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from azure.core.credentials import AzureKeyCredential
from datetime import datetime
import uuid


class EventGridHelper:
    """Helper class for publishing security events to Azure Event Grid."""

    def __init__(self, endpoint: str, key: str):
        self.client = EventGridPublisherClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

    def publish_risk_alert(self, risk_data: dict) -> bool:
        """
        Publish a security risk alert to Event Grid.
        Only publishes CRITICAL and HIGH severity risks.
        """
        severity = risk_data.get("severity", "LOW").upper()
        if severity not in ["CRITICAL", "HIGH"]:
            return False

        try:
            # Build affected_data as a list to match Logic App Parse JSON schema
            affected_data_raw = risk_data.get("affected_data", risk_data.get("affected_resource", risk_data.get("affected_data_classification", "")))
            if isinstance(affected_data_raw, str):
                affected_data_list = [affected_data_raw] if affected_data_raw else []
            elif isinstance(affected_data_raw, list):
                affected_data_list = affected_data_raw
            else:
                affected_data_list = []

            event = EventGridEvent(
                id=str(uuid.uuid4()),
                event_type="DataSecurity.RiskDetected",
                subject=f"/security/risks/{risk_data.get('risk_id', 'unknown')}",
                data={
                    "alert_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                    "severity": severity,
                    "risk_id": risk_data.get("risk_id", ""),
                    "description": risk_data.get("description", risk_data.get("issue", "")),
                    "user": risk_data.get("user", ""),
                    "role": risk_data.get("role", ""),
                    "affected_data": affected_data_list,
                    "timestamp": datetime.utcnow().isoformat(),
                    "requires_approval": risk_data.get("requires_approval", risk_data.get("requires_human_approval", True)),
                    "scan_id": risk_data.get("scan_id", "")
                },
                data_version="1.0"
            )

            self.client.send([event])
            return True

        except Exception as e:
            print(f"Error publishing event: {str(e)}")
            return False

    def publish_batch_alerts(self, risks: list) -> dict:
        """
        Publish multiple risk alerts to Event Grid.
        Filters to only CRITICAL and HIGH severity.
        Returns counts of published and skipped events.
        """
        published = 0
        skipped = 0

        for risk in risks:
            severity = risk.get("severity", "LOW")
            if severity in ["CRITICAL", "HIGH"]:
                if self.publish_risk_alert(risk):
                    published += 1
                else:
                    skipped += 1
            else:
                skipped += 1

        return {"published": published, "skipped": skipped}
