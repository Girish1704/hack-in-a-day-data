"""
Cosmos DB Helper Module
Provides functions to save and retrieve security scan data, alerts, and compliance reports.
"""

from azure.cosmos import CosmosClient, exceptions
import uuid
from datetime import datetime
import time


class CosmosDBHelper:
    """Helper class for Cosmos DB operations in the Data Security Agent."""

    def __init__(self, endpoint: str, key: str, database_name: str):
        self.client = CosmosClient(endpoint, credential=key)
        self.database = self.client.get_database_client(database_name)
        self.scan_container = self.database.get_container_client("ScanResults")
        self.alerts_container = self.database.get_container_client("SecurityAlerts")

    def _retry_operation(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return operation()
            except exceptions.CosmosHttpResponseError as e:
                if e.status_code == 429 and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
        return None

    def save_scan_result(self, scan_data: dict) -> str:
        """Save a complete scan result (classification + risks + compliance) to Cosmos DB."""
        item = {
            "id": str(uuid.uuid4()),
            "scanId": scan_data.get("scan_id", str(uuid.uuid4())),
            "scanType": scan_data.get("scan_type", "full"),
            "timestamp": datetime.utcnow().isoformat(),
            "datasets_scanned": scan_data.get("datasets_scanned", []),
            "classification": scan_data.get("classification", {}),
            "risks": scan_data.get("risks", {}),
            "compliance": scan_data.get("compliance", {}),
            "risk_summary": scan_data.get("risk_summary", {}),
            "compliance_score": scan_data.get("compliance_score", 0),
            "raw_response": scan_data.get("raw_response", "")
        }

        def create_item():
            created = self.scan_container.create_item(body=item)
            return created["id"]

        try:
            return self._retry_operation(create_item)
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 409:
                return item["id"]
            else:
                print(f"Error saving scan result: {e.message}")
                return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None

    def save_alert(self, alert_data: dict) -> str:
        """Save a security alert to Cosmos DB."""
        item = {
            "id": str(uuid.uuid4()),
            "severity": alert_data.get("severity", "MEDIUM"),
            "risk_id": alert_data.get("risk_id", ""),
            "description": alert_data.get("description", ""),
            "affected_resource": alert_data.get("affected_resource", ""),
            "category": alert_data.get("category", ""),
            "regulation": alert_data.get("regulation", []),
            "status": "NEW",
            "acknowledged": False,
            "timestamp": datetime.utcnow().isoformat()
        }

        def create_item():
            created = self.alerts_container.create_item(body=item)
            return created["id"]

        try:
            return self._retry_operation(create_item)
        except Exception as e:
            print(f"Error saving alert: {str(e)}")
            return None

    def get_scan_history(self, limit: int = 20) -> list:
        """Get recent scan results from Cosmos DB."""
        try:
            query = "SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
            items = list(self.scan_container.query_items(
                query=query,
                parameters=[{"name": "@limit", "value": limit}],
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Error retrieving scan history: {str(e)}")
            return []

    def get_alerts(self, severity_filter: str = None, limit: int = 50) -> list:
        """Get security alerts from Cosmos DB, optionally filtered by severity."""
        try:
            if severity_filter and severity_filter != "ALL":
                query = "SELECT * FROM c WHERE c.severity = @severity ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
                params = [
                    {"name": "@severity", "value": severity_filter},
                    {"name": "@limit", "value": limit}
                ]
            else:
                query = "SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
                params = [{"name": "@limit", "value": limit}]

            items = list(self.alerts_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Error retrieving alerts: {str(e)}")
            return []

    def update_alert_status(self, alert_id: str, severity: str, new_status: str) -> bool:
        """Update the status of a security alert."""
        try:
            item = self.alerts_container.read_item(item=alert_id, partition_key=severity)
            item["status"] = new_status
            item["acknowledged"] = new_status in ["ACKNOWLEDGED", "RESOLVED"]
            item["updated_at"] = datetime.utcnow().isoformat()
            self.alerts_container.replace_item(item=alert_id, body=item)
            return True
        except Exception as e:
            print(f"Error updating alert: {str(e)}")
            return False
