"""
AI-Powered Data Security & Compliance Agent
Streamlit Dashboard Application
"""

import streamlit as st
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from azure.cosmos import CosmosClient, exceptions
import uuid
import re
import time
import pandas as pd
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential, AzureCliCredential

load_dotenv()


# ---------------------------------------------------------------------------
# Configuration helpers (support both new and legacy variable names)
# ---------------------------------------------------------------------------
def get_project_endpoint():
    """Foundry project endpoint. Accepts the new PROJECT_ENDPOINT or the
    legacy AGENT_API_ENDPOINT name so older .env files keep working."""
    return os.getenv("PROJECT_ENDPOINT") or os.getenv("AGENT_API_ENDPOINT")


def get_agent_name():
    """Classification agent NAME (new Foundry references agents by name).
    Falls back to the legacy AGENT_ID variable name if that's all that's set."""
    return os.getenv("AGENT_NAME") or os.getenv("AGENT_ID")

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Security Agent",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------
def validate_configuration():
    required_vars = {
        "PROJECT_ENDPOINT": get_project_endpoint(),
        "AGENT_NAME": get_agent_name(),
    }
    optional_vars = {
        "COSMOS_ENDPOINT": os.getenv("COSMOS_ENDPOINT"),
        "COSMOS_KEY": os.getenv("COSMOS_KEY"),
        "STORAGE_ACCOUNT_NAME": os.getenv("STORAGE_ACCOUNT_NAME"),
        "STORAGE_ACCOUNT_KEY": os.getenv("STORAGE_ACCOUNT_KEY"),
        "EVENT_GRID_ENDPOINT": os.getenv("EVENT_GRID_ENDPOINT"),
        "EVENT_GRID_KEY": os.getenv("EVENT_GRID_KEY"),
    }
    missing_required = [k for k, v in required_vars.items() if not v or v.strip() == ""]
    missing_optional = [k for k, v in optional_vars.items() if not v or v.strip() == ""]
    return missing_required, missing_optional


def show_setup_guide(missing_required, missing_optional):
    st.error("Configuration Required")
    st.markdown("""
    ### Setup Guide

    Edit the `.env` file in the codefiles folder with your credentials.
    """)
    if missing_required:
        st.warning(f"**Missing required variables:** {', '.join(missing_required)}")
    if missing_optional:
        st.info(f"**Missing optional variables (some features disabled):** {', '.join(missing_optional)}")
    st.stop()


missing_required, missing_optional = validate_configuration()
if missing_required:
    show_setup_guide(missing_required, missing_optional)

# ---------------------------------------------------------------------------
# CSS Styling & Animations
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ---- Animated Gradient Header ---- */
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .main-header {
        background: linear-gradient(-45deg, #0F62FE, #6366F1, #0F62FE, #A855F7);
        background-size: 400% 400%;
        animation: gradientShift 10s ease infinite;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(15,98,254,0.18);
    }
    .main-header h1 { color: #fff; margin: 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.5px; }
    .main-header p  { color: rgba(255,255,255,0.85); margin: 0.4rem 0 0; font-size: 1.05rem; }

    /* ---- Fade-in animation ---- */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeInUp 0.5s ease-out; }

    /* ---- Status pulse ---- */
    @keyframes statusPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.35); }
        50%      { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
    }
    .status-dot-ok {
        display: inline-block; width: 10px; height: 10px; border-radius: 50%;
        background: #10B981; animation: statusPulse 2s infinite; margin-right: 6px;
    }
    .status-dot-warn {
        display: inline-block; width: 10px; height: 10px; border-radius: 50%;
        background: #F59E0B; margin-right: 6px;
    }
    .status-dot-off {
        display: inline-block; width: 10px; height: 10px; border-radius: 50%;
        background: #EF4444; margin-right: 6px;
    }

    /* ---- Metric cards ---- */
    .metric-card {
        background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem;
        border: 1px solid #E5E7EB; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        animation: fadeInUp 0.5s ease-out;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
    }
    .metric-card .label { font-size: 0.82rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }
    .metric-card .value { font-size: 1.8rem; font-weight: 700; color: #111827; }

    /* severity colors */
    .sev-critical { border-left: 4px solid #EF4444; }
    .sev-high     { border-left: 4px solid #F97316; }
    .sev-medium   { border-left: 4px solid #F59E0B; }
    .sev-low      { border-left: 4px solid #10B981; }

    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 6px;
        font-size: 0.75rem; font-weight: 600; color: #fff; letter-spacing: 0.3px;
    }
    .badge-critical { background: #EF4444; }
    .badge-high     { background: #F97316; }
    .badge-medium   { background: #F59E0B; color: #111; }
    .badge-low      { background: #10B981; }
    .badge-pii      { background: #EF4444; }
    .badge-phi      { background: #8B5CF6; }
    .badge-pci      { background: #F97316; }
    .badge-conf     { background: #F59E0B; color: #111; }
    .badge-public   { background: #10B981; }

    /* ---- Completion banner ---- */
    .completion-banner {
        padding: 1.2rem; border-radius: 10px; text-align: center; margin: 1rem 0;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        box-shadow: 0 4px 16px rgba(16,185,129,0.25);
        animation: fadeInUp 0.5s ease-out;
    }
    .completion-banner h3 { margin: 0; color: #fff; font-size: 1.15rem; }
    .completion-banner p  { margin: 0.3rem 0 0; color: rgba(255,255,255,0.9); font-size: 0.92rem; }

    /* ---- Buttons ---- */
    .stButton>button {
        background: linear-gradient(135deg, #0F62FE 0%, #6366F1 100%);
        color: #fff; font-weight: 600; border: none; padding: 0.7rem 1.8rem;
        border-radius: 8px; transition: all 0.25s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15,98,254,0.3);
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label { color: #E2E8F0 !important; }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] {
        background: #F3F4F6; border-radius: 8px 8px 0 0;
        padding: 0.8rem 1.4rem; font-weight: 600; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #fff; border-bottom: 3px solid #0F62FE;
    }

    /* ---- Progress ---- */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0F62FE 0%, #A855F7 100%);
    }

    /* ---- Risk row animation ---- */
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-12px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    .risk-row { animation: slideIn 0.4s ease-out; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cosmos DB connection
# ---------------------------------------------------------------------------
@st.cache_resource
def get_cosmos_client():
    try:
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        db_name = os.getenv("DATABASE_NAME", "SecurityAgentDB")
        if not all([endpoint, key, db_name]):
            return None, None, None, None
        client = CosmosClient(endpoint, credential=key)
        database = client.get_database_client(db_name)
        scan_container = database.get_container_client("ScanResults")
        alerts_container = database.get_container_client("SecurityAlerts")
        return client, database, scan_container, alerts_container
    except Exception as e:
        return None, None, None, None


def save_scan_to_cosmos(scan_data: dict):
    _, _, scan_container, _ = get_cosmos_client()
    if not scan_container:
        return None
    try:
        item = {
            "id": str(uuid.uuid4()),
            "scanId": scan_data.get("scan_id", str(uuid.uuid4())),
            "scanType": scan_data.get("scan_type", "fast"),
            "timestamp": datetime.utcnow().isoformat(),
            "datasets_scanned": scan_data.get("datasets_scanned", []),
            "classification": scan_data.get("classification", {}),
            "risks": scan_data.get("risks", {}),
            "compliance": scan_data.get("compliance", {}),
            "risk_summary": scan_data.get("risk_summary", {}),
            "compliance_score": scan_data.get("compliance_score", 0),
            "raw_response": scan_data.get("raw_response", "")
        }
        scan_container.create_item(body=item)
        return item["id"]
    except Exception as e:
        return None


def save_alert_to_cosmos(alert: dict):
    _, _, _, alerts_container = get_cosmos_client()
    if not alerts_container:
        return None
    try:
        item = {
            "id": str(uuid.uuid4()),
            "alertId": str(uuid.uuid4()),
            "severity": alert.get("severity", "MEDIUM"),
            "risk_id": alert.get("risk_id", ""),
            "description": alert.get("description", ""),
            "user": alert.get("user", ""),
            "role": alert.get("role", ""),
            "affected_resource": alert.get("affected_resource", ""),
            "category": alert.get("category", ""),
            "scanId": alert.get("scan_id", ""),
            "status": "OPEN",
            "timestamp": datetime.utcnow().isoformat()
        }
        alerts_container.create_item(body=item)
        return item["id"]
    except Exception:
        return None


def get_scan_history(limit=20):
    _, _, scan_container, _ = get_cosmos_client()
    if not scan_container:
        return []
    try:
        return list(scan_container.query_items(
            query=f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}",
            enable_cross_partition_query=True
        ))
    except Exception:
        return []


def get_alerts(severity_filter=None, limit=50):
    _, _, _, alerts_container = get_cosmos_client()
    if not alerts_container:
        return []
    try:
        if severity_filter and severity_filter != "ALL":
            query = f"SELECT * FROM c WHERE c.severity = '{severity_filter}' ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
        else:
            query = f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
        return list(alerts_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Event Grid publishing
# ---------------------------------------------------------------------------
def publish_to_event_grid(risks: list, scan_id: str = ""):
    """Publish CRITICAL/HIGH risks to Event Grid. Returns (published, skipped) counts."""
    endpoint = os.getenv("EVENT_GRID_ENDPOINT")
    key = os.getenv("EVENT_GRID_KEY")
    if not endpoint or not key:
        return 0, len(risks)
    try:
        from azure.eventgrid import EventGridPublisherClient, EventGridEvent
        from azure.core.credentials import AzureKeyCredential

        client = EventGridPublisherClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        published, skipped = 0, 0
        for risk in risks:
            sev = risk.get("severity", "LOW").upper()
            if sev in ["CRITICAL", "HIGH"]:
                alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"

                # Build affected_data as a list to match Logic App Parse JSON schema
                affected_data_raw = risk.get("affected_data", risk.get("affected_resource", risk.get("affected_data_classification", "")))
                if isinstance(affected_data_raw, str):
                    affected_data_list = [affected_data_raw] if affected_data_raw else []
                elif isinstance(affected_data_raw, list):
                    affected_data_list = affected_data_raw
                else:
                    affected_data_list = []

                event = EventGridEvent(
                    id=str(uuid.uuid4()),
                    event_type="DataSecurity.RiskDetected",
                    subject=f"/security/risks/{risk.get('risk_id', 'unknown')}",
                    data={
                        "alert_id": alert_id,
                        "severity": sev,
                        "risk_id": risk.get("risk_id", ""),
                        "description": risk.get("description", risk.get("issue", "")),
                        "user": risk.get("user", ""),
                        "role": risk.get("role", ""),
                        "affected_data": affected_data_list,
                        "timestamp": datetime.utcnow().isoformat(),
                        "requires_approval": risk.get("requires_approval", risk.get("requires_human_approval", True)),
                        "scan_id": scan_id
                    },
                    data_version="1.0"
                )
                client.send([event])
                published += 1

                # Also save alert to Cosmos DB directly
                save_alert_to_cosmos({**risk, "scan_id": scan_id})
            else:
                skipped += 1
        return published, skipped
    except Exception as e:
        return 0, len(risks)

# ---------------------------------------------------------------------------
# Storage Account helpers
# ---------------------------------------------------------------------------
def load_from_storage(container: str, blob: str):
    """Load a file from Azure Blob Storage. Falls back to local datasets/ folder."""
    acct = os.getenv("STORAGE_ACCOUNT_NAME")
    key = os.getenv("STORAGE_ACCOUNT_KEY")
    if acct and key:
        try:
            from azure.storage.blob import BlobServiceClient
            conn = f"DefaultEndpointsProtocol=https;AccountName={acct};AccountKey={key};EndpointSuffix=core.windows.net"
            svc = BlobServiceClient.from_connection_string(conn)
            bc = svc.get_blob_client(container=container, blob=blob)
            data = bc.download_blob().readall().decode("utf-8")
            if blob.endswith(".json"):
                return json.loads(data)
            return data
        except Exception:
            pass

    # Fallback: local datasets folder
    local_path = os.path.join(os.path.dirname(__file__), "datasets", blob)
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            if blob.endswith(".json"):
                return json.load(f)
            return f.read()
    return None

# ---------------------------------------------------------------------------
# Agent response parsing
# ---------------------------------------------------------------------------
def _is_classification_obj(data: dict) -> bool:
    """Check if a dict looks like a classification output."""
    # Wrapper with columns list
    if any(k in data for k in ("columns", "classifications", "sensitivity_map", "classified_columns")):
        return True
    # Individual column object
    if "classification" in data and "column" in data:
        return True
    return False

def _is_risk_obj(data: dict) -> bool:
    """Check if a dict looks like a risk detection output."""
    if any(k in data for k in ("risks", "risk_summary", "risk_findings", "access_anomalies", "policy_risks",
                                "risk_detection", "security_risks", "risk_assessment", "detected_risks",
                                "risk_analysis", "vulnerabilities",
                                "access_policy_risks", "activity_anomalies", "scan_summary", "compliance_gaps")):
        return True
    # Individual risk item
    if "severity" in data and "risk_id" in data:
        return True
    return False

def _is_compliance_obj(data: dict) -> bool:
    """Check if a dict looks like a compliance output."""
    if any(k in data for k in ("remediation_plan", "compliance_mapping", "compliance_score",
                                "remediation", "recommendations", "compliance_framework",
                                "compliance_remediation", "compliance_assessment",
                                "compliance_and_remediation")):
        return True
    return False

def parse_agent_response(response_text: str) -> dict:
    """Parse the combined response from the 3-agent pipeline.

    Handles multiple agent output formats:
    - JSON inside ```json ... ``` code fences (with or without newlines)
    - JSON arrays or objects embedded directly in text
    - Individual JSON objects (one per column/risk) scattered in the response
    - A single large JSON with all three sections as nested keys
    """
    result = {
        "classification": None,
        "risks": None,
        "compliance": None,
    }

    # Collect individual items when agent returns them one-by-one
    classification_items = []
    risk_items = []

    def categorize(data):
        """Categorize a parsed JSON object into the right result bucket."""
        if isinstance(data, list):
            # A list of items - check the first item to decide category
            if data and isinstance(data[0], dict):
                if _is_classification_obj(data[0]):
                    result["classification"] = {"columns": data}
                    return True
                elif _is_risk_obj(data[0]):
                    result["risks"] = {"risks": data}
                    return True
            return False

        if not isinstance(data, dict):
            return False

        # Check if the top-level object contains ALL three sections
        has_cls = any(k in data for k in ("columns", "classifications", "classified_columns", "data_classification"))
        has_risk = any(k in data for k in ("risks", "risk_summary", "risk_findings", "access_anomalies",
                                            "risk_detection", "security_risks", "detected_risks",
                                            "access_policy_risks", "activity_anomalies", "scan_summary"))
        has_comp = any(k in data for k in ("compliance_score", "remediation_plan", "compliance_mapping", "remediation",
                                            "recommendations", "compliance_remediation", "compliance_assessment",
                                            "compliance_and_remediation"))
        if sum([has_cls, has_risk, has_comp]) >= 2:
            # Combined output - split into sections
            cls_keys = ("columns", "classifications", "classified_columns", "data_classification")
            risk_keys = ("risks", "risk_summary", "risk_findings", "access_anomalies", "policy_risks",
                         "risk_detection", "security_risks", "detected_risks", "risk_assessment", "risk_analysis",
                         "access_policy_risks", "activity_anomalies", "scan_summary", "compliance_gaps")
            comp_keys = ("compliance_score", "remediation_plan", "compliance_mapping", "remediation",
                         "recommendations", "compliance_framework", "approval_queue",
                         "compliance_remediation", "compliance_assessment", "compliance_and_remediation")
            cls_data = {k: v for k, v in data.items() if k in cls_keys}
            risk_data = {k: v for k, v in data.items() if k in risk_keys}
            comp_data = {k: v for k, v in data.items() if k in comp_keys}
            other_data = {k: v for k, v in data.items() if k not in cls_keys and k not in risk_keys and k not in comp_keys}

            # Unwrap wrapper keys in split results
            for wk in ("risk_detection", "risk_assessment", "security_risks", "detected_risks", "risk_analysis"):
                if wk in risk_data and isinstance(risk_data[wk], (dict, list)):
                    val = risk_data.pop(wk)
                    if isinstance(val, dict):
                        risk_data.update(val)
                    elif isinstance(val, list):
                        risk_data["risks"] = val
                    break
            for wk in ("compliance_remediation", "compliance_assessment", "compliance_and_remediation"):
                if wk in comp_data and isinstance(comp_data[wk], (dict, list)):
                    val = comp_data.pop(wk)
                    if isinstance(val, dict):
                        comp_data.update(val)
                    break

            if cls_data:
                result["classification"] = {**cls_data, **{k: v for k, v in other_data.items() if k in ("scan_id", "scan_mode", "timestamp")}}
            if risk_data:
                result["risks"] = risk_data
            if comp_data:
                result["compliance"] = comp_data
            return True

        # Single-section objects
        if _is_classification_obj(data):
            if "column" in data and "classification" in data:
                # Individual column classification
                classification_items.append(data)
            elif result["classification"] is None:
                result["classification"] = data
            return True
        elif _is_risk_obj(data):
            if "risk_id" in data and "severity" in data and "risks" not in data:
                risk_items.append(data)
            elif result["risks"] is None:
                result["risks"] = data
            return True
        elif _is_compliance_obj(data):
            if result["compliance"] is None:
                result["compliance"] = data
            return True
        return False

    # Strategy 1: JSON code fences (flexible: with/without newline, with/without trailing whitespace)
    json_blocks = re.findall(r'```(?:json)?\s*\n?(.*?)```', response_text, re.DOTALL)
    for block in json_blocks:
        block = block.strip()
        if not block:
            continue
        try:
            data = json.loads(block)
            categorize(data)
        except json.JSONDecodeError:
            continue

    # Strategy 2: Find top-level JSON arrays in text (outside code fences)
    if not any(result.values()):
        array_matches = re.findall(r'(\[[\s\S]*?\])\s*(?:\n|$)', response_text)
        for arr_str in array_matches:
            try:
                data = json.loads(arr_str)
                categorize(data)
            except json.JSONDecodeError:
                continue

    # Strategy 3: Find standalone JSON objects (outside code fences)
    if not all(result.values()):
        # Remove code-fenced regions first
        cleaned = re.sub(r'```(?:json)?\s*\n?.*?```', '', response_text, flags=re.DOTALL)
        # Match objects at any nesting depth
        brace_depth = 0
        start = -1
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if brace_depth == 0:
                    start = i
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0 and start >= 0:
                    candidate = cleaned[start:i+1]
                    try:
                        data = json.loads(candidate)
                        categorize(data)
                    except json.JSONDecodeError:
                        pass
                    start = -1

    # Merge individual items collected from scattered objects
    if classification_items and result["classification"] is None:
        result["classification"] = {"columns": classification_items}
    elif classification_items and result["classification"] is not None:
        existing = result["classification"]
        if "columns" not in existing and "classifications" not in existing:
            existing["columns"] = classification_items

    if risk_items and result["risks"] is None:
        result["risks"] = {"risks": risk_items}
    elif risk_items and result["risks"] is not None:
        existing = result["risks"]
        if "risks" not in existing and "risk_findings" not in existing:
            existing["risks"] = risk_items

    # Post-process: unwrap any remaining wrapper keys in risk data
    if result["risks"] and isinstance(result["risks"], dict):
        for wk in ("risk_detection", "risk_assessment", "security_risks", "detected_risks", "risk_analysis"):
            if wk in result["risks"] and isinstance(result["risks"][wk], (dict, list)):
                val = result["risks"].pop(wk)
                if isinstance(val, dict):
                    result["risks"].update(val)
                elif isinstance(val, list):
                    result["risks"]["risks"] = val
                break

        # Flatten access_policy_risks + activity_anomalies + compliance_gaps into a single "risks" list
        if "risks" not in result["risks"] or not result["risks"]["risks"]:
            flat_risks = []
            for rk in ("access_policy_risks", "activity_anomalies", "compliance_gaps", "policy_risks"):
                items = result["risks"].get(rk)
                if isinstance(items, list):
                    flat_risks.extend(items)
            if flat_risks:
                result["risks"]["risks"] = flat_risks

        # Normalize scan_summary → risk_summary
        if "scan_summary" in result["risks"] and "risk_summary" not in result["risks"]:
            result["risks"]["risk_summary"] = result["risks"].pop("scan_summary")

    # Final fallback: parse text/markdown sections when no JSON was found for risks/compliance
    if result["risks"] is None:
        result["risks"] = _parse_risks_from_text(response_text)
    if result["compliance"] is None:
        result["compliance"] = _parse_compliance_from_text(response_text)

    return result


def _parse_risks_from_text(text: str) -> dict | None:
    """Extract risk information from markdown/text when no JSON block is available."""
    # Look for risk-related sections in the text
    risk_section = None
    patterns = [
        r'(?:###?\s*\d*\.?\s*Risk\s+Detection[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:Risk\s+Detection\s+Summary[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:Detected\s+Risks[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:###?\s*\d*\.?\s*Risk\s+Assessment[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:###?\s*\d*\.?\s*Security\s+Risks[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:###?\s*\d*\.?\s*Risk\s+Analysis[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
        r'(?:###?\s*\d*\.?\s*Vulnerabilities[^\n]*\n)(.*?)(?=###|---\s*\n###|$)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            risk_section = m.group(1)
            break

    if not risk_section:
        return None

    # Extract risk summary counts
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    count_match = re.search(r'(\d+)\s*critical', risk_section, re.IGNORECASE)
    if count_match:
        summary["critical"] = int(count_match.group(1))
    count_match = re.search(r'(\d+)\s*high', risk_section, re.IGNORECASE)
    if count_match:
        summary["high"] = int(count_match.group(1))
    count_match = re.search(r'(\d+)\s*medium', risk_section, re.IGNORECASE)
    if count_match:
        summary["medium"] = int(count_match.group(1))
    count_match = re.search(r'(\d+)\s*low', risk_section, re.IGNORECASE)
    if count_match:
        summary["low"] = int(count_match.group(1))

    # Extract individual risk items from bullet points
    risks = []
    bullets = re.findall(r'[-*]\s+(.+)', risk_section)
    for idx, bullet in enumerate(bullets):
        # Determine severity from text
        sev = "MEDIUM"
        bullet_lower = bullet.lower()
        if "critical" in bullet_lower:
            sev = "CRITICAL"
        elif "high" in bullet_lower:
            sev = "HIGH"
        elif "low" in bullet_lower:
            sev = "LOW"

        # Determine category
        category = "General"
        if any(w in bullet_lower for w in ("access", "permission", "role", "privilege")):
            category = "Access Control"
        elif any(w in bullet_lower for w in ("encrypt", "mask", "plaintext")):
            category = "Data Protection"
        elif any(w in bullet_lower for w in ("anomal", "after-hours", "bulk", "unusual", "foreign")):
            category = "Anomalous Activity"
        elif any(w in bullet_lower for w in ("compliance", "audit", "breach", "notification")):
            category = "Compliance Gap"

        risks.append({
            "risk_id": f"RISK-{idx+1:03d}",
            "severity": sev,
            "category": category,
            "description": bullet.strip(),
            "affected_resource": "",
            "recommended_action": "Review and remediate",
            "requires_human_approval": sev in ("CRITICAL", "HIGH")
        })

    if not risks and not any(summary.values()):
        return None

    return {"risk_summary": summary, "risks": risks}


def _parse_compliance_from_text(text: str) -> dict | None:
    """Extract compliance/remediation info from markdown/text when no JSON is available."""
    comp_section = None
    patterns = [
        r'(?:###?\s*\d*\.?\s*Compliance\s+Mapping[^\n]*\n)(.*?)(?=###?\s*\d*\.?\s*(?:Recommended|$))',
        r'(?:###?\s*\d*\.?\s*Remediation[^\n]*\n)(.*?)(?=###?\s*\d*\.?|$)',
        r'(?:###?\s*\d*\.?\s*Compliance[^\n]*\n)(.*?)(?=###?\s*\d*\.?|$)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            comp_section = m.group(1)
            break

    if not comp_section:
        # Try to grab everything from "Regulatory Violations" or "Remediation" onwards
        m = re.search(r'((?:Regulatory|Remediation|Compliance)[^\n]*\n.*)', text, re.DOTALL | re.IGNORECASE)
        if m:
            comp_section = m.group(1)

    if not comp_section:
        return None

    # Extract compliance score if mentioned
    score = 0
    score_match = re.search(r'compliance\s+score[:\s]*(\d+)', comp_section, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))

    # Extract remediation items from markdown table rows
    remediation = []
    # Match table rows: | REM-001 | Action | Priority | Assigned | Regulation |
    table_rows = re.findall(r'\|\s*(REM-\d+|\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+?)\s*\|', comp_section)
    for row in table_rows:
        step_id, action, priority, assigned, regulation = [x.strip() for x in row]
        remediation.append({
            "action": action,
            "priority": priority,
            "assigned_to": assigned,
            "regulation": [r.strip() for r in regulation.split(",")] if "," in regulation else [regulation],
            "description": action,
            "requires_human_approval": priority.lower() in ("immediate", "short-term")
        })

    # Also try bullet-point remediation items
    if not remediation:
        bullets = re.findall(r'[-*]\s+(?:\*\*)?([^*\n]+?)(?:\*\*)?\s*(?::|\u2014|-)\s*(.+)', comp_section)
        for idx, (action, desc) in enumerate(bullets):
            remediation.append({
                "action": action.strip(),
                "priority": "Medium",
                "assigned_to": "Security Team",
                "regulation": [],
                "description": desc.strip(),
                "requires_human_approval": True
            })

    # Extract compliance mapping
    mapping = []
    reg_patterns = [
        ("GDPR", r'GDPR[^.\n]*[.\n]'),
        ("HIPAA", r'HIPAA[^.\n]*[.\n]'),
        ("PCI-DSS", r'PCI-?DSS[^.\n]*[.\n]'),
    ]
    for reg_name, pat in reg_patterns:
        matches = re.findall(pat, comp_section, re.IGNORECASE)
        for match_text in matches[:1]:  # Take first mention
            mapping.append({
                "regulation": reg_name,
                "description": match_text.strip().rstrip("."),
                "status": "Non-Compliant"
            })

    if not remediation and not mapping and score == 0:
        return None

    # Estimate a compliance score based on the number of issues if not explicitly given
    if score == 0 and (remediation or mapping):
        total_issues = len(remediation) + len(mapping)
        score = max(10, 100 - (total_issues * 8))  # rough estimate

    return {
        "compliance_score": score,
        "remediation_plan": remediation,
        "compliance_mapping": mapping
    }

# ---------------------------------------------------------------------------
# Azure credential helper
# ---------------------------------------------------------------------------
@st.cache_resource
def get_azure_credential():
    """Get Azure credential, trying DefaultAzureCredential first, then interactive browser login."""
    try:
        cred = DefaultAzureCredential()
        # Force a token request to verify it works
        cred.get_token("https://management.azure.com/.default")
        return cred
    except Exception:
        pass

    try:
        cred = AzureCliCredential()
        cred.get_token("https://management.azure.com/.default")
        return cred
    except Exception:
        pass

    # Fallback: open browser for interactive login
    try:
        cred = InteractiveBrowserCredential()
        cred.get_token("https://management.azure.com/.default")
        return cred
    except Exception as e:
        st.error(f"All authentication methods failed. Please run 'az login' in a terminal on this VM, then refresh the app.\n\nError: {e}")
        return None

# ---------------------------------------------------------------------------
# Agent API call
# ---------------------------------------------------------------------------
def call_agent_api(prompt: str):
    """Call the Classification prompt agent via the Microsoft Foundry Responses API.

    New Foundry model: agents are referenced by NAME through the Responses API
    (project.get_openai_client() -> responses.create with an agent_reference).
    The Classification agent delegates to the Risk Detection and Compliance
    Advisor agents via the A2A tool wired by setup_a2a.py, so a single call
    drives the whole pipeline and the combined text is returned.
    """
    try:
        project_endpoint = get_project_endpoint()
        agent_name = get_agent_name()
        if not all([project_endpoint, agent_name]):
            st.error("Missing agent configuration. Check PROJECT_ENDPOINT and AGENT_NAME in your .env file.")
            return None

        with st.spinner("Authenticating with Azure ..."):
            credential = get_azure_credential()
            if credential is None:
                return None

        with st.spinner("Connecting to Microsoft Foundry ..."):
            project = AIProjectClient(endpoint=project_endpoint, credential=credential)
            openai_client = project.get_openai_client()

        with st.spinner("Creating conversation ..."):
            conversation = openai_client.conversations.create()

        with st.spinner("Running agent pipeline - Classification, Risk Detection, Compliance ..."):
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
                input=prompt,
            )

        # Prefer the convenience aggregate; fall back to walking output items.
        response_text = getattr(response, "output_text", "") or ""
        if not response_text.strip():
            parts = []
            for item in getattr(response, "output", []) or []:
                for content in getattr(item, "content", []) or []:
                    text = getattr(content, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
                    elif text is not None and hasattr(text, "value"):
                        parts.append(text.value)
            response_text = "\n".join(parts)

        if not response_text.strip():
            st.error("No response received from the agent.")
            return None

        return response_text

    except Exception as e:
        st.error(f"Error calling agent: {str(e)}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())
        return None

# ---------------------------------------------------------------------------
# Build scan prompt
# ---------------------------------------------------------------------------
def build_scan_prompt(datasets: list, access_policies, access_logs, scan_mode: str, row_limit: int) -> str:
    """Construct the prompt sent to the Classification Agent."""
    parts = [
        f"Analyze the following data assets for security classification, risk detection, and compliance.\n",
        f"SCAN MODE: {'Fast Scan (sample rows only)' if scan_mode == 'Fast' else 'Full Scan (all available rows)'}\n",
    ]

    for ds in datasets:
        if ds:
            table = ds.get("table_name", "Unknown")
            db = ds.get("database", "Unknown")
            total = ds.get("total_rows", "unknown")
            cols = ds.get("columns", [])
            rows = ds.get("sample_rows", [])
            if scan_mode == "Fast" and len(rows) > row_limit:
                rows = rows[:row_limit]

            parts.append(f"\n--- DATA ASSET: {table} (Database: {db}, Total Rows: {total}) ---")
            parts.append(f"Schema:\n```json\n{json.dumps(cols, indent=2)}\n```")
            parts.append(f"Sample Data ({len(rows)} rows):\n```json\n{json.dumps(rows, indent=2)}\n```")

    if access_policies:
        parts.append(f"\n--- ACCESS POLICIES ---\n```json\n{json.dumps(access_policies, indent=2)}\n```")

    if access_logs:
        if isinstance(access_logs, str):
            parts.append(f"\n--- ACCESS LOGS ---\n```\n{access_logs}\n```")
        elif isinstance(access_logs, list):
            parts.append(f"\n--- ACCESS LOGS ({len(access_logs)} entries) ---\n```\n{json.dumps(access_logs[:50], indent=2)}\n```")

    parts.append("""

IMPORTANT: Return your complete analysis as THREE separate JSON code blocks (wrapped in ```json ... ```), one for each section:

SECTION 1 - DATA CLASSIFICATION (```json block 1):
{
  "columns": [
    {
      "column": "ColumnName",
      "table": "TableName",
      "data_type": "VARCHAR(100)",
      "classification": "PII",
      "confidence": 0.95,
      "reason": "Contains personal names",
      "regulations": ["GDPR", "HIPAA"],
      "recommended_controls": ["encryption", "masking"]
    }
  ]
}

SECTION 2 - RISK DETECTION (```json block 2):
{
  "risk_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "risks": [
    {
      "risk_id": "RISK-001",
      "severity": "CRITICAL",
      "category": "Access Control",
      "description": "Description of the risk",
      "affected_resource": "ResourceName",
      "user": "username",
      "role": "RoleName",
      "recommended_action": "What to do",
      "requires_human_approval": true
    }
  ]
}

SECTION 3 - COMPLIANCE & REMEDIATION (```json block 3):
{
  "compliance_score": 45,
  "compliance_mapping": [
    {"regulation": "GDPR", "article": "Article 32", "status": "Non-Compliant", "description": "..."}
  ],
  "remediation_plan": [
    {
      "action": "Encrypt PII columns",
      "priority": "Immediate",
      "assigned_to": "DBA",
      "regulation": ["GDPR"],
      "description": "Apply AES-256 encryption",
      "requires_human_approval": true
    }
  ]
}

Do NOT use markdown tables or bullet points for the main output. Use ONLY the three JSON code blocks above. You may add brief text explanations between the blocks.
""")

    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Helper renderers
# ---------------------------------------------------------------------------
def severity_badge(sev: str) -> str:
    s = sev.upper()
    cls = {"CRITICAL": "badge-critical", "HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(s, "badge-low")
    return f'<span class="badge {cls}">{s}</span>'


def classification_badge(cls_name: str) -> str:
    c = cls_name.upper()
    badge = {"PII": "badge-pii", "PHI": "badge-phi", "PCI": "badge-pci", "CONFIDENTIAL": "badge-conf", "PUBLIC": "badge-public"}.get(c, "badge-public")
    return f'<span class="badge {badge}">{c}</span>'


def render_metric_card(label: str, value, extra_class: str = ""):
    return f"""
    <div class="metric-card {extra_class}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>"""

# ===========================================================================
# HEADER
# ===========================================================================
st.markdown("""
<div class="main-header">
    <h1>Data Security & Compliance Agent</h1>
    <p>Identify sensitive data, detect risky access patterns, and generate compliance recommendations</p>
</div>
""", unsafe_allow_html=True)

# ===========================================================================
# SIDEBAR
# ===========================================================================
with st.sidebar:
    st.markdown("### Connection Status")

    endpoint = get_project_endpoint()
    agent_name = get_agent_name()
    cosmos_ep = os.getenv("COSMOS_ENDPOINT")
    storage_name = os.getenv("STORAGE_ACCOUNT_NAME")
    eg_ep = os.getenv("EVENT_GRID_ENDPOINT")

    def status_dot(ok):
        return '<span class="status-dot-ok"></span>' if ok else '<span class="status-dot-off"></span>'

    st.markdown(f'{status_dot(endpoint and agent_name)} Foundry Agents', unsafe_allow_html=True)
    st.markdown(f'{status_dot(cosmos_ep)} Cosmos DB', unsafe_allow_html=True)
    st.markdown(f'{status_dot(storage_name)} Storage Account', unsafe_allow_html=True)
    st.markdown(f'{status_dot(eg_ep)} Event Grid', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Scan Settings")
    scan_mode = st.radio("Scan Mode", ["Fast", "Full"], index=0,
                         help="Fast: top 5 rows per table. Full: all available sample rows.")
    fast_row_limit = 5

    st.markdown("---")
    st.markdown("### Stats")
    history = get_scan_history(limit=100)
    st.metric("Total Scans", len(history))
    alerts_all = get_alerts(limit=100)
    st.metric("Active Alerts", sum(1 for a in alerts_all if a.get("status") in ("NEW", "OPEN")))

# ===========================================================================
# TABS
# ===========================================================================
tab_scan, tab_class, tab_risks, tab_fix, tab_alerts, tab_history = st.tabs([
    "Scan Data Assets",
    "Classification",
    "Risk Detection",
    "Remediation",
    "Alerts & Approvals",
    "Scan History"
])

# ---------------------------------------------------------------------------
# TAB 1: Scan Data Assets
# ---------------------------------------------------------------------------
with tab_scan:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Select Data Sources")

    col_left, col_right = st.columns([3, 1])
    with col_left:
        available_datasets = {
            "customer_data.json": "Customers (RetailDB)",
            "medical_records.json": "Medical Records (HealthcareDB)",
            "financial_transactions.json": "Financial Transactions (FinanceDB)",
            "employee_data.json": "Employees (HRDB)"
        }
        selected_files = st.multiselect(
            "Choose datasets to scan",
            options=list(available_datasets.keys()),
            default=list(available_datasets.keys()),
            format_func=lambda x: available_datasets[x]
        )
        include_policies = st.checkbox("Include access policies", value=True)
        include_logs = st.checkbox("Include access logs", value=True)

    with col_right:
        st.markdown(f"**Mode:** {scan_mode} Scan")
        if scan_mode == "Fast":
            st.caption(f"Reads top {fast_row_limit} rows per table")
        else:
            st.caption("Reads all available sample rows")
        st.markdown(f"**Datasets:** {len(selected_files)} selected")

    st.markdown("---")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        run_scan = st.button("Run Security Scan", type="primary", use_container_width=True)

    if run_scan:
        if not selected_files:
            st.error("Select at least one dataset to scan.")
        else:
            # Load datasets
            datasets = []
            progress = st.progress(0, text="Loading data sources ...")
            for i, fname in enumerate(selected_files):
                ds = load_from_storage("schemas", fname)
                if ds:
                    datasets.append(ds)
                progress.progress((i + 1) / (len(selected_files) + 2), text=f"Loaded {fname}")

            access_policies = None
            if include_policies:
                access_policies = load_from_storage("access-policies", "access_policies.json")
                progress.progress((len(selected_files) + 1) / (len(selected_files) + 2), text="Loaded access policies")

            access_logs = None
            if include_logs:
                access_logs = load_from_storage("access-logs", "access_logs.csv")
                progress.progress(1.0, text="Loaded access logs")

            time.sleep(0.3)
            progress.empty()

            # Build prompt
            prompt = build_scan_prompt(
                datasets=datasets,
                access_policies=access_policies,
                access_logs=access_logs,
                scan_mode=scan_mode,
                row_limit=fast_row_limit
            )

            # Call agent pipeline
            response_text = call_agent_api(prompt)

            if response_text:
                parsed = parse_agent_response(response_text)

                # Extract risk list for Event Grid
                risk_list = []
                if parsed["risks"]:
                    risk_list = parsed["risks"].get("risks", parsed["risks"].get("risk_findings",
                                parsed["risks"].get("detected_risks", parsed["risks"].get("security_risks", []))))
                    # Flatten nested category arrays if flat risks list is empty
                    if not risk_list:
                        for rk in ("access_policy_risks", "activity_anomalies", "compliance_gaps"):
                            items = parsed["risks"].get(rk)
                            if isinstance(items, list):
                                risk_list.extend(items)

                # Publish critical/high risks to Event Grid
                scan_id = str(uuid.uuid4())
                pub_count, skip_count = 0, 0
                if risk_list:
                    pub_count, skip_count = publish_to_event_grid(risk_list, scan_id=scan_id)

                # Save to Cosmos DB
                scan_result = {
                    "scan_id": scan_id,
                    "scan_type": scan_mode.lower(),
                    "datasets_scanned": selected_files,
                    "classification": parsed["classification"],
                    "risks": parsed["risks"],
                    "compliance": parsed["compliance"],
                    "risk_summary": parsed["risks"].get("risk_summary", {}) if parsed["risks"] else {},
                    "compliance_score": parsed["compliance"].get("compliance_score", 0) if parsed["compliance"] else 0,
                    "raw_response": response_text
                }
                cosmos_id = save_scan_to_cosmos(scan_result)

                # Store in session
                st.session_state["last_scan"] = scan_result
                st.session_state["last_scan_raw"] = response_text

                # Completion banner
                cls_ok = "Yes" if parsed["classification"] else "No"
                rsk_ok = "Yes" if parsed["risks"] else "No"
                cmp_ok = "Yes" if parsed["compliance"] else "No"
                st.markdown(f"""
                <div class="completion-banner">
                    <h3>Scan Complete</h3>
                    <p>{len(selected_files)} datasets analyzed &nbsp;|&nbsp; {pub_count} alerts published to Event Grid &nbsp;|&nbsp; {'Saved to Cosmos DB' if cosmos_id else 'Cosmos DB not connected'}</p>
                    <p style="font-size:0.85rem;margin-top:4px;">Classification: {cls_ok} &nbsp;|&nbsp; Risks: {rsk_ok} &nbsp;|&nbsp; Compliance: {cmp_ok}</p>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Debug: Raw Agent Response"):
                    st.text(response_text[:5000] if len(response_text) > 5000 else response_text)
                with st.expander("Debug: Parsed Sections"):
                    st.json({"classification_found": parsed["classification"] is not None,
                             "risks_found": parsed["risks"] is not None,
                             "compliance_found": parsed["compliance"] is not None})
                    if parsed["classification"]:
                        st.markdown("**Classification keys:**")
                        st.json(list(parsed["classification"].keys()) if isinstance(parsed["classification"], dict) else "list")
                    if parsed["risks"]:
                        st.markdown("**Risks keys:**")
                        st.json(list(parsed["risks"].keys()) if isinstance(parsed["risks"], dict) else "list")
                    if parsed["compliance"]:
                        st.markdown("**Compliance keys:**")
                        st.json(list(parsed["compliance"].keys()) if isinstance(parsed["compliance"], dict) else "list")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 2: Classification
# ---------------------------------------------------------------------------
with tab_class:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Data Classification Results")

    scan = st.session_state.get("last_scan")
    if scan and scan.get("classification"):
        cls_data = scan["classification"]

        # Try to extract column-level classifications
        columns = cls_data.get("columns", cls_data.get("classifications", cls_data.get("classified_columns", [])))

        if isinstance(columns, list) and columns:
            # Count by category
            counts = {}
            for col in columns:
                cat = col.get("classification", col.get("category", col.get("sensitivity", "PUBLIC"))).upper()
                counts[cat] = counts.get(cat, 0) + 1

            # Metric cards
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                st.markdown(render_metric_card("Total Columns", len(columns)), unsafe_allow_html=True)
            with mc2:
                st.markdown(render_metric_card("PII", counts.get("PII", 0), "sev-critical"), unsafe_allow_html=True)
            with mc3:
                st.markdown(render_metric_card("PHI", counts.get("PHI", 0), "sev-high"), unsafe_allow_html=True)
            with mc4:
                st.markdown(render_metric_card("PCI", counts.get("PCI", 0), "sev-medium"), unsafe_allow_html=True)
            with mc5:
                st.markdown(render_metric_card("Public", counts.get("PUBLIC", 0), "sev-low"), unsafe_allow_html=True)

            st.markdown("---")

            # Table
            rows_display = []
            for col in columns:
                cat = col.get("classification", col.get("category", col.get("sensitivity", "PUBLIC"))).upper()
                rows_display.append({
                    "Table": col.get("table", col.get("table_name", "")),
                    "Column": col.get("column_name", col.get("column", col.get("name", ""))),
                    "Type": col.get("data_type", col.get("type", "")),
                    "Classification": cat,
                    "Confidence": col.get("confidence", ""),
                    "Regulation": ", ".join(col.get("regulation", col.get("regulations", []))) if isinstance(col.get("regulation", col.get("regulations", [])), list) else str(col.get("regulation", "")),
                    "Action": col.get("recommended_action", col.get("action", ""))
                })

            df = pd.DataFrame(rows_display)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            # Show raw classification JSON
            st.json(cls_data)

        with st.expander("Raw Classification Output"):
            st.json(cls_data)
    else:
        st.info("Run a security scan first to see classification results.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 3: Risk Detection
# ---------------------------------------------------------------------------
with tab_risks:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Risk Detection Results")

    scan = st.session_state.get("last_scan")
    if scan and scan.get("risks"):
        risk_data = scan["risks"]
        risk_list = risk_data.get("risks", risk_data.get("risk_findings",
                    risk_data.get("detected_risks", risk_data.get("security_risks", []))))
        # Flatten nested category arrays if flat risks list is empty
        if not risk_list:
            risk_list = []
            for rk in ("access_policy_risks", "activity_anomalies", "compliance_gaps"):
                items = risk_data.get(rk)
                if isinstance(items, list):
                    risk_list.extend(items)

        # Summary
        summary = risk_data.get("risk_summary", risk_data.get("scan_summary", {}))
        if not summary and isinstance(risk_list, list):
            summary = {}
            for r in risk_list:
                s = r.get("severity", "LOW").upper()
                summary[s.lower()] = summary.get(s.lower(), 0) + 1

        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            st.markdown(render_metric_card("Critical", summary.get("critical", summary.get("CRITICAL", 0)), "sev-critical"), unsafe_allow_html=True)
        with rc2:
            st.markdown(render_metric_card("High", summary.get("high", summary.get("HIGH", 0)), "sev-high"), unsafe_allow_html=True)
        with rc3:
            st.markdown(render_metric_card("Medium", summary.get("medium", summary.get("MEDIUM", 0)), "sev-medium"), unsafe_allow_html=True)
        with rc4:
            st.markdown(render_metric_card("Low", summary.get("low", summary.get("LOW", 0)), "sev-low"), unsafe_allow_html=True)

        st.markdown("---")

        # Compliance score if present
        comp_score = risk_data.get("compliance_score")
        if comp_score is not None:
            st.markdown(f"**Compliance Score:** {comp_score}")
            st.progress(min(float(comp_score) / 100 if float(comp_score) > 1 else float(comp_score), 1.0))

        # Risk list
        if isinstance(risk_list, list):
            for i, risk in enumerate(risk_list):
                sev = risk.get("severity", "LOW").upper()
                sev_class = f"sev-{sev.lower()}"
                st.markdown(f"""
                <div class="metric-card {sev_class} risk-row" style="margin-bottom:0.8rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            {severity_badge(sev)}
                            <strong style="margin-left:8px;">{risk.get('risk_id', risk.get('id', f'RISK-{i+1:03d}'))}</strong>
                            - <span style="color:#6B7280;">{risk.get('category', '')}</span>
                        </div>
                        <span style="font-size:0.82rem;color:#9CA3AF;">{risk.get('affected_resource', risk.get('affected_data_classification', ''))}</span>
                    </div>
                    <p style="margin:0.5rem 0 0;color:#374151;">{risk.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.json(risk_data)

        with st.expander("Raw Risk Output"):
            st.json(risk_data)
    else:
        st.info("Run a security scan first to see risk detection results.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 4: Remediation & Compliance
# ---------------------------------------------------------------------------
with tab_fix:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Remediation & Compliance")

    scan = st.session_state.get("last_scan")
    if scan and scan.get("compliance"):
        comp_data = scan["compliance"]

        # Compliance score
        score = comp_data.get("compliance_score", comp_data.get("score", None))
        if score is not None:
            sc1, sc2 = st.columns([1, 3])
            with sc1:
                st.markdown(render_metric_card("Compliance Score", f"{score}{'%' if float(str(score)) > 1 else ''}"), unsafe_allow_html=True)
            with sc2:
                score_val = float(str(score))
                normalized = score_val / 100 if score_val > 1 else score_val
                st.progress(min(normalized, 1.0))

        st.markdown("---")

        # Remediation plans
        remediation = comp_data.get("remediation_plan", comp_data.get("remediation", comp_data.get("recommendations", [])))
        if isinstance(remediation, list) and remediation:
            st.markdown("#### Remediation Steps")
            for idx, item in enumerate(remediation):
                if isinstance(item, dict):
                    approval = item.get("requires_human_approval", item.get("approval_required", False))
                    label = "Needs Approval" if approval else "Auto-Approved"
                    icon = "lock" if approval else "check"
                    with st.expander(f"{idx+1}. {item.get('action', item.get('recommendation', item.get('title', 'Step')))} - {label}"):
                        st.write(item.get("description", item.get("reason", "")))
                        impl = item.get("implementation", item.get("sql", item.get("command", "")))
                        if impl:
                            st.code(impl, language="sql")
                        regs = item.get("regulation", item.get("regulations_violated", []))
                        if regs:
                            if isinstance(regs, list):
                                st.caption(f"Regulations: {', '.join(regs)}")
                            else:
                                st.caption(f"Regulation: {regs}")
                elif isinstance(item, str):
                    st.markdown(f"{idx+1}. {item}")

        # Compliance mapping
        mapping = comp_data.get("compliance_mapping", [])
        if isinstance(mapping, list) and mapping:
            st.markdown("---")
            st.markdown("#### Compliance Mapping")
            for m in mapping:
                if isinstance(m, dict):
                    st.markdown(f"- **{m.get('regulation', m.get('framework', ''))}** - {m.get('description', m.get('requirement', m.get('article', '')))}")
                elif isinstance(m, str):
                    st.markdown(f"- {m}")

        with st.expander("Raw Compliance Output"):
            st.json(comp_data)
    else:
        st.info("Run a security scan first to see remediation recommendations.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 5: Alerts & Approvals
# ---------------------------------------------------------------------------
with tab_alerts:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Security Alerts")

    col_filter, col_refresh = st.columns([2, 1])
    with col_filter:
        sev_filter = st.selectbox("Filter by severity", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("Refresh Alerts")

    alerts_list = get_alerts(severity_filter=sev_filter if sev_filter != "ALL" else None)

    if alerts_list:
        for alert in alerts_list:
            sev = alert.get("severity", "MEDIUM").upper()
            sev_class = f"sev-{sev.lower()}"
            status = alert.get("status", "NEW")
            ts = alert.get("timestamp", "")
            try:
                ts_display = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_display = ts

            status_color = {"NEW": "#EF4444", "ACKNOWLEDGED": "#F59E0B", "RESOLVED": "#10B981"}.get(status, "#6B7280")
            st.markdown(f"""
            <div class="metric-card {sev_class} risk-row" style="margin-bottom:0.8rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        {severity_badge(sev)}
                        <strong style="margin-left:8px;">{alert.get('risk_id', alert.get('id', '')[:8])}</strong>
                    </div>
                    <div>
                        <span class="badge" style="background:{status_color};">{status}</span>
                        <span style="font-size:0.8rem;color:#9CA3AF;margin-left:8px;">{ts_display}</span>
                    </div>
                </div>
                <p style="margin:0.5rem 0 0;color:#374151;">{alert.get('description', 'No description')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alerts found. Alerts appear here when CRITICAL or HIGH risks are published to Event Grid and processed by the Logic App.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 6: Scan History
# ---------------------------------------------------------------------------
with tab_history:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown("### Scan History")

    history = get_scan_history(limit=20)
    if history:
        for idx, item in enumerate(history):
            ts = item.get("timestamp", "")
            try:
                ts_display = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_display = ts

            scan_type = item.get("scanType", "unknown").capitalize()
            datasets = item.get("datasets_scanned", [])
            score = item.get("compliance_score", "N/A")
            risk_sum = item.get("risk_summary", {})

            with st.expander(f"{ts_display} - {scan_type} Scan - Score: {score}"):
                st.caption(f"Datasets: {', '.join(datasets) if datasets else 'N/A'}")
                if risk_sum:
                    st.json(risk_sum)
                if item.get("classification"):
                    st.markdown("**Classification:**")
                    st.json(item["classification"])
                if item.get("risks"):
                    st.markdown("**Risks:**")
                    st.json(item["risks"])
                if item.get("compliance"):
                    st.markdown("**Compliance:**")
                    st.json(item["compliance"])

                if st.button(f"Load this scan", key=f"load_hist_{idx}"):
                    st.session_state["last_scan"] = item
                    st.rerun()
    else:
        st.info("No scan history yet. Run a security scan to see past results here.")

    st.markdown("</div>", unsafe_allow_html=True)
