# Update a Snowflake record from Salesforce using a Python-based OData middleware connected through an External Data Source

This repository contains a Proof of Concept (POC) demonstrating how to view and update data in a Snowflake database directly from the Salesforce user interface in real-time. This is achieved using Salesforce Connect and a lightweight Python web service that acts as an OData middleware.

<img width="991" alt="image" src="https://github.com/user-attachments/assets/20dba72f-4140-4873-b872-12e5ce31640e" />
![Uploading image.png…]()

*(A diagram showing Salesforce -> ngrok -> Python/Flask App -> Snowflake)*

## Architecture
The integration uses four key components:
1.  **Salesforce:** The system of engagement where users view and edit data. It uses Salesforce Connect to treat external data as native "External Objects".
2.  **Snowflake:** The system of record where the actual data resides.
3.  **Python Flask App (`app.py`):** A lightweight web server that acts as a live translator. It receives OData 4.0 requests from Salesforce and translates them into SQL queries for Snowflake, and vice-versa.
4.  **ngrok:** A tunneling service that creates a secure, public URL for our local Python app, making it accessible to the Salesforce cloud platform.

---

## Prerequisites
Before you begin, ensure you have the following:
* A **Salesforce Developer Org**.
* A **Snowflake Account** with permissions to create tables and users.
* **Python** installed on your local machine (preferably via Anaconda or miniconda to manage environments).
* A code editor like **Visual Studio Code**.
* **ngrok** installed and authenticated on your local machine.

---

## Step 1: Snowflake Setup

First, we need to create the table in Snowflake that will store our data.

1.  **Create the Table:** Log in to your Snowflake account, open a worksheet, and run the following SQL to create the `COMMISSION_DATA` table.
    ```sql
    CREATE OR REPLACE TABLE DEMODB.PUBLIC.COMMISSION_DATA (
        OpportunityID   VARCHAR(18) PRIMARY KEY,
        CommissionAmount  NUMBER(10, 2),
        Status            VARCHAR(50),
        Needs_Review_Flag BOOLEAN,
        Review_Reason     VARCHAR(255),
        LastModifiedDate  DATETIME
    );
    ```

2.  **Insert Sample Data:** Run the following `INSERT` statement to populate the table.
    ```sql
    INSERT INTO COMMISSION_DATA (OpportunityID, CommissionAmount, Status, Needs_Review_Flag, Review_Reason, LastModifiedDate)
    VALUES
        ('0068c00001BqV2aAAF', 7500.50, 'Calculated', FALSE, NULL, CURRENT_TIMESTAMP()),
        ('0068c00001BqV3bBCG', 12350.00, 'In Dispute', TRUE, 'Commission percentage seems incorrect.', CURRENT_TIMESTAMP()),
        ('0068c00001BqV4cCDH', 1200.75, 'Pending Payment', FALSE, NULL, CURRENT_TIMESTAMP()),
        ('0068c00001BqV5dDEI', 25000.00, 'In Dispute', TRUE, 'This was a multi-year deal.', CURRENT_TIMESTAMP());
    ```

3.  **Grant Permissions:** Grant the necessary privileges to the role your application will use (e.g., `ACCOUNTADMIN`).
    ```sql
    GRANT SELECT, UPDATE ON TABLE DEMODB.PUBLIC.COMMISSION_DATA TO ROLE ACCOUNTADMIN;
    ```

---

## Step 2: Python Application Setup

Next, set up the local Python project that will serve as the middleware.

1.  **Create Project Directory:** Create a folder for the project (e.g., `OdataPoc`).

2.  **Install Libraries:** In your terminal, install the required Python libraries.
    ```bash
    pip install Flask snowflake-connector-python python-dotenv
    ```

3.  **Create `app.py`:** Inside your project folder, create a file named `app.py` and paste the complete code from the final working version in our conversation.

4.  **Create `.env` File:** In the same folder, create a file named `.env` to store your credentials securely. **Do not commit this file to GitHub.** Populate it with your details.
    ```
    SNOWFLAKE_USER=YourSnowflakeUser
    SNOWFLAKE_PASSWORD=YourSnowflakePassword
    SNOWFLAKE_ACCOUNT=YourFullAccountIdentifier.region.cloud
    SNOWFLAKE_WAREHOUSE=YourComputeWarehouse
    SNOWFLAKE_DATABASE=DEMODB
    SNOWFLAKE_SCHEMA=PUBLIC
    SNOWFLAKE_ROLE=ACCOUNTADMIN
    ```

---

## Step 3: Running the Local Environment

Now, let's start the servers. You will need two separate terminal windows.

1.  **Identify Your Python Environment:** If you encountered environment issues, first find the correct Python path by running `import sys; print(sys.executable)` in a working Jupyter notebook.

2.  **Start the Flask App (Terminal 1):** Launch the web server, making sure to use the correct Python executable path and a port that is not in use (e.g., 7001).
    ```bash
    # Replace the path with your specific Python path
    /path/to/your/python -m flask run --port=7001
    ```

3.  **Start ngrok (Terminal 2):** Create the public tunnel to your running Flask application.
    ```bash
    ngrok http 7001
    ```
    `ngrok` will provide you with a public HTTPS URL (e.g., `https://<random-string>.ngrok-free.app`). Copy this URL.

---

## Step 4: Salesforce Configuration

Finally, configure Salesforce to connect to your running service.

1.  **Create External Data Source:**
    * In Salesforce Setup, go to **External Data Sources** and click **New**.
    * **Type:** `Salesforce Connect: OData 4.0`
    * **URL:** Paste your ngrok URL, making sure it ends with `/odata/`
        * Example: `https://<random-string>.ngrok-free.app/odata/`
    * **Writable External Objects:** ✅ Check this box.
    * Click **Save**.

2.  **Validate and Sync:**
    * On the next screen, click **Validate and Sync**.
    * Salesforce will connect to your service. Check the box next to the `CommissionData` table and click **Sync**.

3.  **Create a Tab:**
    * In Setup, go to **Tabs** and create a new "Custom Object Tab".
    * Select your new `Commission Record` object, choose a tab style, and save it.

---

## How to Use
1.  In Salesforce, navigate to the "Commission Records" tab you just created. You should see the data from your Snowflake table.
2.  Click on a record's ID to view the detail page.
3.  Click **Edit**, change a value (e.g., update the `Status` or check the `Needs Review Flag`), and click **Save**.
4.  Verify the change by refreshing the page in Salesforce and by running a `SELECT` query in your Snowflake worksheet. The data should be updated in both places instantly.
