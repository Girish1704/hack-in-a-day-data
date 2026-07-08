# Challenge 02: Build the Data Classification Agent

## Overview

In this challenge, you will create your first AI agent as a **prompt agent** in Microsoft Foundry Agent Service. The Data Classification Agent is the entry point of the security pipeline. It scans data schemas and sample rows to classify each column as PII, PHI, PCI, Confidential, or Public. You will configure the agent with detailed classification instructions and test it using the playground with sample data from your Storage Account.

> **What changed:** The new Microsoft Foundry uses **prompt agents** that are referenced by their **name** (there is no `asst_...` Agent ID anymore). In Challenges 3-4 you will connect the three agents with **A2A (Agent-to-Agent)** - the successor to the deprecated "Connected agents" feature.

## Challenge Objectives

- Navigate to the Agents section in Microsoft Foundry
- Create the Data Classification prompt agent with a descriptive name
- Configure the agent to use your GPT model deployment
- Write comprehensive instructions for data classification
- Test the agent with customer data and medical records
- Verify classification accuracy and JSON output format

## Steps to Complete

### Task 1: Navigate to the Agents Section

1. Open the **Microsoft Foundry** portal at [https://ai.azure.com](https://ai.azure.com) and select your project: **data-security-<inject key="DeploymentID" enableCopy="false"/>**.

1. From the top navigation, select the **Build** section.

1. In the left pane, select **Agents**.

   > **Note**: If you encounter any errors related to role assignments or permissions, first refresh the browser. If the issue persists, sign out of the portal and sign in again, then retry the operation.

### Task 2: Create the Data Classification Agent

1. Select **New agent**.

1. Enter the agent name `Data-Classification-Agent` and confirm.

   > **Important:** In the new Foundry, an agent's **name is permanent** - you can't rename it after creation, and in code you reference it as `<agent_name>:<version>`. Type it exactly as shown.

1. The agent opens in the **Agents playground**. In the setup pane, select the **Model**: **data-security-model** (the deployment from Challenge 1). Leave **Temperature** and **Top P** at their defaults (1).

1. This is a **prompt agent** - a declaratively defined agent (model + instructions + tools) that Foundry runs for you. You will use its **name** as `AGENT_NAME` in the `.env` file in Challenge 5.

### Task 3: Write Agent Instructions

1. In the **Instructions** text box, copy and paste the following complete instructions:

   ```
   You are a Data Classification Specialist for enterprise security. Your role is to analyze database schemas and sample data to classify every column into one of the following sensitivity categories: PII, PHI, PCI, CONFIDENTIAL, or PUBLIC.

   CLASSIFICATION DEFINITIONS:

   1. PII (Personally Identifiable Information):
      - Social Security Numbers (SSN), Tax IDs
      - Full names when combined with other identifiers
      - Email addresses, phone numbers
      - Physical addresses (street, city, state, zip when combined)
      - Date of birth
      - Driver's license numbers
      - Passport numbers
      - Biometric identifiers
      - IP addresses when linked to individuals
      - Any data that can uniquely identify a person

   2. PHI (Protected Health Information):
      - Medical record numbers, patient IDs
      - Diagnoses, diagnosis codes (ICD-10)
      - Treatment plans, procedures
      - Medications and prescriptions
      - Lab results, test outcomes
      - Insurance IDs, policy numbers
      - Mental health records
      - Substance abuse records
      - Genetic information
      - Any health data linked to an individual

   3. PCI (Payment Card Industry Data):
      - Credit/debit card numbers (full or partial)
      - CVV/CVC security codes
      - Card expiration dates
      - Cardholder name (when with card data)
      - Bank account numbers
      - Routing numbers
      - PIN numbers
      - Transaction authorization codes

   4. CONFIDENTIAL:
      - Salary and compensation data
      - Performance reviews and ratings
      - Disciplinary records
      - Internal risk scores
      - Trade secrets or proprietary data
      - Financial amounts (revenue, profit)
      - Internal notes with sensitive context

   5. PUBLIC:
      - Product names, categories
      - Order status, shipping status
      - Country, region (non-specific location)
      - Timestamps (created_at, updated_at)
      - Auto-generated IDs (not linked to PII)
      - Public-facing descriptions

   ANALYSIS PROCESS:
   1. Examine each column name, data type, and description
   2. Review sample data values for patterns (SSN format XXX-XX-XXXX, card numbers, etc.)
   3. Check for indirect identifiers (combinations that could identify someone)
   4. Consider the context of the table and database
   5. Look for free-text fields that may contain embedded sensitive data

   OUTPUT FORMAT:
   Return your classification as a JSON object with this structure:
   ```json
   {
     "database": "database_name",
     "table": "table_name",
     "total_columns": number,
     "classifications": [
       {
         "column": "column_name",
         "data_type": "column_type",
         "classification": "PII|PHI|PCI|CONFIDENTIAL|PUBLIC",
         "confidence": 0.0 to 1.0,
         "reason": "Brief explanation of why this classification was chosen",
         "regulations": ["GDPR", "HIPAA", "PCI-DSS"],
         "recommended_controls": ["encryption", "masking", "access_restriction", "audit_logging"]
       }
     ],
     "summary": {
       "pii_count": number,
       "phi_count": number,
       "pci_count": number,
       "confidential_count": number,
       "public_count": number,
       "highest_risk_columns": ["column names with highest sensitivity"]
     }
   }
   ```

   IMPORTANT RULES:
   - Classify EVERY column, do not skip any
   - When a column could fall into multiple categories, choose the HIGHEST sensitivity (PHI > PII > PCI > CONFIDENTIAL > PUBLIC)
   - Free-text "Notes" fields should be examined for embedded PII/PHI patterns in sample data
   - Date of birth is PII, not PUBLIC
   - Email and phone are PII even when stored alone
   - Account numbers and routing numbers are PCI
   - Always include the applicable regulations for each classification

1. Paste the instructions into the **Instructions** box of the Agents playground.

### Task 4: Configure Agent Description

1. If a **Description** field is available in the setup pane, add:

   ```
   Analyzes database schemas and sample data to classify every column into sensitivity categories (PII, PHI, PCI, Confidential, Public). Returns structured JSON with confidence scores, applicable regulations, and recommended security controls.
   ```

### Task 5: Save the Agent Version and Note the Name

1. Select **Save** in the Agents playground to store your changes as **version 1** of the agent.

   > **Note:** Prompt-agent changes are saved as immutable **versions**. You can test unsaved edits in the playground, but you must Save to create a version that other tools (and the A2A wiring in Challenges 3-4) can reference. Each Save creates a new version.

1. Confirm the **Agent name** reads exactly `Data-Classification-Agent`.

1. Save this **name** in Notepad - you will use it as `AGENT_NAME` in Challenge 5 for the Streamlit app. (The new Foundry references agents by name, so there is no `asst_` ID to copy.)

<validation step="b9b7e553-3506-41b0-bcc6-6c20678e7729" />

> **Congratulations** on completing the task! Now, it's time to validate it. Here are the steps:
> - Hit the Validate button for the corresponding task. If you receive a success message, you can proceed to the next task.
> - If not, carefully read the error message and retry the step, following the instructions in the lab guide.
> - If you need any assistance, please contact us at cloudlabs-support@spektrasystems.com. We are available 24/7 to help.

## Success Criteria

- Data Classification Agent created with the correct model deployment
- Agent instructions cover all five classification categories (PII, PHI, PCI, Confidential, Public)
- Agent returns structured JSON output with classification, confidence, reasons, and regulations
- Customer data test correctly identifies PII and PCI columns
- Medical records test correctly identifies PHI columns
- Notes fields are classified based on sample data content (not just column name)
- Agent name documented for later use

## Additional Resources

- [GDPR Data Classification](https://learn.microsoft.com/compliance/regulatory/gdpr)
- [HIPAA Protected Health Information](https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html)
- [PCI DSS Requirements](https://www.pcisecuritystandards.org/)
- [Create a prompt agent in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/agents/quickstarts/prompt-agent)

Now, click **Next** to continue to **Challenge 03**.

![](media/page_no_4.png)