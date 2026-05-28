# Article CMS – Windows Setup & Azure Deployment Guide

## Project Structure

```
cms_project/
├── application.py          ← Flask entry point
├── config.py               ← All configuration / env vars
├── requirements.txt        ← Python dependencies
├── writeup.md              ← Required project write-up
├── cms_app.log             ← Auto-created on first run (login logs)
├── app/
│   ├── __init__.py         ← App factory + logging setup
│   ├── models.py           ← SQL helpers (CRUD)
│   ├── views.py            ← All routes + OAuth2
│   └── templates/
│       ├── base.html       ← Shared layout (Bootstrap 5)
│       ├── login.html      ← Login + Microsoft sign-in button
│       ├── index.html      ← Article listing with edit/delete
│       ├── create.html     ← Create article form
│       └── edit.html       ← Edit article form
└── sql_scripts/
    ├── users.sql           ← Run FIRST in Azure SQL
    └── articles.sql        ← Run SECOND in Azure SQL
```

---

## Step 1 – Prerequisites (Windows)

### 1.1 Install Python 3.10
Download from https://www.python.org/downloads/ and check **"Add Python to PATH"** during install.

Verify:
```cmd
python --version
```

### 1.2 Install Microsoft ODBC Driver 17 for SQL Server
Download the Windows installer from:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

Choose **x64** for 64-bit Windows. Run the installer, accept defaults.

Verify it is installed (look for "ODBC Driver 17 for SQL Server" in the list):
```cmd
odbcad32
```

### 1.3 Install Git
Download from https://git-scm.com/download/win

---

## Step 2 – Local Setup

### 2.1 Create & activate a virtual environment
```cmd
cd cms_project
python -m venv venv
venv\Scripts\activate
```

Your prompt will show `(venv)` when active.

### 2.2 Install dependencies
```cmd
pip install -r requirements.txt
```

### 2.3 Set environment variables (for local dev)
Local development uses SQLite by default, so you can run the app and test `admin` / `pass` without connecting to Azure SQL.

Optional: create a file called `.env.bat` in the project root:
```bat
@echo off
set SECRET_KEY=dev-secret-key-change-me
set DATABASE_BACKEND=sqlite
set SQLITE_DATABASE=cms_local.db
set IMAGE_UPLOAD_BACKEND=local
```

Run it before starting the app:
```cmd
.env.bat
```

### 2.4 Run the app locally
```cmd
python application.py
```
Open http://localhost:5000 in your browser.
Login: `admin` / `pass`

---

## Step 3 – Azure Setup

### 3.1 Resource Group
- Name: `cms`
- Region: East US

### 3.2 Azure SQL Database
1. Create a SQL Server: `cms.database.windows.net`
2. Create a database: `cms` (DTU Basic)
3. In **Networking**, select Public Endpoint and set both firewall rules to **Yes**
4. Open **Query Editor** in the Azure Portal
5. Run `sql_scripts/users.sql` first, then `sql_scripts/articles.sql`
6. **Take a screenshot** of both tables in the Query Editor for your submission

### 3.3 Azure Blob Storage
1. Create a Storage Account named `images11`
2. Enable "Allow anonymous access on individual containers"
3. Access tier: Cool
4. Create a container named `images`, set access level to **Container** (public)
5. Note down the Blob connection string from **Security + Networking → Access keys**
6. **Take a screenshot** of the storage account properties page for submission

### 3.4 Azure App Service
1. Create a Web App:
   - Name: `udacitycms` (or any unique name)
   - Runtime: Python 3.10
   - Plan: Free F1
2. Go to **Settings -> Environment Variables** and add these production settings:
   - `DATABASE_BACKEND=sqlserver`
   - `SQL_SERVER=<your-server-name>.database.windows.net`
   - `SQL_DATABASE=<your-database-name>`
   - `SQL_USER_NAME=<your-sql-admin-user>`
   - `SQL_PASSWORD=<your-sql-admin-password>`
   - `SQL_DRIVER=ODBC Driver 17 for SQL Server`
   - `SQL_TRUST_SERVER_CERTIFICATE=no`
   - `IMAGE_UPLOAD_BACKEND=blob`
   - `BLOB_ACCOUNT=<your-storage-account>`
   - `BLOB_CONTAINER=images`
   - `BLOB_STORAGE_KEY=<your-storage-key>`
   - `BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=<your-storage-account>;AccountKey=<your-storage-key>;EndpointSuffix=core.windows.net`
   - `CLIENT_ID=<your-entra-app-client-id>`
   - `CLIENT_SECRET=<your-entra-client-secret>`
3. Go to **Deployment Center**:
   - Source: GitHub
   - Select your repo and branch

### 3.5 Microsoft Entra ID (OAuth2)
1. Go to **Microsoft Entra ID → App Registrations → cmsEntraID**
2. Click **Authentication → Add a Platform → Web**
3. Redirect URI: `https://udacitycms.azurewebsites.net/getAToken`
4. Logout URL: `https://udacitycms.azurewebsites.net/login`

---

## Step 4 – Logging & Screenshots for Submission

The app automatically logs to **two places**:
1. **Console** (visible in App Service Log Stream or local terminal)
2. **`cms_app.log`** file in the project root

Log format:
```
2024-01-15 10:23:11 INFO app.views : Successful login: admin
2024-01-15 10:23:45 WARNING app.views : Failed login attempt for username: hacker
```

To view logs in Azure App Service:
- Go to **Monitoring → Log Stream** in the Azure Portal
- Or download from **Monitoring → App Service Logs**
---

## Troubleshooting (Windows)

| Problem | Fix |
|---|---|
| `pyodbc` install fails | Run `pip install pyodbc` as Administrator, or install Visual C++ Build Tools |
| ODBC Driver not found | Re-install Microsoft ODBC Driver 17 from the link above, restart PC |
| `pip` not found | Re-install Python with "Add to PATH" checked |
| App won't start | Check `.env.bat` was run in the same terminal window |
| Azure SQL connection refused | Check firewall rules in Azure SQL → Networking (your IP must be whitelisted) |
