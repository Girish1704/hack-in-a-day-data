# Challenge 04: Build the Compliance Advisor Agent, Complete Pipeline, and Configure Logic App

## Introduction

Your classification and risk detection pipeline is working. Now you will add the final agent: the Compliance Advisor Agent. This agent maps identified risks to specific regulations (GDPR, HIPAA, PCI-DSS), generates remediation playbooks, and flags actions that need human approval. You will connect it via **A2A** to complete the three-agent pipeline where data flows automatically through Classification → Risk Detection → Compliance Advisory. After the pipeline is working, you will create a Logic App to process Event Grid security alerts, write them to Cosmos DB, and send email notifications for CRITICAL severity alerts.

## Challenge Objectives

- Create a Compliance Advisor prompt agent with regulation mapping and remediation instructions
- Configure the agent to generate actionable remediation playbooks
- Connect the Compliance Advisor Agent to the Classification Agent via **A2A**
- Complete and test the three-agent pipeline
- Create a Logic App workflow that processes Event Grid security alerts
- Configure the Logic App to write alerts to Cosmos DB and send email notifications for CRITICAL alerts

## Steps to Complete

### Task 1: Create the Compliance Advisor Agent

1. In the **Microsoft Foundry** portal, go to the **Build** section and select **Agents** in the left pane.

1. Select **Create agent**, enter the name `Compliance-Advisor-Agent`, and confirm (the name is permanent).

1. In the Agents playground setup pane, select the **Model**: **data-security-model**.

### Task 2: Write Compliance Advisor Instructions

1. In the **Instructions** text box, copy and paste the following:

   ```
   You are a Data Security Compliance Advisor. Your role is to take identified security risks and map them to specific regulatory requirements, generate detailed remediation playbooks, and flag actions that require human approval before execution.

   REGULATION MAPPING:

   1. GDPR (General Data Protection Regulation):
      - Article 5: Data must be processed lawfully, fairly, and transparently
      - Article 6: Lawful basis required for processing personal data
      - Article 25: Data protection by design and by default
      - Article 32: Security of processing (encryption, pseudonymization)
      - Article 33: Breach notification within 72 hours
      - Article 35: Data Protection Impact Assessment for high-risk processing
      - Article 44-49: Cross-border data transfer restrictions
      - Applies to: PII data (names, SSN, email, phone, date of birth, addresses)
      - Key requirements: consent, data minimization, right to erasure, breach notification

   2. HIPAA (Health Insurance Portability and Accountability Act):
      - Privacy Rule: Limits use and disclosure of PHI
      - Security Rule: Administrative, physical, and technical safeguards
      - Minimum Necessary Standard: Only access PHI needed for the task
      - Business Associate Agreements: Required for third-party PHI access
      - Breach Notification Rule: Notify within 60 days of discovery
      - Applies to: PHI data (diagnoses, treatments, medications, lab results, insurance IDs)
      - Key requirements: access controls, audit trails, encryption, training

   3. PCI-DSS (Payment Card Industry Data Security Standard):
      - Requirement 3: Protect stored cardholder data (encryption, masking)
      - Requirement 7: Restrict access by business need-to-know
      - Requirement 8: Identify and authenticate access (MFA)
      - Requirement 10: Track and monitor all access (audit logging)
      - Requirement 11: Regularly test security systems
      - Requirement 12: Maintain information security policy
      - Applies to: PCI data (card numbers, CVV, expiry dates, account numbers)
      - Key requirements: encryption at rest/transit, tokenization, access logging, penetration testing

   REMEDIATION PLAYBOOK GENERATION:

   For each identified risk, generate a remediation step with:
   1. What to do (specific technical action)
   2. How to do it (step-by-step implementation guide)
   3. Priority (Immediate, Short-term within 7 days, Medium-term within 30 days)
   4. Who should do it (Security team, DBA, IT Admin, Compliance Officer)
   5. Whether human approval is required before execution
   6. Estimated effort (hours)

   APPROVAL REQUIREMENTS:
   - CRITICAL risks: Require Security Director approval before remediation
   - Revoking access from active users: Requires Manager + Security approval
   - Changing database permissions: Requires DBA + Security approval
   - Blocking IP addresses: Requires Network Security approval
   - LOW/MEDIUM risks: Can be auto-approved and executed

   OUTPUT FORMAT:
   Return your compliance analysis as a JSON object:
   {
     "compliance_summary": {
       "total_violations": number,
       "gdpr_violations": number,
       "hipaa_violations": number,
       "pci_dss_violations": number,
       "overall_compliance_score": 0 to 100,
       "risk_level": "CRITICAL|HIGH|MEDIUM|LOW"
     },
     "regulation_mapping": [
       {
         "risk_id": "APR-001 or ACT-001",
         "regulation": "GDPR|HIPAA|PCI-DSS",
         "specific_article": "Article or Requirement number",
         "violation_description": "How this risk violates the regulation",
         "potential_penalty": "Fine range or consequence"
       }
     ],
     "remediation_playbook": [
       {
         "step_id": "REM-001",
         "risk_id": "APR-001",
         "action": "What needs to be done",
         "implementation": "Step-by-step instructions",
         "priority": "Immediate|Short-term|Medium-term",
         "assigned_to": "Security Team|DBA|IT Admin|Compliance Officer",
         "requires_approval": true or false,
         "approver": "Security Director|Manager|DBA",
         "estimated_hours": number,
         "regulation_reference": "GDPR Art. 32|HIPAA Security Rule|PCI-DSS Req. 3"
       }
     ],
     "approval_queue": [
       {
         "action": "Description of action needing approval",
         "risk_id": "Reference to the risk",
         "approver": "Who needs to approve",
         "urgency": "Immediate|24 hours|7 days",
         "impact": "What happens if not approved"
       }
     ]
   }

   SCORING GUIDELINES:
   - 90-100: Fully compliant, minor improvements possible
   - 70-89: Mostly compliant, some gaps to address
   - 50-69: Significant compliance gaps, action required
   - Below 50: Non-compliant, immediate remediation needed

   IMPORTANT RULES:
   - Every CRITICAL and HIGH risk must have a remediation step
   - PHI exposure without audit logging is always a HIPAA violation
   - PCI data without encryption is always a PCI-DSS violation
   - Intern or contractor access to PHI/PCI without MFA is always flagged for approval
   - Include estimated penalties for regulation violations where applicable
   - Remediation steps must be specific and actionable, not generic advice
   ```

1. Paste the instructions into the **Instructions** box, then select **Save** to store them as version 1 of the agent.

### Task 3: Add Agent Description

1. If a **Description** field is available in the setup pane, add:

   ```
   Maps identified security risks to GDPR, HIPAA, and PCI-DSS regulations. Generates actionable remediation playbooks with step-by-step implementation, priority levels, and human approval requirements. Returns structured JSON with compliance scores and violation details.
   ```

### Task 4: Connect Compliance Advisor to Classification Agent using A2A

Just like the Risk Detection agent in Challenge 3, you connect the Compliance Advisor agent with **A2A** by re-running `setup_a2a.py`. Now that all three agents exist, the script wires the full pipeline: it enables incoming A2A on **both** sub-agents, creates a RemoteA2A connection for each, and rebuilds the Classification agent with **two** A2A tools.

1. Return to the **Visual Studio Code** terminal you used in Challenge 3 (the `.env` file already has `COMPLIANCE_AGENT_NAME=Compliance-Advisor-Agent`).

1. Run the wiring script again:

   ```bash
   python setup_a2a.py
   ```

   This time both sub-agents are found. Expected output:

   ```text
   Step 1/3: Enable incoming A2A on the available sub-agents
     [ok] Incoming A2A enabled on 'Risk-Detection-Agent'
     [ok] Incoming A2A enabled on 'Compliance-Advisor-Agent'
   Step 2/3: Create RemoteA2A connections
     [ok] Connection 'risk-a2a' -> Risk-Detection-Agent
     [ok] Connection 'compliance-a2a' -> Compliance-Advisor-Agent
   Step 3/3: Attach A2A tools to the Classification agent
     [ok] 'Data-Classification-Agent' updated with 2 A2A tool(s) (new version: 3)
   A2A pipeline wired successfully.
   ```

1. The Classification agent now delegates to **both** sub-agents via A2A: after classifying, it calls Risk Detection, then Compliance Advisor, and returns all three results.

### Task 5: Test the Complete Three-Agent Pipeline

You can test the full pipeline from the **Data-Classification-Agent** playground in the portal (the Streamlit dashboard in Challenge 5 drives the same flow).

1. Go to **Data-Classification-Agent** and open it in the **Agents playground**.

1. Send this comprehensive scan request:

   ```
   Perform a complete security scan on the following data:

   DATABASE SCHEMA:
   Database: RetailDB, Table: Customers, Total Rows: 48500
   Columns: CustomerID (INT), FirstName (VARCHAR), LastName (VARCHAR), SSN (VARCHAR), Email (VARCHAR), Phone (VARCHAR), CreditCardNumber (VARCHAR), CVV (VARCHAR), CardExpiry (VARCHAR), DateOfBirth (DATE), AccountStatus (VARCHAR), Notes (TEXT)

   Sample Data:
   1. CustomerID: 1001, SSN: 123-45-6789, CreditCardNumber: 4532-1234-5678-9012, CVV: 847, Notes: "Customer mentioned SSN issue with account 987-65-4321"
   2. CustomerID: 1002, SSN: 234-56-7890, CreditCardNumber: 5412-7534-9821-0063, CVV: 312

   ACCESS POLICIES:
   Role: Intern | Tables: Customers, FinancialTransactions | Permissions: SELECT * | Masking: None | MFA: No | Audit: No
   Role: Data Analyst | Tables: ALL | Permissions: SELECT * | Masking: None | MFA: No | Audit: No | Last Review: 2024-08-10

   ACCESS LOGS:
   2025-06-15 02:47:00 | jake.morrison (Intern) | SELECT FirstName, LastName, SSN, CreditCardNumber, CVV FROM Customers | 48500 rows | IP: 10.0.1.45 | Status: Success
   2025-06-15 03:12:00 | wei.zhang (Intern) | SELECT * FROM FinancialTransactions | 125000 rows | IP: 103.45.67.89 | Status: Success
   ```

1. Observe the three-agent flow (the Classification agent invokes the two A2A sub-agents as tool calls):
   - **Agent 1 (Classification)**: Classifies all columns (SSN → PII, CreditCardNumber → PCI, CVV → PCI, etc.)
   - **Agent 2 (Risk Detection, via A2A)**: Flags intern access, after-hours bulk exports, foreign IP, missing MFA/audit
   - **Agent 3 (Compliance Advisor, via A2A)**: Maps to GDPR/PCI-DSS, generates remediation steps, creates approval queue

1. Verify that the final response includes results from ALL THREE stages.

### Task 6: Create Logic App

1. In the **Azure Portal**, search for **Logic Apps** and select it.

1. Click on **+ Create**.

1. Configure the Logic App:

   - **Plan type**: Select **Consumption**
   - **Subscription**: Select the available **Azure subscription**
   - **Resource Group**: Select **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**
   - **Logic App name**: **security-alert-processor-<inject key="DeploymentID" enableCopy="false"/>**
   - **Region**: Keep **Default**

1. Click **Review + Create**, then **Create**.

1. Wait for the deployment to complete and click **Go to resource**.

### Task 7: Configure Logic App - Event Grid Trigger

1. In the Logic App, click on **Logic app designer** from the left navigation under **Development Tools**.

1. In the designer, under **Start with a common trigger**, select **When an Event Grid resource event occurs**.

   > **Note:** If you do not see this option, click **+ Add a trigger** and search for **Event Grid**.

1. If prompted to sign in, click **Sign in** and authenticate with your lab credentials:
   - Email: **<inject key="AzureAdUserEmail"></inject>**
   - Password: **<inject key="AzureAdUserPassword"></inject>**

1. Configure the Event Grid trigger:

   - **Subscription**: Select your Azure subscription
   - **Resource Type**: Select **Microsoft.EventGrid.Topics**
   - **Resource Name**: Select **security-alerts-topic-<inject key="DeploymentID" enableCopy="false"/>**
   - **Event Type Item**: Leave as default (all events)

1. Click **+ New step** to add the next action.

### Task 8: Configure Logic App - Parse Event Data

1. Search for **Parse JSON** action and select it.

1. In the **Content** field, click the dynamic content panel. Under **When a resource event occurs**, select **Event data** (not Body).

   > **Important:** The Event Grid trigger already decomposes the event envelope into separate fields (Event data, Event Type, Subject, etc.). The **Event data** field contains the custom data payload where severity lives. Do NOT select Body - that would give you the full event envelope and the nested fields would not be directly accessible.

1. In the **Schema** field, click **Use sample payload to generate schema** and paste the following sample payload:

   ```json
   {
     "alert_id": "ALERT-001",
     "severity": "CRITICAL",
     "risk_id": "ACT-001",
     "description": "Intern bulk-exported 48500 rows of PII/PCI data at 2:47 AM",
     "user": "jake.morrison",
     "role": "Intern",
     "affected_data": ["SSN", "CreditCardNumber", "CVV"],
     "timestamp": "2025-06-15T02:47:00Z",
     "requires_approval": true,
     "scan_id": "scan-20250615-001"
   }
   ```

   > **Note:** This is just the `data` portion of the Event Grid event - not the full event object. Since the trigger already extracts Event data for you, you only need to parse the inner payload.

1. Click **Done** to generate the schema. You should see fields like `severity`, `alert_id`, `description`, `user`, `role`, etc. in the generated schema.

### Task 9: Configure Logic App - Condition, Cosmos DB Actions, and Email Notification

1. Click **+ New step**. Search for and select **Condition** (under Control).

1. In the Condition, configure:

   - Click the left value field, select **Body severity** from the Parse JSON dynamic content
   - Set the operator to **is equal to**
   - Set the right value to **CRITICAL**

   > **Important:** The email notification is triggered **only** when the alert severity is **CRITICAL**. If the agent classifies risks as HIGH or MEDIUM instead of CRITICAL, no email will be sent. If you want to test the full email flow regardless of severity, change the condition from **is equal to** `CRITICAL` to **is not equal to** `CRITICAL`, so the email triggers for any severity. Remember to revert this change after testing.
   >
   > **Note:** The validation for this challenge will work without the email being sent, so don't worry if the email doesn't trigger - it's not a blocker.

1. In the **If true** branch (CRITICAL alerts), click the **+** icon and select **Add an action**.

1. Search for **Azure Cosmos DB** and select **Create or update document (V3)**.

1. If prompted, create a new connection:

   - **Connection Name**: Enter `SecurityCosmosDB`
   - **Authentication Type**: Select **Access Key**
   - **Account ID**: Enter your Cosmos DB account name: **security-agent-cosmos-<inject key="DeploymentID" enableCopy="false"/>**
   - **Access Key to your Azure Cosmos DB account**: Paste the **PRIMARY KEY** you saved from Challenge 1 (not the connection string - use the key only)
   - Click **Create**.

   > **Troubleshooting:** If you get a **Forbidden** error about the request being blocked by firewall settings, go to your Cosmos DB account → **Networking** → set **Public network access** to **All networks** → click **Save**. Wait 1-2 minutes, then retry creating the connection.

1. Configure the Cosmos DB action:

   - **Database ID**: Click the dropdown and select **SecurityAgentDB**
   - **Collection ID**: Click the dropdown and select **SecurityAlerts**

      > **Note:** The Logic App UI uses the older Cosmos DB terminology "Collection ID" - this is the same as "Container ID".

   - **Document**: Paste the following JSON:

     ```json
     {
       "id": "@{guid()}",
       "alertId": "@{body('Parse_JSON')?['alert_id']}",
       "severity": "@{body('Parse_JSON')?['severity']}",
       "description": "@{body('Parse_JSON')?['description']}",
       "user": "@{body('Parse_JSON')?['user']}",
       "role": "@{body('Parse_JSON')?['role']}",
       "timestamp": "@{body('Parse_JSON')?['timestamp']}",
       "scanId": "@{body('Parse_JSON')?['scan_id']}",
       "status": "OPEN",
       "processedAt": "@{utcNow()}"
     }
     ```

   > **Note:** You do not need to set a Partition Key Value. The V3 connector automatically derives it from the document's `severity` field, which matches the container's partition key path (`/severity`).

   > **Note:** If you see a multi-line text box for the Document field, click **Switch to input text format** to enter the JSON directly. You can also use the **Code view** tab at the top to paste the JSON directly.

1. After the Cosmos DB action in the **If true** branch, click the **+** icon and select **Add an action**.

1. Search for **Office 365 Outlook** and select the **Send an email (V2)** action.

1. If prompted to sign in, click **Sign in** and authenticate with your lab credentials:
   - Email: **<inject key="AzureAdUserEmail"></inject>**
   - Password: **<inject key="AzureAdUserPassword"></inject>**

1. Configure the email action:

   - **To**: **<inject key="AzureAdUserEmail"></inject>**
   - **Subject**: Click in the field, then use the dynamic content panel to build the subject:

     Type: `CRITICAL Security Alert - ` then select **risk_id** from the Parse JSON dynamic content.

     The full subject should look like: `CRITICAL Security Alert - @{body('Parse_JSON')?['risk_id']}`

   - **Body**: Switch to **Code View** by clicking the `</>` icon in the body field toolbar, then paste the following HTML:

     ```html
     <html>
     <body style="font-family: Arial, sans-serif; padding: 20px;">
       <div style="background-color: #DC2626; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
         <h2 style="margin: 0;">CRITICAL Security Alert</h2>
         <p style="margin: 5px 0 0;">Data Security & Compliance Agent</p>
       </div>

       <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold; width: 150px;">Alert ID</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['alert_id']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">Severity</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB; color: #DC2626; font-weight: bold;">@{body('Parse_JSON')?['severity']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">Description</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['description']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">User</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['user']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">Role</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['role']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">Timestamp</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['timestamp']}</td>
         </tr>
         <tr>
           <td style="padding: 10px; border: 1px solid #E5E7EB; background-color: #F9FAFB; font-weight: bold;">Requires Approval</td>
           <td style="padding: 10px; border: 1px solid #E5E7EB;">@{body('Parse_JSON')?['requires_approval']}</td>
         </tr>
       </table>

       <div style="background-color: #FEF2F2; border-left: 4px solid #DC2626; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
         <h3 style="margin: 0 0 10px; color: #991B1B;">Immediate Action Required</h3>
         <p style="margin: 0; color: #374151;">This alert requires immediate attention from the Security team. Please log into the Data Security Dashboard to review the full scan results and take appropriate remediation actions.</p>
       </div>

       <p style="color: #6B7280; font-size: 12px;">This is an automated notification from the AI-Powered Data Security & Compliance Agent. Scan ID: @{body('Parse_JSON')?['scan_id']}</p>
     </body>
     </html>
     ```

1. In the **If false** branch (for non-CRITICAL alerts), click the **+** icon and select **Add an action**.

1. Search for **Azure Cosmos DB** and select **Create or update document (V3)** again.

1. Use the same connection and configure:

   - **Database ID**: Select **SecurityAgentDB**
   - **Collection ID**: Select **SecurityAlerts**
   - **Document**: Paste the same JSON as the If true branch:

     ```json
     {
       "id": "@{guid()}",
       "alertId": "@{body('Parse_JSON')?['alert_id']}",
       "severity": "@{body('Parse_JSON')?['severity']}",
       "description": "@{body('Parse_JSON')?['description']}",
       "user": "@{body('Parse_JSON')?['user']}",
       "role": "@{body('Parse_JSON')?['role']}",
       "timestamp": "@{body('Parse_JSON')?['timestamp']}",
       "scanId": "@{body('Parse_JSON')?['scan_id']}",
       "status": "OPEN",
       "processedAt": "@{utcNow()}"
     }
     ```

   > **Note:** As with the If true branch, you do not need to set a Partition Key Value - the connector derives it automatically from the `severity` field in the document.

1. Click **Save** at the top of the Logic App designer to save the workflow.

   Your Logic App designer should now look like this:
   - **When a resource event occurs** (Event Grid trigger)
   - **Parse JSON**
   - **Condition** (severity is equal to CRITICAL)
     - **True**: Create or update document (V3) → Send an email (V2)
     - **False**: Create or update document (V3) 1

<validation step="cbc8d2d7-71d5-4813-8b32-a17a26e1125f" />

> **Congratulations** on completing the task! Now, it's time to validate it. Here are the steps:
> - Hit the Validate button for the corresponding task. If you receive a success message, you can proceed to the next task.
> - If not, carefully read the error message and retry the step, following the instructions in the lab guide.
> - If you need any assistance, please contact us at cloudlabs-support@spektrasystems.com. We are available 24/7 to help.

## Success Criteria

- Compliance Advisor Agent created as a prompt agent with correct model deployment
- Agent maps risks to specific GDPR, HIPAA, and PCI-DSS articles/requirements
- Agent generates actionable remediation playbooks with priorities and owners
- Agent correctly identifies actions requiring human approval
- Compliance Advisor Agent connected to Classification Agent via **A2A** (`setup_a2a.py` wired both sub-agents)
- Complete three-agent pipeline tested: Classification → Risk Detection → Compliance Advisory
- All results from three agents flow through automatically
- Healthcare scenario correctly triggers HIPAA-specific remediations
- Low-risk scenario returns high compliance scores
- Logic App created and configured with Event Grid trigger, Cosmos DB actions, and email notification for CRITICAL alerts
- Logic App designer matches the expected flow: Event Grid → Parse JSON → Condition → True (Cosmos DB + Email) / False (Cosmos DB)

## Additional Resources

- [GDPR Official Text](https://gdpr-info.eu/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [PCI DSS v4.0 Summary](https://www.pcisecuritystandards.org/document_library/)
- [Azure Compliance Offerings](https://learn.microsoft.com/azure/compliance/)
- [Azure Logic Apps](https://learn.microsoft.com/azure/logic-apps/)
- [Office 365 Outlook Connector - Logic Apps](https://learn.microsoft.com/azure/connectors/connectors-create-api-office365-outlook)

Now, click **Next** to continue to **Challenge 05**.

![](media/page_no_6.png)