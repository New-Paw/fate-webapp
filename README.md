## 1. Project Introduction

FATE WebApp UI is a FastAPI-based web application designed to simplify the use of a standalone FATE federated learning environment through a browser interface.

The application provides a complete workflow for managing datasets, creating training jobs, managing trained models, running prediction tasks, and viewing job status, logs, and results. It is designed for a deployment environment where FATE runs inside a Docker container on a remote server, and the WebApp communicates with that server through SSH.

The main goal of this project is to provide a user-friendly interface for operating FATE without requiring users to manually run every command inside the server or Docker container.

The system supports:

* User registration and login
* Secure password hashing for WebApp accounts
* Encrypted storage of remote server passwords
* Dataset upload and management
* Automatic upload of CSV files to FATE
* Training job creation
* Model record management
* Prediction job creation
* Prediction result viewing and local result download
* Job status, logs, and metrics query
* Deletion of database records, FATE tables, and generated server files

---

## 2. Project Structure

```text
FATE_WEBAPP/
│
├── app/
│   ├── dependencies/
│   │   └── auth.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── app_user.py
│   │   ├── uploaded_file.py
│   │   ├── job_record.py
│   │   ├── model_record.py
│   │   └── prediction_record.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── pages.py
│   │   ├── fate_api.py
│   │   └── file_storage.py
│   │
│   ├── schemas/
│   │   └── fate.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── fate_client.py
│   │   └── remote_fate_service.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── mainpage.html
│   │   ├── datapage.html
│   │   ├── trainingpage.html
│   │   ├── modelpage.html
│   │   └── predictedpage.html
│   │
│   ├── config.py
│   ├── db.py
│   └── main.py
|
├── docker/
│   └── oracle/
│       └── init/
│           └── 01_create_app_user.sql
│
├── scripts/
│   └── seed_admin.py
|
├── logs/
├── uploads/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
├── documentation/
└── README.md
```

---

## 3. Installation

### 3.1 Clone the Repository

```bash
git clone https://github.com/New-Paw/fate-webapp.git
cd fate-webapp
```
---

### 3.2 Create a Python Virtual Environment

On Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure the required database driver is installed. For example, if Oracle is used, the project may require oracledb or a compatible Oracle driver depending on the database configuration.

---

### 3.4 Docker Requirement

This project uses Docker Oracle Database for local testing.

Before running the WebApp, make sure Docker Desktop is installed and running.

Check Docker status:

```bash
docker --version
docker ps
```

The Oracle XE image used by this project is:

```text
container-registry.oracle.com/database/express:21.3.0-xe
```

If the image is not downloaded automatically by Docker Compose, pull it manually:

```bash
docker pull container-registry.oracle.com/database/express:21.3.0-xe
```

If Oracle Container Registry requires authentication, log in first:

```bash
docker login container-registry.oracle.com
```

You may need to accept the Oracle Database Express Edition license on Oracle Container Registry before pulling the image.

---

## 4. Environment Configuration

This project uses a local `.env` file to store configuration and secrets.

The real `.env` file must not be committed to GitHub.  
The repository only provides `.env.example`.

Create your local `.env` file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit .env and fill in your own values.

---

### 4.1 Example `.env` Configuration for Docker Oracle

```env

# ------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------
APP_HOST=127.0.0.1
APP_PORT=8000


# ------------------------------------------------------------
# Docker Oracle Database
# ------------------------------------------------------------
# This password is used by the Oracle Docker container.
ORACLE_PWD=OracleSysPassword123


# ------------------------------------------------------------
# WebApp Database Connection
# ------------------------------------------------------------
# FATE_APP is created by: docker/oracle/init/01_create_app_user.sql
DATABASE_URL=oracle+oracledb://FATE_APP:fate_app_password@127.0.0.1:1521/?service_name=XEPDB1


# ------------------------------------------------------------
# WebApp Authentication
# ------------------------------------------------------------
# Generate APP_SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
APP_SECRET_KEY=replace_with_random_secret_key

# Generate APP_FERNET_KEY: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
APP_FERNET_KEY=replace_with_fernet_key

ACCESS_TOKEN_EXPIRE_MINUTES=720


# ------------------------------------------------------------
# Default Administrator Account for Testing
# ------------------------------------------------------------
# scripts/seed_admin.py will create:
# Account: administrator
# Password: 123456
ADMIN_ACCOUNT=administrator
ADMIN_PASSWORD=123456

# These are the SSH credentials for the remote FATE server.
# ADMIN_SERVER_PASSWORD will be encrypted before being stored in the database.
ADMIN_SERVER_USERNAME=your_remote_fate_server_username
ADMIN_SERVER_PASSWORD=your_remote_fate_server_password


# ------------------------------------------------------------
# Remote FATE Server SSH Configuration
# ------------------------------------------------------------
GRACE_HOST=your_remote_fate_server_host
GRACE_PORT=22

# ------------------------------------------------------------
# FATE Docker / Runtime Configuration
# ------------------------------------------------------------
FATE_CONTAINER=standalone_fate
FATE_ROOT=/data/projects/fate


# ------------------------------------------------------------
# Optional FATE Flow SDK Configuration
# ------------------------------------------------------------
FATE_HOST=127.0.0.1
FATE_PORT=9380
FATE_API_VERSION=v1
```

---

### 4.2 Generate Security Keys

Generate `APP_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Generate `APP_FERNET_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Important:

* `APP_SECRET_KEY` is used to sign JWT access tokens.
* `APP_FERNET_KEY` is used to encrypt and decrypt remote server passwords.
* Run scripts/seed_admin.py only after APP_FERNET_KEY, ADMIN_SERVER_USERNAME, and ADMIN_SERVER_PASSWORD are correctly configured.
* If `APP_FERNET_KEY` is changed after `seed_admin.py` creates the administrator account, the stored remote server password cannot be decrypted.

---

## 5. Docker Oracle Database and Administrator Account

This project uses a Docker-based Oracle XE database for local testing.

The repository does not provide a pre-filled database volume and does not include real remote server passwords. Instead, testers create the database locally with Docker Compose and then run `scripts/seed_admin.py` to create the default administrator account.

Default WebApp login account:

```text
Account: administrator
Password: 123456
```

This account is created by: 

```bash
python scripts/seed_admin.py
```

The script reads the following values from .env:

```env
ADMIN_ACCOUNT=administrator
ADMIN_PASSWORD=123456
ADMIN_SERVER_USERNAME=your_remote_fate_server_username
ADMIN_SERVER_PASSWORD=your_remote_fate_server_password
```

The WebApp login password is stored as a hash.

The remote FATE server password is encrypted using APP_FERNET_KEY before being saved into the Docker Oracle database.

---

### 5.1 Start Docker Oracle Database

Start the Oracle database container:

```bash
docker compose up -d oracle-db
```

Check whether the container is running:

```bash
docker ps
```

The container should show a healthy status:

```text
fate_oracle_xe   Up ... (healthy)
```

View database logs:

```bash
docker logs -f fate_oracle_xe
```

When the following message appears, the database is ready:

```text
DATABASE IS READY TO USE!
```

---

### 5.2 Oracle Database User

The WebApp connects to Oracle using the application database user:

```text
Username: FATE_APP
Password: fate_app_password
Service: XEPDB1
```

This user is created by:

```text
docker/oracle/init/01_create_app_user.sql
```

The corresponding SQLAlchemy database URL is:

```env
DATABASE_URL=oracle+oracledb://FATE_APP:fate_app_password@127.0.0.1:1521/?service_name=XEPDB1
```

---

### 5.3 Create Administrator Account

After Docker Oracle is ready and `.env` is configured, run:

```bash
python scripts/seed_admin.py
```

Expected output:

```text
Initializing database tables...
Checking administrator account: administrator
Creating administrator account...
Administrator account created successfully.
--------------------------------------------
Account : administrator
Password: 123456
--------------------------------------------
Remote server password has been encrypted in database.
```

If the administrator account already exists, the script will not create it again.

---

### 5.4 Testing Procedure

```bash
git clone https://github.com/New-Paw/fate-webapp.git
cd fate-webapp

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then start Oracle:

```bash
docker compose up -d oracle-db
```

Create the default administrator:

```bash
python scripts/seed_admin.py
```

Start the WebApp:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Login with:

```text
Account: administrator
Password: 123456
```

---

## 6. How to Run

### 6.1 Start Docker Oracle Database

From the project root directory:

```bash
docker compose up -d oracle-db
```

Check status:

```bash
docker ps
```

Wait until the Oracle container becomes healthy.

---

### 6.2 Create the Administrator Account

Make sure `.env` has valid values for:

```env
APP_FERNET_KEY=
ADMIN_SERVER_USERNAME=
ADMIN_SERVER_PASSWORD=
GRACE_HOST=
GRACE_PORT=
```

Then run:

```bash
python scripts/seed_admin.py
```

---

### 6.3 Start the Web Application

From the project root directory:

```bash
uvicorn app.main:app --reload
```

Then open the browser:

```text
http://127.0.0.1:8000
```

Login:

```text
Account: administrator
Password: 123456
```

---

### 6.4 First-Time Usage

1. Start Docker Oracle database.
2. Configure `.env`.
3. Run `scripts/seed_admin.py`.
4. Start the WebApp.
5. Login with `administrator / 123456`.
6. Upload datasets, create training jobs, manage models, and run predictions.
---

## 7. Main Features

### 7.1 User Authentication

The application provides registration, login, and logout functionality.

Related files:

```text
app/routers/auth.py
app/dependencies/auth.py
app/services/auth_service.py
app/models/app_user.py
```

Features:

* Register a new user
* Login with account and password
* Store WebApp password as a hash
* Encrypt remote server password
* Store login token in an HTTP-only cookie
* Protect pages and APIs through authentication dependencies

---

### 7.2 Dataset Management

The dataset module allows users to upload CSV files and import them into FATE.

Related files:

```text
app/routers/file_storage.py
app/models/uploaded_file.py
app/services/remote_fate_service.py
```

Features:

* Upload CSV files
* Select dataset usage type: `train` or `predict`
* Save file metadata and binary content in the database
* Write the file to the remote FATE server
* Automatically prepare FATE-compatible CSV files
* Upload datasets to FATE tables
* Query dataset metadata
* Backend endpoint for downloading uploaded files, although file download is not emphasized as a main UI function in the current version
* Delete database records, FATE tables, and generated server files
* Clean orphan files left on the remote server

---

### 7.3 Training Management

The training module allows users to create FATE training jobs from uploaded datasets.

Related files:

```text
app/routers/fate_api.py
app/services/remote_fate_service.py
app/models/job_record.py
app/models/model_record.py
```

Features:

* Load uploaded training datasets
* Select training algorithm
* Configure training parameters
* Dynamically generate a FATE pipeline script
* Start training inside the remote FATE Docker container
* Extract Job ID, Model ID, and Model Version
* Save job records
* Save model records
* Query training progress
* Request job logs
* Query training metrics
* Stop a training job

Current implementation mainly supports:

```text
Homo Logistic Regression / HomoLR
```

---

### 7.4 Model Management

The model module provides local model record management and FATE model query functions.

Related files:

```text
app/routers/fate_api.py
app/models/model_record.py
app/services/remote_fate_service.py
```

Features:

* List trained models
* View local model details
* Query FATE model information
* Edit local model name, version, and description
* Delete model records
* Delete WebApp-generated pipeline `.pkl` files from the remote server

---

### 7.5 Prediction Management

The prediction module allows users to create prediction jobs based on trained models and prediction datasets.

Related files:

```text
app/routers/fate_api.py
app/models/prediction_record.py
app/models/model_record.py
app/models/uploaded_file.py
app/services/remote_fate_service.py
app/static/js/app.js
```

Features:

* Load available trained models
* Load uploaded prediction datasets
* Dynamically generate prediction pipeline scripts
* Start prediction jobs in FATE
* Save prediction records
* Save prediction jobs into the job history
* Query prediction status
* View prediction results
* Download prediction results to a local text file
* Edit prediction notes
* Delete prediction records
* Delete generated prediction scripts from the remote server

Prediction results are not stored directly in the WebApp database. The database stores the prediction job record and prediction Job ID. When the user clicks **View** or **Download**, the backend queries the FATE output table, downloads the result data from FATE, reads the generated CSV/meta files, and returns the content to the frontend.

The current prediction result workflow is:

```text
Prediction Job ID
        ↓
flow output query-data-table -tn homo_lr_0
        ↓
Get output table namespace and name
        ↓
flow data download
        ↓
Read downloaded result files
        ↓
Display result in WebApp or download result as local .txt file
```

---

### 7.6 Dashboard

The main dashboard shows the current FATE Flow status and recent job records.

Related files:

```text
app/routers/fate_api.py
app/static/js/app.js
app/templates/mainpage.html
```

Features:

* Check whether FATE Flow is running
* Automatically attempt to start FATE Flow if it is not running
* Show recent training job count
* Show recent prediction job count
* Show recent job list
* Auto-refresh dashboard data

---

## 8. API Overview

### 8.1 Authentication Routes

| Method | Path        | Description                           |
| ------ | ----------- | ------------------------------------- |
| `GET`  | `/login`    | Show login page                       |
| `POST` | `/login`    | Submit login form                     |
| `GET`  | `/register` | Show registration page                |
| `POST` | `/register` | Submit registration form              |
| `GET`  | `/logout`   | Logout and delete access token cookie |

---

### 8.2 Page Routes

| Method | Path         | Description              |
| ------ | ------------ | ------------------------ |
| `GET`  | `/`          | Main dashboard page      |
| `GET`  | `/data`      | Dataset management page  |
| `GET`  | `/training`  | Training management page |
| `GET`  | `/model`     | Model management page    |
| `GET`  | `/predicted` | Prediction page          |

---

### 8.3 Dataset APIs

Prefix:

```text
/api/files
```

| Method   | Path                            | Description                                       |
| -------- | ------------------------------- | ------------------------------------------------- |
| `POST`   | `/api/files/upload`             | Upload a dataset and import it into FATE          |
| `GET`    | `/api/files/list`               | List uploaded files                               |
| `GET`    | `/api/files/{file_id}`          | Get file details and FATE metadata                |
| `PUT`    | `/api/files/{file_id}`          | Update file description                           |
| `GET`    | `/api/files/{file_id}/download` | Download original uploaded file                   |
| `DELETE` | `/api/files/{file_id}`          | Delete file record, FATE table, and server files  |
| `POST`   | `/api/files/cleanup-orphans`    | Clean orphan WebApp-generated files on the server |

---

### 8.4 FATE Status and Dashboard APIs

Prefix:

```text
/api/fate
```

| Method | Path                               | Description                             |
| ------ | ---------------------------------- | --------------------------------------- |
| `GET`  | `/api/fate/status`                 | Check FATE Flow process status          |
| `GET`  | `/api/fate/root-check`             | Check remote FATE environment           |
| `GET`  | `/api/fate/debug/components`       | List available FATE pipeline components |
| `GET`  | `/api/fate/dashboard/main-summary` | Get dashboard summary                   |

---

### 8.5 Training APIs

| Method | Path                          | Description                              |
| ------ | ----------------------------- | ---------------------------------------- |
| `GET`  | `/api/fate/training/datasets` | List datasets available for training     |
| `POST` | `/api/fate/training/create`   | Create a training job from configuration |
| `POST` | `/api/fate/training/progress` | Query training progress                  |
| `POST` | `/api/fate/training/logs`     | Get training logs                        |
| `POST` | `/api/fate/training/metrics`  | Query training metrics                   |
| `POST` | `/api/fate/training/stop`     | Stop a training job                      |
| `POST` | `/api/fate/training/start`    | Start training from a pipeline script    |

---

### 8.6 Job APIs

| Method | Path                           | Description                             |
| ------ | ------------------------------ | --------------------------------------- |
| `POST` | `/api/fate/job/query`          | Query a FATE job with role and party ID |
| `GET`  | `/api/fate/job/query/{job_id}` | Query a FATE job by Job ID              |
| `GET`  | `/api/fate/job/log/{job_id}`   | Get job log                             |

---

### 8.7 Data Table APIs

| Method | Path                      | Description                            |
| ------ | ------------------------- | -------------------------------------- |
| `POST` | `/api/fate/output/table`  | Query job output table                 |
| `POST` | `/api/fate/data/upload`   | Upload data using a remote JSON config |
| `GET`  | `/api/fate/data/history`  | Query upload history                   |
| `POST` | `/api/fate/data/query`    | Query FATE table                       |
| `GET`  | `/api/fate/data/download` | Download or preview FATE table data    |
| `POST` | `/api/fate/table/delete`  | Delete a FATE table                    |

---

### 8.8 Model APIs

| Method   | Path                          | Description                                           |
| -------- | ----------------------------- | ----------------------------------------------------- |
| `GET`    | `/api/fate/models/list`       | List local model records                              |
| `POST`   | `/api/fate/models/detail`     | Get local and FATE model details                      |
| `PUT`    | `/api/fate/models/update`     | Update local model record                             |
| `DELETE` | `/api/fate/models/{model_id}` | Delete local model record and generated pipeline file |
| `POST`   | `/api/fate/model/query`       | Query FATE model                                      |
| `POST`   | `/api/fate/model/export`      | Export FATE model                                     |
| `POST`   | `/api/fate/model/load`        | Load FATE model                                       |
| `POST`   | `/api/fate/predict/conf`      | Get prediction config                                 |
| `POST`   | `/api/fate/predict/dsl`       | Get prediction DSL                                    |

---

### 8.9 Prediction APIs

| Method   | Path                                       | Description                                                |
| -------- | ------------------------------------------ | ---------------------------------------------------------- |
| `GET`    | `/api/fate/prediction/models`              | List models available for prediction                       |
| `GET`    | `/api/fate/prediction/datasets`            | List datasets available for prediction                     |
| `POST`   | `/api/fate/prediction/create`              | Create a prediction job                                    |
| `GET`    | `/api/fate/prediction/list`                | List prediction records                                    |
| `POST`   | `/api/fate/prediction/status`              | Query prediction status                                    |
| `POST`   | `/api/fate/prediction/result`              | Query, download from FATE, and return prediction result    |
| `PUT`    | `/api/fate/prediction/update`              | Update prediction note                                     |
| `DELETE` | `/api/fate/prediction/{prediction_job_id}` | Delete prediction record and generated prediction script   |
| `POST`   | `/api/fate/prediction/start`               | Start prediction from a pipeline script                    |

The `/api/fate/prediction/result` endpoint is used by both the **View** button and the **Download** button on the Predicted Page.

It does not read prediction results directly from the WebApp database. Instead, it:

```text
1. receives prediction_job_id from the frontend;
2. queries the FATE output table of homo_lr_0;
3. extracts the result table namespace and name;
4. downloads the result table using flow data download;
5. reads the downloaded CSV/meta files;
6. returns readable text to the frontend.
```

The frontend uses the returned text in two ways:

```text
View button:
    display the prediction result in a modal window

Download button:
    generate a local .txt file in the browser
```

---

## 9. Notes and Important Considerations

### 9.1 `.env`

The real `.env` file contains sensitive data such as:

* Database connection string
* Application secret key
* Fernet encryption key
* Remote server configuration
* Possible server credentials

So only `.env.example` is committed to GitHub.

Recommended `.gitignore` entries:

```gitignore
.env
*.env
!.env.example
.venv/
venv/
__pycache__/
*.pyc
*.log
*.sqlite
*.sqlite3
```

---

### 9.2 Remote Server Password Encryption

Remote server passwords are encrypted using `APP_FERNET_KEY`.

Do not change `APP_FERNET_KEY` after user registration unless you are ready to re-register or reset encrypted server passwords.

If the key changes, existing encrypted passwords in the database cannot be decrypted.

---

### 9.3 FATE Environment Assumptions

This project assumes:

* FATE is installed on a remote server.
* FATE runs inside a Docker container.
* The container name is configured by `FATE_CONTAINER`.
* The FATE root directory is configured by `FATE_ROOT`.
* The backend can SSH into the remote server.
* The remote user has permission to start and execute commands inside the FATE Docker container.

---

### 9.4 Current Algorithm Support

The current dynamic training pipeline mainly supports:

```text
Homo Logistic Regression / HomoLR
```

Algorithm names mapped internally to `HomoLR`.

If additional algorithms are required, `RemoteFateService.build_training_pipeline_script()` can be extended.

---

### 9.5 CSV Format Requirements

Uploaded CSV files should contain an ID column.

The default ID column name is:

```text
id
```

For training datasets, the default label column name is:

```text
label
```

The system automatically creates a processed CSV with an additional `match_id` column because the FATE HomoLR environment requires it.

Example training CSV:

```csv
id,feature1,feature2,label
1,0.5,1.2,0
2,0.8,2.1,1
```

The system will convert it internally to:

```csv
id,match_id,feature1,feature2,label
1,1,0.5,1.2,0
2,2,0.8,2.1,1
```

---

### 9.6 Database Table Creation

The application uses:

```python
Base.metadata.create_all(bind=engine)
```

To automatically create database tables during startup.

This is convenient for course projects and prototypes.

For production systems, it is recommended to use a migration tool such as Alembic.

---

### 9.7 Multi-User Data Isolation

The current code checks user login status, but some database queries may not yet filter records by `user_id`.

---

### 9.8 Error Handling

Training, prediction, and upload operations depend on remote SSH, Docker, FATE Flow, and pipeline execution.

If a task fails, check:

* Browser alert message
* WebApp log output panel
* Backend terminal logs
* Returned `stdout` and `stderr`
* FATE task error reports
* Remote generated scripts under `/data/projects/fate/examples`

---

### 9.9 Docker Oracle Database Notes

This project uses Docker Oracle XE for local testing.

The database container is started by:

```bash
docker compose up -d oracle-db
```

The Oracle image is:

```text
container-registry.oracle.com/database/express:21.3.0-xe
```

The WebApp database user is:

```text
FATE_APP / fate_app_password
```

The service name is:

```text
XEPDB1
```

If the database needs to be reset during development, run:

```bash
docker compose down -v
docker compose up -d oracle-db
```

Warning:

```text
docker compose down -v
```

will remove the Oracle Docker volume and delete all local database data, including uploaded file records, job records, model records, prediction records, and the administrator account.

After resetting the database, run:

```bash
python scripts/seed_admin.py
```

again to recreate the administrator account.
