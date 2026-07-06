# AI-Powered Data Security & Compliance Agent

Streamlit dashboard for data security scanning, risk detection, and compliance reporting.

## Features

- **Sensitive Data Classification** - Scans schemas and sample data to identify PII, PHI, PCI, and confidential information
- **Risk Detection** - Cross-references access policies and activity logs to find over-privilege, anomalies, and compliance gaps
- **Compliance Remediation** - Generates fix plans mapped to GDPR, HIPAA, PCI-DSS with approval workflows
- **Event-Driven Alerts** - Publishes critical risks to Azure Event Grid, processed by Logic App
- **Scan History** - Stores all results in Cosmos DB for audit trail
- **Fast / Full Scan** - Choose between quick sample scan or comprehensive analysis

## Quick Start

### Prerequisites

- Python 3.11+
- Azure CLI installed and authenticated
- A Microsoft Foundry project with three **prompt agents** created (Classification, Risk Detection, Compliance Advisor)
- Azure Cosmos DB, Storage Account, Event Grid Topic, Logic App

### Setup

```bash
# Copy and edit environment config
copy .env.example .env

# Authenticate with Azure
az login

# Install dependencies
pip install -r requirements.txt

# Wire the A2A agent-to-agent hand-off (Classification -> Risk -> Compliance)
python setup_a2a.py

# Run the app
streamlit run app.py
```

> The app calls the Classification agent through the Microsoft Foundry
> **Responses API** (`azure-ai-projects` 2.x). The Classification agent
> delegates to the Risk Detection and Compliance Advisor agents via the
> **A2A tool** wired by `setup_a2a.py` (A2A is the successor to the
> deprecated "Connected agents" feature).

### Environment Variables

| Variable | Source | Required |
|---|---|---|
| `PROJECT_ENDPOINT` | Microsoft Foundry Portal > Project > Overview | Yes |
| `AGENT_NAME` | Name of the Classification prompt agent | Yes |
| `SUBSCRIPTION_ID` / `RESOURCE_GROUP` / `FOUNDRY_ACCOUNT` / `PROJECT_NAME` | Azure Portal / Foundry project | `setup_a2a.py` only |
| `RISK_AGENT_NAME` / `COMPLIANCE_AGENT_NAME` / `MODEL_DEPLOYMENT_NAME` | Names from the Foundry portal | `setup_a2a.py` only |
| `COSMOS_ENDPOINT` | Azure Portal > Cosmos DB > Keys | Yes |
| `COSMOS_KEY` | Azure Portal > Cosmos DB > Keys | Yes |
| `STORAGE_ACCOUNT_NAME` | Azure Portal > Storage Account | Yes |
| `STORAGE_ACCOUNT_KEY` | Azure Portal > Storage Account > Access Keys | Yes |
| `EVENT_GRID_ENDPOINT` | Azure Portal > Event Grid Topic > Overview | Yes |
| `EVENT_GRID_KEY` | Azure Portal > Event Grid Topic > Access Keys | Yes |

## Architecture

```
User → Streamlit App → Classification Agent ──(A2A)──> Risk Agent
                            (Responses API)  └─(A2A)──> Compliance Agent
                                                                    ↓
                                        Event Grid Topic ← CRITICAL/HIGH risks
                                              ↓
                                          Logic App
                                         ↓         ↓
                                    Cosmos DB    Email/Teams
```

## File Structure

```
codefiles/
├── app.py                 # Streamlit dashboard (Foundry Responses API)
├── setup_a2a.py           # One-time A2A pipeline wiring script
├── cosmos_helper.py       # Cosmos DB operations
├── storage_helper.py      # Azure Blob Storage operations
├── event_grid_helper.py   # Event Grid publishing
├── requirements.txt
├── .env / .env.example
├── Dockerfile
└── datasets/
    ├── customer_data.json
    ├── medical_records.json
    ├── financial_transactions.json
    ├── employee_data.json
    ├── access_policies.json
    └── access_logs.csv
```
