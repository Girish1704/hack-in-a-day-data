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

### Option A — One-command PowerShell bootstrap (download + extract + run)

From a fresh Windows machine, paste this into **PowerShell** (replace the URL with
**your** GitHub repo's archive link). It downloads the code, extracts it, and hands
off to `run.ps1`:

```powershell
$zip = "https://github.com/<your-org>/<your-repo>/archive/refs/heads/main.zip"
$dst = "$env:USERPROFILE\DataSecurityAgent"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Invoke-WebRequest $zip -OutFile "$dst\app.zip"
Expand-Archive "$dst\app.zip" -DestinationPath $dst -Force
$code = (Get-ChildItem $dst -Recurse -Filter app.py | Select-Object -First 1).DirectoryName
Set-Location $code
./run.ps1
```

(Equivalently, once you have the repo, just run the bundled **`setup.ps1`** — edit its
default `-ZipUrl` first.)

### Option B — Already downloaded? Just run the launcher

```powershell
cd <folder-with-app.py>
./run.ps1
```

`run.ps1` installs dependencies, creates `.env` from `.env.example` on first run
(opens it for you to fill in), checks/does `az login`, then starts the app. Run it
again after filling in `.env` and it launches Streamlit.

### Option C — Manual steps

```bash
copy .env.example .env      # then fill in your values
az login
pip install -r requirements.txt
streamlit run app.py
```

> The app orchestrates the three prompt agents itself through the Microsoft
> Foundry **Responses API** (`azure-ai-projects` 2.x): it calls the
> Classification agent, feeds its output to the Risk Detection agent, then feeds
> both to the Compliance Advisor agent. Each agent is referenced by **name**.
> There is no separate wiring step - create the three agents, set the `.env`,
> and run.

> **Security:** never commit your real `.env`. It is git-ignored; only the
> `.env.example` template is meant to be committed/shared.

### Environment Variables

| Variable | Source | Required |
|---|---|---|
| `PROJECT_ENDPOINT` | Microsoft Foundry Portal > Project > Overview | Yes |
| `AGENT_NAME` | Name of the Classification prompt agent | Yes |
| `RISK_AGENT_NAME` | Name of the Risk Detection prompt agent | Yes |
| `COMPLIANCE_AGENT_NAME` | Name of the Compliance Advisor prompt agent | Yes |
| `COSMOS_ENDPOINT` | Azure Portal > Cosmos DB > Keys | Yes |
| `COSMOS_KEY` | Azure Portal > Cosmos DB > Keys | Yes |
| `STORAGE_ACCOUNT_NAME` | Azure Portal > Storage Account | Yes |
| `STORAGE_ACCOUNT_KEY` | Azure Portal > Storage Account > Access Keys | Yes |
| `EVENT_GRID_ENDPOINT` | Azure Portal > Event Grid Topic > Overview | Yes |
| `EVENT_GRID_KEY` | Azure Portal > Event Grid Topic > Access Keys | Yes |

## Architecture

```
User → Streamlit App ─→ Classification Agent
            │                    │  (classifications)
            │                    ▼
            ├──────────→ Risk Detection Agent
            │                    │  (risk findings)
            │                    ▼
            └──────────→ Compliance Advisor Agent
                                 │  (CRITICAL/HIGH risks)
                                 ▼
                         Event Grid Topic → Logic App
                                              ↓        ↓
                                         Cosmos DB   Email/Teams
```

The Streamlit app calls the three agents in sequence (Responses API) and chains
each stage's output into the next.

## File Structure

```
codefiles/
├── app.py                 # Streamlit dashboard + 3-agent pipeline orchestration
├── cosmos_helper.py       # Cosmos DB operations
├── storage_helper.py      # Azure Blob Storage operations
├── event_grid_helper.py   # Event Grid publishing
├── run.ps1                # Plug-and-play launcher (install deps, .env, az login, run)
├── setup.ps1              # Bootstrap: download + extract the repo zip, then run.ps1
├── requirements.txt
├── .env.example           # Config template (copy to .env; .env is git-ignored)
├── Dockerfile
└── datasets/
    ├── customer_data.json
    ├── medical_records.json
    ├── financial_transactions.json
    ├── employee_data.json
    ├── access_policies.json
    └── access_logs.csv
```
