"""
Azure Blob Storage Helper Module
Provides functions to read data files from Azure Storage Account containers.
"""

from azure.storage.blob import BlobServiceClient
import json
import csv
import io


class StorageHelper:
    """Helper class for Azure Blob Storage operations."""

    def __init__(self, account_name: str, account_key: str):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={account_key};"
            f"EndpointSuffix=core.windows.net"
        )
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    def list_blobs(self, container_name: str) -> list:
        """List all blobs in a container."""
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing blobs in {container_name}: {str(e)}")
            return []

    def read_json(self, container_name: str, blob_name: str) -> dict:
        """Read and parse a JSON file from blob storage."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            data = blob_client.download_blob().readall()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            print(f"Error reading JSON blob {blob_name}: {str(e)}")
            return {}

    def read_csv(self, container_name: str, blob_name: str) -> list:
        """Read and parse a CSV file from blob storage. Returns list of dicts."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            data = blob_client.download_blob().readall().decode("utf-8")
            reader = csv.DictReader(io.StringIO(data))
            return list(reader)
        except Exception as e:
            print(f"Error reading CSV blob {blob_name}: {str(e)}")
            return []

    def upload_json(self, container_name: str, blob_name: str, data: dict) -> bool:
        """Upload a JSON object to blob storage."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            json_str = json.dumps(data, indent=2)
            blob_client.upload_blob(json_str, overwrite=True)
            return True
        except Exception as e:
            print(f"Error uploading JSON blob {blob_name}: {str(e)}")
            return False

    def read_with_limit(self, container_name: str, blob_name: str, row_limit: int = None) -> dict:
        """
        Read a JSON data file with optional row limit for Fast Scan mode.
        Returns the schema data with sample_rows truncated to row_limit.
        """
        data = self.read_json(container_name, blob_name)
        if not data:
            return {}

        if row_limit and "sample_rows" in data:
            data["sample_rows"] = data["sample_rows"][:row_limit]
            data["scan_note"] = f"Fast Scan: showing {len(data['sample_rows'])} of {data.get('total_rows', 'unknown')} total rows"

        return data

    def read_csv_with_limit(self, container_name: str, blob_name: str, row_limit: int = None) -> list:
        """Read a CSV file with optional row limit for Fast Scan mode."""
        rows = self.read_csv(container_name, blob_name)
        if row_limit:
            return rows[:row_limit]
        return rows
