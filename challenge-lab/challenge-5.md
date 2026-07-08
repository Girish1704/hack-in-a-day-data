# Challenge 05: Run the Dashboard and Test End-to-End

## Overview

Your three-agent pipeline is operational and the Logic App is configured to process security alerts. All the application code has been built for you. In this final challenge, you will download and configure the Streamlit web dashboard, run it locally, and perform end-to-end testing of the complete Data Security Agent system.

## Prerequisites

- Completed Challenge 4 (all three prompt agents created and wired via A2A with `setup_a2a.py`, Logic App configured)
- Event Grid Topic created in Challenge 1
- Cosmos DB and Storage Account configured with sample data
- Logic App created with Event Grid trigger, Cosmos DB actions, and email notification for CRITICAL alerts

## Challenge Objectives

- Download and configure the Streamlit application
- Authenticate with Azure CLI
- Run the dashboard and test the multi-agent pipeline
- Verify end-to-end flow: Scan → Classification → Risk Detection → Compliance → Alerts
- Verify Logic App processes Event Grid alerts and sends email for CRITICAL alerts

## Steps to Complete

### Task 1: Download and Extract Code Files

The application code is provided in a pre-built package.

1. On your lab VM, open a terminal PowerShell.

1. Create a working directory:

   ```powershell
   mkdir C:\Code
   ```

1. **Download the code package**:

   Access the link below using your browser:

   ```
   https://github.com/CloudLabsAI-Azure/hack-in-a-day-data/archive/refs/heads/security-&-compliance-agent.zip
   ```

1. **Extract the ZIP file**:

   - Right-click on the downloaded `ai-powered-data-security.zip` file
   - Select the **Extract All...** option
   - Choose a location: `C:\Code`
   - Click on **Extract**

### Task 2: Authenticate with Azure CLI

The application uses Azure CLI authentication to connect to your agents.

1. From the **Desktop**, open **Visual Studio Code**.

1. In **Visual Studio Code**, select **File** > **Open Folder**.

1. Browse to **C:\Code**, open the **hack-in-a-day-data-ai-powered-data-security** folder, select the **codefiles** folder, and then choose **Select Folder**.

1. In the **Trust the authors of the files in this folder?** pop-up, select **Yes, I trust the authors**.

1. Select **Terminal** from the top menu, and then choose **New Terminal**.

1. In the opened terminal, log in to Azure by running the following command:

   ```bash
   az login
   ```

   > **Note:** This will open a browser pop-up for authentication; minimize Visual Studio Code to view the sign-in window.

1. On the **Sign in** page, select **Work or school account**, and then click **Continue**.

1. On the **Sign into Microsoft Azure** page, enter the below provided email and password to login.

   - Email/Username: **<inject key="AzureAdUserEmail"></inject>**
   - Password: **<inject key="AzureAdUserPassword"></inject>**

1. In the **Stay signed in to all your apps?** window, select **No, sign in to this app only**.

1. Return to **Visual Studio Code**, enter **1** to select the subscription, and then press **Enter**.

### Task 3: Get Your Agent Credentials

You need the following values to connect to your agents:

1. Open **Notepad** and keep it ready to paste the required values.

1. Go to **Microsoft Foundry** and open the project that you created in Challenge 1.

1. In the Overview section, find the **Microsoft Foundry project endpoint** which would look like:

   - Example: `https://data-security-XXXXXXX.services.ai.azure.com/api/projects/proj-default`
   - **Important:** The project name at the end is always `proj-default` (not data-security-XXXX)
   - Make sure it ends with `/api/projects/proj-default`

1. Go to the **Build** section and select **Agents** in the left pane.

1. Click on your **Data-Classification-Agent**.

1. Open the agent in the **Agents playground** and note the **Agent name** (`Data-Classification-Agent`). In the new Foundry, agents are referenced by **name** - there is no `asst_` ID to copy. This is the value you set as `AGENT_NAME`.

1. From Challenge 1, retrieve your **Cosmos DB** connection details:
   - Go to Azure Portal → Your Cosmos DB account
   - Click **Keys** → Copy **URI** and **Primary Key**

1. From Challenge 1, retrieve your **Storage Account** details:
   - Go to Azure Portal → Your Storage Account
   - Click **Access keys** → Copy **Storage account name** and **Key**

1. From Challenge 1, retrieve your **Event Grid** details:
   - Go to Azure Portal → Your Event Grid Topic
   - Click **Access keys** → Copy **Topic Endpoint** and **Key 1**

### Task 4: Configure the Application

1. Navigate back to **Visual Studio Code**.

1. If you already created and filled in the **.env** file while running `setup_a2a.py` in Challenges 3-4, it is ready to use - just confirm `PROJECT_ENDPOINT`, `AGENT_NAME`, and the Cosmos DB / Storage / Event Grid values are set.

1. Otherwise, rename the **.env.example** file to **.env**, then replace each placeholder with the actual values you copied. Save the file.

   > **Important:** The A2A wiring (`python setup_a2a.py`) must have been run in Challenges 3-4 so the Classification agent delegates to the Risk Detection and Compliance Advisor agents. If you skipped it, run it now before starting the app.

### Task 5: Review the Code

Before running the application, explore the code structure:

**app.py** - Main Streamlit application
- **Lines 1-30**: Imports, page config, and environment variable loading
- **Lines 32-220**: Custom CSS styling (gradient header, animations, severity badges, metric cards, dark sidebar)
- **Lines 225-405**: Cosmos DB, Event Grid, and Storage Account helper functions
- **Lines 407-799**: Response parsing for classification, risk detection, and compliance results
- **Lines 801-895**: Agent API calling with `AIProjectClient` + the Responses API (`get_openai_client()`) and DefaultAzureCredential
- **Lines 895-988**: Scan prompt builder (constructs the full data payload for the agent)
- **Lines 989-1150**: Streamlit UI with 6 tabs (Scan, Classification, Risk Detection, Remediation, Alerts, History)

**Helper modules:**
- **setup_a2a.py** - One-time A2A pipeline wiring (Classification → Risk → Compliance)
- **cosmos_helper.py** - Cosmos DB operations (save scan results, save alerts, query history)
- **storage_helper.py** - Azure Blob Storage operations (read schemas, policies, logs)
- **event_grid_helper.py** - Event Grid publishing (CRITICAL and HIGH risk alerts)

**Key features:**
- Microsoft Foundry Responses API (`azure-ai-projects` 2.x), agent referenced by name
- A2A agent-to-agent delegation to the Risk Detection and Compliance Advisor sub-agents
- Azure CLI authentication using DefaultAzureCredential
- Fast Scan (top 5 rows) and Full Scan (all rows) modes
- Real-time progress tracking with status indicators
- Gradient header and severity-coded badges
- Connection status dots in the sidebar
- Automatic Event Grid publishing for critical/high risks
- Cosmos DB persistence for scan history and alerts
- Six-tab dashboard interface

### Task 6: Install Dependencies

1. In the terminal, run:

   ```bash
   pip install -r requirements.txt
   ```

1. This installs:

   - `streamlit` - Web framework
   - `azure-ai-projects` (2.x) - Microsoft Foundry SDK (new Foundry projects API)
   - `openai` - OpenAI client used via the Responses API
   - `azure-identity` - Azure authentication
   - `azure-cosmos` - Cosmos DB SDK
   - `azure-storage-blob` - Blob Storage SDK
   - `azure-eventgrid` - Event Grid SDK
   - `python-dotenv` - Environment variables
   - `requests` - used by `setup_a2a.py`
   - `pandas` - Data processing

### Task 7: Run the Application

1. Start the Streamlit app:

   **Windows PowerShell:**

   ```powershell
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

   streamlit run app.py
   ```

1. Enter the email as **<inject key="AzureAdUserEmail"></inject>** and press Enter.

1. The application will automatically open in your browser at `http://localhost:8501` or `http://localhost:8502`.

### Task 8: Test the Security Scan Pipeline

1. You will see a gradient header: **"Data Security & Compliance Agent"**.

1. Set the **Scan Mode** to **Fast Scan** (reads top 5 rows per table for faster results).

1. Navigate to the **Scan Data Assets** tab.

1. Click the **Run Security Scan** button.

1. After completion, a completion banner appears and the results populate across tabs.

1. Explore and review the Results.

### Task 9: Verify Event Grid and Logic App Flow

> **Important:** The email notification is triggered **only** when the alert severity is **CRITICAL**. If the scan didn't produce any CRITICAL risks, the Logic App will still run (processing the Event Grid event and writing to Cosmos DB), but the email won't be sent because the condition checks for CRITICAL severity.
>
> If you want to test the full email flow, go to your Logic App in the Azure Portal, open the **Logic App Designer**, find the **Condition** step, and change the condition from **is equal to** `CRITICAL` to **is not equal to** `CRITICAL`. This way, the email will trigger for any severity level.
>
> **Note:** The validation for this challenge will work without the email being sent, so don't worry if the email doesn't trigger, it's not a blocker.

1. Go to the **Azure Portal** and navigate to your Logic App: **security-alert-processor-<inject key="DeploymentID" enableCopy="false"/>**.

1. Click on **Overview** and check the **Runs history** section.

1. You should see one or more successful runs triggered by the Event Grid alerts from your scans.

1. Click on a run to see the execution details:
   - Event Grid trigger fired
   - JSON parsed
   - Condition evaluated (CRITICAL or not)
   - Document created in Cosmos DB

1. Navigate to **Cosmos DB** → **Data Explorer** → **SecurityAgentDB** → **SecurityAlerts**.

1. Verify that alert documents were created by the Logic App with the correct severity, description, and status.

<validation step="b44097cf-4404-4fa5-8816-9b882ac7ee2d" />

> **Congratulations** on completing the task! Now, it's time to validate it. Here are the steps:
> - Hit the Validate button for the corresponding task. If you receive a success message, you can proceed to the next task.
> - If not, carefully read the error message and retry the step, following the instructions in the lab guide.
> - If you need any assistance, please contact us at cloudlabs-support@spektrasystems.com. We are available 24/7 to help.

## Congratulations! You have successfully:

- Built a 3-agent AI system in Microsoft Foundry (Classification → Risk Detection → Compliance Advisory)
- Connected agents in a pipeline with automatic hand-off using **A2A (Agent-to-Agent)**
- Created an Event Grid Topic for event-driven alerts
- Configured a Logic App to process security alerts, write to Cosmos DB, and send email for CRITICAL alerts
- Deployed sample datasets to Azure Blob Storage
- Run a Streamlit web dashboard with 6 interactive tabs
- Performed end-to-end security scans with Fast and Full scan modes
- Verified the complete flow from data scan to alert processing and email notification

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Azure Logic Apps](https://learn.microsoft.com/azure/logic-apps/)
- [Azure Event Grid](https://learn.microsoft.com/azure/event-grid/)
- [Microsoft Foundry SDKs](https://learn.microsoft.com/azure/foundry/how-to/develop/sdk-overview)
- [Use the Responses API](https://learn.microsoft.com/azure/foundry/agents/quickstarts/responses-api)

Congratulations! You have completed all challenges. Your AI-Powered Data Security & Compliance Agent system is fully operational with automated alert processing and email notifications.
