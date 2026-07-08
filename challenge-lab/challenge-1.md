# Challenge 01: Set Up Azure Infrastructure

## Introduction

Before building the AI-powered Data Security Agent, you need to provision the necessary Azure infrastructure. This challenge involves creating a Microsoft Foundry project with GPT model deployment, Cosmos DB for storing scan results and security alerts, a Storage Account for hosting data assets, and an Event Grid Topic for event-driven alerting.

## Challenge Objectives

- Set up a Microsoft Foundry project with GPT model deployment
- Provision Cosmos DB with the SecurityAgentDB database and containers
- Create a Storage Account with blob containers for data assets
- Upload sample datasets to the Storage Account
- Create an Event Grid Topic for publishing security alerts
- Verify all resources are properly configured and accessible

## Steps to Complete

### Task 1: Verify Pre-Deployed Resource Group

1. In the **Azure Portal**, search for **Resource groups** in the top search bar and select it.

1. You should see a pre-deployed resource group named **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**.

1. Click on **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>** to open it.

1. This resource group will be used for all resources you create in this hackathon.

### Task 2: Create Microsoft Foundry Project with Model Deployment

1. In the **Azure Portal**, search for **Microsoft Foundry** and select it.

1. In the **Use with Foundry** tab, click on **Foundry**.

1. Click **+ Create** to create a new Foundry project.

1. Configure the Microsoft Foundry project:

   - **Subscription**: Select the available **Azure subscription**.
   - **Resource Group**: Select **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**
   - **Project name**: **data-security-<inject key="DeploymentID" enableCopy="false"/>**
   - **Region:** Supported Microsoft Foundry region
   - **Default project name**: Keep it as default
   - Click on **Review + Create**.

1. Click on **Create**.

1. Wait for the deployment to complete (2-3 minutes).

1. Once created, click **Go to resource** in the overview section.

1. In **data-security-<inject key="DeploymentID" enableCopy="false"/>**, select **Access control (IAM)** from the left navigation menu.

1. Select **+ Add**, and then choose **Add role assignment**.

1. In the **Role** tab, search for **Foundry Owner**, select **Foundry Owner** from the results, and then click **Next**.

1. In the **Members** tab, select **+ Select members**, search for **<inject key="AzureAdUserEmail"></inject>**, choose the user from the results, and then again search for `https://odl_user_sp_`<inject key="DeploymentID" enableCopy="false"/> choose the app from the results and click **Select**.

1. Click **Review + assign** to complete the role assignment.

1. In the **Review + assign** tab, click **Review + assign** to confirm the role assignment.

1. Once created, click **Go to Microsoft Foundry portal** in the overview section.

### Task 3: Deploy GPT Model in Microsoft Foundry

1. In the **Microsoft Foundry** portal, select the **Build** section.

1. In the left pane, select **Models**.

1. Search for and select **gpt-5-mini** from the model catalog and click on **Deploy**.

1. Configure the deployment:

   - **Deployment name**: `data-security-model`
   - **Deployment type**: **Global Standard**
   - **Tokens per Minute Rate Limit**: **50K**

      > **Important**: Do not increase the TPM limit beyond 50K to avoid exceeding quota limits and additional costs.

1. Click on **Deploy**.

   > **Note:** If you are unable to deploy gpt-5-mini or the quota shows as zero, try changing the deployment type to Standard. If the issue persists, deploy the gpt-5-mini model instead.

### Task 4: Test the Model Deployment

1. Open the `data-security-model` deployment and select **Open in playground** (the model playground).

1. In the chat box, enter and test with this prompt:

   ```
   What are the key differences between PII, PHI, and PCI data classifications?
   ```

1. Verify you receive a response explaining the data classification categories.

### Task 5: Create Azure Cosmos DB

1. In the **Azure Portal**, search for **Azure Cosmos DB** and select it.

1. Click on **+ Create** button.

1. Click on **Create** for **Azure Cosmos DB for NoSQL**.

1. Configure Cosmos DB:

   - **Workload Type**: Select **Development/Testing**
   - **Subscription**: Select the available **Azure subscription**
   - **Resource Group**: Select **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**
   - **Account Name**: **security-agent-cosmos-<inject key="DeploymentID" enableCopy="false"/>**
   - **Availability Zones**: Select **Disable**
   - **Location**: Keep it **Default**
   - **Capacity mode**: **Serverless**

      > **Note:** If you are unable to create Azure Cosmos DB with the workload type set to **Development/Testing**, select **Production** and try again.

1. Click **Review + Create**, then **Create**.

1. Wait for the deployment to complete (10-15 minutes).

### Task 6: Create Cosmos DB Database and Containers

1. In your Cosmos DB account, click on **Data Explorer** from the left navigation.

   > **Note:** Close all pop-up windows.

1. Click **+ New Container** drop-down. From the drop-down, select **+ New Database**.

1. Configure the database:

   - **Database id**: `SecurityAgentDB`
   - Click **OK**

1. Create the first container for scan results:

   - Right-Click on the **SecurityAgentDB** and click **New Container**
   - **Database id**: Select **Use existing** and choose **SecurityAgentDB**.
   - **Container id**: `ScanResults`
   - **Partition key**: `/scanId`
   - Click **OK**

1. Create a second container for security alerts:

   - Right-Click on the **SecurityAgentDB** and click **New Container** again
   - **Database id**: Select **Use existing** and choose **SecurityAgentDB**.
   - **Container id**: `SecurityAlerts`
   - **Partition key**: `/severity`
   - Click **OK**

1. Verify both containers are visible in Data Explorer under SecurityAgentDB.

1. Navigate to **Networking** in the left menu under **Settings**.

1. Under **Public network access**, select **All networks**.

1. Click **Save** and wait for the update to apply.

   > **Important:** This is required so that the Logic App (created in Challenge 5) can connect to Cosmos DB. If public network access is restricted, the Logic App will be blocked by the firewall.

1. Navigate to **Keys** in the left menu under **Settings** and copy:

   - **URI**
   - **PRIMARY KEY**
   - Save these values in Notepad for later use.

### Task 7: Create Azure Storage Account

1. In the **Azure Portal**, search for **Storage accounts** and select it.

1. Click on **+ Create**.

1. Configure the Storage Account:

   - **Subscription**: Select the available **Azure subscription**
   - **Resource Group**: Select **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**
   - **Storage account name**: **securitydata<inject key="DeploymentID" enableCopy="false"/>**
   - **Region**: Keep **Default**
   - **Performance**: **Standard**
   - **Redundancy**: **Locally-redundant storage (LRS)**

1. Click **Review + Create**, then **Create**.

1. Wait for the deployment to complete.

1. Navigate to the Storage Account and go to **Access keys** under **Security + networking**.

1. Click **Show** next to the first key and copy both:

   - **Storage account name**
   - **Key**
   - Save these values in Notepad for later use.

### Task 8: Create Storage Containers and Upload Sample Data

1. In your Storage Account, click on **Containers** under **Data storage** in the left navigation.

1. Create four blob containers by clicking **+ Container** for each:

   - Container name: `schemas` - Click **Create**
   - Container name: `access-policies` - Click **Create**
   - Container name: `access-logs` - Click **Create**
   - Container name: `remediation-reports` - Click **Create**

1. Upload sample data files to the **schemas** container:

   - Click on the **schemas** container to open it.
   - Click **Upload**.
   - To download the required packages, open the link below in your web browser:

     ```
     https://github.com/CloudLabsAI-Azure/hack-in-a-day-data/archive/refs/heads/security-&-compliance-agent.zip
     ```

   - Extract the ZIP file.
   - Navigate to the `datasets` folder inside the extracted files.
   - Upload these four files:
     - `customer_data.json`
     - `medical_records.json`
     - `financial_transactions.json`
     - `employee_data.json`
   - Click **Upload** to confirm.

1. Upload access policy data to the **access-policies** container:

   - Go back to **Containers** and click on the **access-policies** container.
   - Click **Upload**.
   - From the same extracted `datasets` folder, upload:
     - `access_policies.json`
   - Click **Upload** to confirm.

1. Upload access log data to the **access-logs** container:

   - Go back to **Containers** and click on the **access-logs** container.
   - Click **Upload**.
   - From the same extracted `datasets` folder, upload:
     - `access_logs.csv`
   - Click **Upload** to confirm.

1. Verify all files are uploaded to the correct containers:
   - `schemas` container: 4 JSON files (customer_data, medical_records, financial_transactions, employee_data)
   - `access-policies` container: 1 JSON file (access_policies)
   - `access-logs` container: 1 CSV file (access_logs)
   - `remediation-reports` container: empty (will store output from the pipeline)

### Task 9: Create Event Grid Topic

1. In the **Azure Portal**, search for **Event Grid Topics** and select it.

1. Click on **+ Create**.

1. Configure the Event Grid Topic:

   - **Subscription**: Select the available **Azure subscription**
   - **Resource Group**: Select **challenge-rg-<inject key="DeploymentID" enableCopy="false"/>**
   - **Name**: **security-alerts-topic-<inject key="DeploymentID" enableCopy="false"/>**
   - **Region**: Keep **Default**

1. Click **Review + Create**, then **Create**.

1. Wait for the deployment to complete.

1. Navigate to the Event Grid Topic and go to **Access keys** under **Settings**.

1. Copy:

   - **Topic Endpoint**
   - **Key 1**
   - Save these values in Notepad for later use.

### Task 10: Gather Configuration Values

Create a text file or note with the following values (you will need these in subsequent challenges):

```text
Microsoft Foundry:
- Project Endpoint: https://<your-resource>.services.ai.azure.com/api/projects/proj-default
- Deployment Name: data-security-model
- Agent Name (set in Challenge 2): Data-Classification-Agent
  (In the new Foundry, agents are referenced by NAME, not by an asst_ ID.)

Foundry / A2A wiring (needed by setup_a2a.py in Challenge 3-4):
- Subscription ID: [your-subscription-id]
- Resource Group: challenge-rg-<DeploymentID>
- Foundry Account Name: [the Microsoft Foundry resource/account name]
- Project Name: proj-default

Cosmos DB:
- URI: https://security-agent-cosmos-xxxxx.documents.azure.com:443/
- Primary Key: [your-key]
- Database Name: SecurityAgentDB
- Containers: ScanResults, SecurityAlerts

Storage Account:
- Account Name: securitydataxxxxx
- Account Key: [your-key]
- Containers: schemas, access-policies, access-logs, remediation-reports

Event Grid:
- Topic Endpoint: https://security-alerts-topic-xxxxx.[region].eventgrid.azure.net/api/events
- Key: [your-key]
```

<validation step="e9601c8b-f49e-42ba-8446-3fc630d3f98c" />

> **Congratulations** on completing the task! Now, it's time to validate it. Here are the steps:
> - Hit the Validate button for the corresponding task. If you receive a success message, you can proceed to the next task.
> - If not, carefully read the error message and retry the step, following the instructions in the lab guide.
> - If you need any assistance, please contact us at cloudlabs-support@spektrasystems.com. We are available 24/7 to help.

## Success Criteria

- Microsoft Foundry project created with GPT model deployed and tested
- Cosmos DB account created with SecurityAgentDB database and two containers (ScanResults, SecurityAlerts)
- Storage Account created with four blob containers and sample data uploaded
- Event Grid Topic created and access keys documented
- All connection strings, keys, and endpoints saved for future use
- All resources deployed in the same resource group

## Additional Resources

- [What is Microsoft Foundry?](https://learn.microsoft.com/azure/foundry/what-is-foundry)
- [Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)
- [Azure Event Grid](https://learn.microsoft.com/azure/event-grid/)

Now, click **Next** to continue to **Challenge 02**.

![](media/page_no_3.png)