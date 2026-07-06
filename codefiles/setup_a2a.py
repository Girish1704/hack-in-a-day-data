"""
setup_a2a.py
============
Wires the security pipeline using Agent-to-Agent (A2A), the successor to the
deprecated "Connected agents" feature from the classic Foundry portal.

Run this after creating the prompt agents in the Microsoft Foundry portal:

  - Data-Classification-Agent   (pipeline entry point)
  - Risk-Detection-Agent        (A2A sub-agent, created in Challenge 3)
  - Compliance-Advisor-Agent    (A2A sub-agent, created in Challenge 4)

The script is idempotent and tolerant: you can run it in Challenge 3 (only the
Risk agent exists yet) to wire Risk, then run it again in Challenge 4 to also
wire Compliance. Any sub-agent that doesn't exist yet is skipped with a warning.

What it does (per available sub-agent)
--------------------------------------
1. Enables the incoming A2A protocol + publishes an agent card on the sub-agent.
2. Creates a RemoteA2A connection on the project pointing at the sub-agent.
3. Rebuilds the Classification agent with one A2A tool per wired connection,
   plus pipeline instructions telling it to delegate and return all results.

A2A is currently a public-preview feature configured through the SDK / REST API
only (no portal UI yet), which is why this lives in a script.

Prerequisites
-------------
  pip install -r requirements.txt
  az login
  # .env filled in (see .env.example)

Docs:
  https://learn.microsoft.com/azure/foundry/agents/how-to/enable-agent-to-agent-endpoint
  https://learn.microsoft.com/azure/foundry/agents/how-to/tools/agent-to-agent
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, A2APreviewTool

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (from .env)
# ---------------------------------------------------------------------------
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT") or os.getenv("AGENT_API_ENDPOINT")
CLASSIFICATION_AGENT = os.getenv("AGENT_NAME", "Data-Classification-Agent")
RISK_AGENT = os.getenv("RISK_AGENT_NAME", "Risk-Detection-Agent")
COMPLIANCE_AGENT = os.getenv("COMPLIANCE_AGENT_NAME", "Compliance-Advisor-Agent")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT_NAME", "data-security-model")

SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP")
FOUNDRY_ACCOUNT = os.getenv("FOUNDRY_ACCOUNT")
PROJECT_NAME = os.getenv("PROJECT_NAME", "proj-default")

# Token audiences
AI_SCOPE = "https://ai.azure.com/.default"
ARM_SCOPE = "https://management.azure.com/.default"

# Sub-agents that the Classification agent delegates to via A2A.
# (agent_name, connection_name, skill_id, skill_name, description)
SUB_AGENTS = [
    (
        RISK_AGENT, "risk-a2a", "risk-detection", "Security Risk Detection",
        "Analyzes classifications, access policies, and logs to detect security risks.",
    ),
    (
        COMPLIANCE_AGENT, "compliance-a2a", "compliance-advisory", "Compliance Advisory",
        "Maps risks to GDPR/HIPAA/PCI-DSS and generates remediation playbooks.",
    ),
]

# Classification instructions re-applied when we add the A2A tools. This is the
# same content the learner pasted in the portal (Challenge 2), plus a pipeline
# block directing delegation through the A2A tools instead of connected agents.
CLASSIFICATION_INSTRUCTIONS = """\
You are a Data Classification Specialist for enterprise security. Your role is to analyze database schemas and sample data to classify every column into one of the following sensitivity categories: PII, PHI, PCI, CONFIDENTIAL, or PUBLIC.

Classify every column, do not skip any. When a column could fall into multiple categories, choose the HIGHEST sensitivity (PHI > PII > PCI > CONFIDENTIAL > PUBLIC). Free-text "Notes" fields must be examined for embedded PII/PHI patterns in the sample data. Date of birth is PII. Email and phone are PII even when stored alone. Account numbers and routing numbers are PCI. Always include the applicable regulations (GDPR, HIPAA, PCI-DSS) for each classification.

Return the classification as a JSON object with per-column entries (column, data_type, classification, confidence, reason, regulations, recommended_controls) and a summary of counts.

PIPELINE INSTRUCTIONS (MANDATORY - A2A):
After classifying all columns in the data asset, you MUST use your A2A tools to run the rest of the pipeline, in order:
1. Delegate to the Risk Detection sub-agent (A2A): send it the classification results together with the access policies and activity logs, and ask for a security risk analysis.
2. After risk detection completes, delegate to the Compliance Advisor sub-agent (A2A): send it the classification results and the risk findings, and ask for regulation mapping and a remediation playbook.
3. Include the results from ALL available stages (classification, risk detection, compliance advisory) in your final response.
"""


def fail(msg):
    print(f"\n[ERROR] {msg}")
    sys.exit(1)


def require(value, name):
    if not value:
        fail(f"Missing required config: {name}. Set it in your .env file.")


def a2a_base_path(agent_name: str) -> str:
    """The A2A base path a caller uses to reach this agent."""
    return f"{PROJECT_ENDPOINT.rstrip('/')}/agents/{agent_name}/endpoint/protocols/a2a"


# ---------------------------------------------------------------------------
# Step 1: Enable incoming A2A + agent card on a sub-agent (data-plane REST PATCH)
# Returns True on success, False if the agent doesn't exist yet (skip).
# ---------------------------------------------------------------------------
def enable_incoming_a2a(agent_name, skill_id, skill_name, description, token):
    url = f"{PROJECT_ENDPOINT.rstrip('/')}/agents/{agent_name}?api-version=v1"
    body = {
        "agent_card": {
            "description": description,
            "version": "1.0",
            "skills": [{"id": skill_id, "name": skill_name, "description": description}],
        },
        "agent_endpoint": {"protocols": ["responses", "a2a"]},
    }
    resp = requests.patch(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=60,
    )
    if resp.status_code == 404:
        print(f"  [skip] Agent '{agent_name}' not found yet - create it, then re-run this script.")
        return False
    if resp.status_code >= 400:
        fail(
            f"Enabling incoming A2A on '{agent_name}' failed ({resp.status_code}).\n"
            f"       {resp.text}\n"
            f"       Make sure you have the Foundry User role on the project."
        )
    print(f"  [ok] Incoming A2A enabled on '{agent_name}'")
    return True


# ---------------------------------------------------------------------------
# Step 2: Create a RemoteA2A connection on the project (ARM management REST PUT)
# ---------------------------------------------------------------------------
def create_a2a_connection(connection_name, target_agent, arm_token):
    url = (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.CognitiveServices"
        f"/accounts/{FOUNDRY_ACCOUNT}/projects/{PROJECT_NAME}"
        f"/connections/{connection_name}?api-version=2025-04-01-preview"
    )
    body = {
        "properties": {
            "authType": "AgenticIdentity",
            "category": "RemoteA2A",
            "target": a2a_base_path(target_agent),
            "audience": "https://ai.azure.com",
            "Credentials": {},
            "metadata": {"AgentCardPath": "/agentCard/v1.0"},
        }
    }
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {arm_token}", "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=60,
    )
    if resp.status_code >= 400:
        fail(
            f"Creating A2A connection '{connection_name}' failed ({resp.status_code}).\n"
            f"       {resp.text}\n"
            f"       Check SUBSCRIPTION_ID / RESOURCE_GROUP / FOUNDRY_ACCOUNT / PROJECT_NAME in .env."
        )
    print(f"  [ok] Connection '{connection_name}' -> {target_agent}")


# ---------------------------------------------------------------------------
# Step 3: Add the A2A tools to the Classification agent (SDK create_version)
# ---------------------------------------------------------------------------
def wire_classification_agent(project, connection_names):
    tools = []
    for conn_name in connection_names:
        conn = project.connections.get(conn_name)
        tools.append(A2APreviewTool(project_connection_id=conn.id))

    agent = project.agents.create_version(
        agent_name=CLASSIFICATION_AGENT,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT,
            instructions=CLASSIFICATION_INSTRUCTIONS,
            tools=tools,
        ),
    )
    print(
        f"  [ok] '{CLASSIFICATION_AGENT}' updated with {len(tools)} A2A tool(s) "
        f"(new version: {getattr(agent, 'version', '?')})"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Microsoft Foundry - A2A pipeline wiring")
    print("=" * 44)

    require(PROJECT_ENDPOINT, "PROJECT_ENDPOINT")
    require(SUBSCRIPTION_ID, "SUBSCRIPTION_ID")
    require(RESOURCE_GROUP, "RESOURCE_GROUP")
    require(FOUNDRY_ACCOUNT, "FOUNDRY_ACCOUNT")

    credential = DefaultAzureCredential()
    try:
        ai_token = credential.get_token(AI_SCOPE).token
        arm_token = credential.get_token(ARM_SCOPE).token
    except Exception as e:
        fail(f"Could not acquire Azure tokens. Run 'az login' first.\n       {e}")

    project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    wired_connections = []
    print("\nStep 1/3: Enable incoming A2A on the available sub-agents")
    for agent_name, conn_name, skill_id, skill_name, desc in SUB_AGENTS:
        if enable_incoming_a2a(agent_name, skill_id, skill_name, desc, ai_token):
            wired_connections.append((conn_name, agent_name))

    if not wired_connections:
        fail("No sub-agents were found. Create the Risk/Compliance agents first, then re-run.")

    print("\nStep 2/3: Create RemoteA2A connections")
    for conn_name, agent_name in wired_connections:
        create_a2a_connection(conn_name, agent_name, arm_token)

    print("\nStep 3/3: Attach A2A tools to the Classification agent")
    wire_classification_agent(project, [c for c, _ in wired_connections])

    print("\n" + "=" * 44)
    print("A2A pipeline wired successfully.")
    print(f"  Entry point : {CLASSIFICATION_AGENT}")
    print(f"  Sub-agents  : {', '.join(a for _, a in wired_connections)}")
    if len(wired_connections) < len(SUB_AGENTS):
        print("  Note: not all sub-agents were wired yet. Re-run after creating the rest.")
    print("\nYou can now run:  streamlit run app.py")


if __name__ == "__main__":
    main()
