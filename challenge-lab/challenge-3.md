# Challenge 03: Build the Risk Detection Agent and Connect Pipeline

## Overview

Now that you have a Data Classification Agent, you need a Risk Detection Agent that cross-references data classifications with access policies and activity logs to find security threats. In this challenge, you will create the second prompt agent, then connect it to the Classification Agent using **A2A (Agent-to-Agent)** so classifications automatically flow to risk analysis, creating your first multi-agent pipeline.

> **What changed:** The classic "Connected agents" feature is **not available** in the new Foundry Agent Service. Its successor is the **A2A protocol**: the Classification agent calls the Risk Detection agent as an A2A sub-agent. A2A is currently a public-preview feature configured through the SDK/REST API (there is no portal UI yet), so you wire it by running the provided `setup_a2a.py` script instead of clicking in the portal.

## Challenge Objectives

- Create a Risk Detection prompt agent with access analysis instructions
- Configure the agent to detect over-privilege, suspicious activity, and compliance gaps
- Connect the Risk Detection Agent to the Classification Agent using **A2A**
- Wire the pipeline by running `setup_a2a.py`
- Understand how the Classification agent delegates to sub-agents via the A2A tool

## Steps to Complete

### Task 1: Create the Risk Detection Agent

1. In the **Microsoft Foundry** portal, go to the **Build** section and select **Agents** in the left pane.

1. Select **Create agent**, enter the name `Risk-Detection-Agent`, and confirm (the name is permanent).

1. In the Agents playground setup pane, select the **Model**: **data-security-model**.

### Task 2: Write Risk Detection Instructions

1. In the **Instructions** text box, copy and paste the following:

   ```
   You are a Data Security Risk Detection Specialist. Your role is to analyze data classifications alongside access policies and activity logs to identify security risks, over-privileged access, suspicious activity patterns, and compliance violations.

   RISK DETECTION ANALYSIS:

   1. Over-Privilege Detection:
      - Compare each role's permissions against the data classifications
      - Flag roles with access to PII/PHI/PCI columns that do not require it for their job function
      - Identify roles with SELECT * permissions on tables containing sensitive data
      - Flag roles without data masking on sensitive columns
      - Detect roles with write/delete permissions on sensitive tables without justification
      - Flag intern, contractor, or temporary roles with access to sensitive data

   2. Access Anomaly Detection:
      - Identify access outside business hours (before 6 AM or after 10 PM)
      - Flag bulk data exports (SELECT * or large row counts on sensitive tables)
      - Detect access from unusual IP addresses or geographic locations
      - Identify users accessing tables outside their normal pattern
      - Flag excessive query volume from a single user in a short timeframe
      - Detect specific column targeting (e.g., querying only SSN and Name columns)

   3. Policy Compliance Gaps:
      - Flag roles missing MFA requirements when accessing sensitive data
      - Identify roles without audit logging enabled
      - Detect stale access reviews (last review date older than 90 days)
      - Flag missing data masking policies for PII/PHI/PCI columns
      - Identify broad access rules (e.g., "ALL TABLES" or "SELECT *")
      - Detect contractor or external users with unaudited access

   4. Cross-Reference Analysis:
      - Map classification results to access policies to find mismatches
      - Correlate anomalous log entries with the user's assigned role permissions
      - Identify patterns where multiple anomalies point to the same user or role
      - Flag users who accessed data they should not have based on their role

   SEVERITY LEVELS:
   - CRITICAL: Immediate threat - active data exfiltration, unauthorized PHI/PCI access, bulk export of sensitive data at unusual hours
   - HIGH: Significant risk - over-privileged roles with PII/PHI access, missing MFA on sensitive data access, foreign IP access
   - MEDIUM: Compliance gap - stale reviews, missing audit logs, broad permissions that should be narrowed
   - LOW: Improvement opportunity - missing data masking on low-risk fields, minor policy updates needed

   OUTPUT FORMAT:
   Return your risk analysis as a JSON object:

   {
     "risk_summary": {
       "total_risks_found": number,
       "critical": number,
       "high": number,
       "medium": number,
       "low": number,
       "highest_risk_role": "role_name",
       "highest_risk_user": "user_name"
     },
     "risks": [
       {
         "risk_id": "RISK-001",
         "severity": "CRITICAL|HIGH|MEDIUM|LOW",
         "category": "Access Control|Anomalous Activity|Compliance Gap",
         "description": "What the risk is and why it is dangerous",
         "user": "username (if applicable, otherwise empty string)",
         "role": "role_name",
         "affected_data": ["column or table names as a list"],
         "evidence": "Specific policy detail or log entry that creates the risk",
         "regulation_violated": ["GDPR", "HIPAA", "PCI-DSS"],
         "requires_approval": true
       }
     ]
   }

   IMPORTANT RULES:
   - Always cross-reference classifications with access policies - do not analyze them in isolation
   - Flag ANY role that has unmasked access to SSN, credit card numbers, or medical diagnoses
   - Intern and contractor roles accessing sensitive data should always be HIGH or CRITICAL
   - After-hours bulk exports of sensitive data are always CRITICAL
   - Access from foreign IP addresses to sensitive data is always HIGH
   - Include specific evidence (log entries, policy details) for every risk found
   ```

1. Paste the instructions into the **Instructions** box, then select **Save** to store them as version 1 of the agent.

### Task 3: Add Agent Description

1. If a **Description** field is available in the setup pane, add:

   ```
   Analyzes data classifications alongside access policies and activity logs to detect over-privileged roles, suspicious access patterns, and compliance violations. Returns structured JSON with severity-rated risks and evidence.
   ```

### Task 4: Connect Risk Detection Agent to Classification Agent using A2A

Now comes the key step: connecting the agents with **A2A**. Because A2A is configured through code today (no portal UI yet), you use the provided `setup_a2a.py` script. It does three things for you:

- **Enables incoming A2A** on the Risk Detection agent (publishes its *agent card* so it can be discovered and called).
- **Creates a RemoteA2A connection** on your project that points at the Risk Detection agent.
- **Rebuilds the Classification agent** with an **A2A tool** for that connection, plus pipeline instructions that tell it to delegate to the sub-agent.

1. On your lab VM, open a terminal (PowerShell) and get the code + configure the `.env` file. If you haven't already:

   ```powershell
   mkdir C:\Code
   ```

   Download and extract the code package, then open the `codefiles` folder in **Visual Studio Code**:

   ```
   https://github.com/CloudLabsAI-Azure/hack-in-a-day-data/archive/refs/heads/security-&-compliance-agent.zip
   ```

1. Rename **.env.example** to **.env** and fill in these values (from the notes you saved in Challenge 1 and the agent names from Challenges 2-3):

   ```text
   PROJECT_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/proj-default
   AGENT_NAME=Data-Classification-Agent
   RISK_AGENT_NAME=Risk-Detection-Agent
   COMPLIANCE_AGENT_NAME=Compliance-Advisor-Agent
   MODEL_DEPLOYMENT_NAME=data-security-model
   SUBSCRIPTION_ID=<your-subscription-id>
   RESOURCE_GROUP=challenge-rg-<inject key="DeploymentID" enableCopy="false"/>
   FOUNDRY_ACCOUNT=<your-foundry-account-name>
   PROJECT_NAME=proj-default
   ```

1. In the VS Code terminal, authenticate and install dependencies:

   ```bash
   az login
   pip install -r requirements.txt
   ```

1. Run the A2A wiring script:

   ```bash
   python setup_a2a.py
   ```

   At this stage only the **Risk Detection** agent exists, so the script wires **Risk** and skips Compliance with a note. You will run it again in Challenge 4 after creating the Compliance agent. Expected output:

   ```text
   Step 1/3: Enable incoming A2A on the available sub-agents
     [ok] Incoming A2A enabled on 'Risk-Detection-Agent'
     [skip] Agent 'Compliance-Advisor-Agent' not found yet - create it, then re-run this script.
   Step 2/3: Create RemoteA2A connections
     [ok] Connection 'risk-a2a' -> Risk-Detection-Agent
   Step 3/3: Attach A2A tools to the Classification agent
     [ok] 'Data-Classification-Agent' updated with 1 A2A tool(s) (new version: 2)
   A2A pipeline wired successfully.
   ```

   > **Note:** If the script reports a permissions error, confirm you were assigned the **Foundry Owner** (or **Foundry User**) role on the project in Challenge 1, then re-run.

### Task 5: Understand the A2A Hand-Off

The script updated the Classification agent so that, after classifying every column, it uses its **A2A tool** to delegate to the Risk Detection agent - sending the classification results together with the access policies and activity logs - and then includes the risk analysis in its response.

You do **not** need to hand-edit the Classification agent's instructions in the portal for the hand-off; `setup_a2a.py` applies the pipeline instructions (a new agent version) as part of the wiring. When you open **Data-Classification-Agent** in the portal you will see a new version with the A2A tool attached and the updated instructions.

<validation step="8faafdf3-98a0-421e-9bbe-52a2c08d1cdf" />

> **Congratulations** on completing the task! Now, it's time to validate it. Here are the steps:
> - Hit the Validate button for the corresponding task. If you receive a success message, you can proceed to the next task.
> - If not, carefully read the error message and retry the step, following the instructions in the lab guide.
> - If you need any assistance, please contact us at cloudlabs-support@spektrasystems.com. We are available 24/7 to help.

## Success Criteria

- Risk Detection Agent created as a prompt agent with the correct model deployment
- Agent identifies over-privileged roles, suspicious activity, and compliance gaps
- Agent returns structured JSON with severity ratings and evidence
- Risk Detection Agent connected to Classification Agent via **A2A** (`setup_a2a.py` ran successfully)
- Classification agent has a new version carrying the A2A tool and pipeline instructions
- Hand-off happens automatically without manual intervention

## Additional Resources

- [Enable incoming A2A on a Foundry agent](https://learn.microsoft.com/azure/foundry/agents/how-to/enable-agent-to-agent-endpoint)
- [Connect to an A2A agent endpoint from Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/agent-to-agent)
- [Principle of Least Privilege](https://learn.microsoft.com/security/zero-trust/develop/least-privilege)

Now, click **Next** to continue to **Challenge 04**.

![](media/page_no_5.png)