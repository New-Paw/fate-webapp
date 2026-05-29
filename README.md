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
│
├── logs/
├── uploads/
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

## 4. Environment Configuration

This project uses a `.env` file to store local configuration and secrets.

The real .env file is not uploaded to GitHub.

The repository only include:

.env.example

To create your local `.env` file:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your own values.

---

### 4.1 Example `.env` Configuration

```env

# ------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------
APP_HOST=127.0.0.1
APP_PORT=8000


# ------------------------------------------------------------
# Database
# Oracle format:
# oracle+oracledb://USERNAME:PASSWORD@HOST:PORT/?service_name=SERVICE_NAME
# SQLite local test format:
# sqlite:///./fate_webapp.db
# ------------------------------------------------------------
DATABASE_URL=oracle+oracledb://YOUR_DB_USERNAME:YOUR_DB_PASSWORD@YOUR_DB_HOST:1521/?service_name=YOUR_SERVICE_NAME


# ------------------------------------------------------------
# Remote Server SSH Configuration
# Server username/password should normally be registered through the WebApp UI.
# ------------------------------------------------------------
GRACE_HOST=grace1.fit.vutbr.cz
GRACE_PORT=22


# ------------------------------------------------------------
# FATE Docker / Runtime Configuration
# ------------------------------------------------------------
FATE_CONTAINER=standalone_fate
FATE_ROOT=/data/projects/fate


# ------------------------------------------------------------
# Optional FATE Flow SDK Configuration
# Used by app/services/fate_client.py if enabled.
# ------------------------------------------------------------
FATE_HOST=127.0.0.1
FATE_PORT=9380
FATE_API_VERSION=v1


# ------------------------------------------------------------
# WebApp Authentication
# Generate APP_SECRET_KEY:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
# ------------------------------------------------------------
APP_SECRET_KEY=replace_with_random_secret_key


# ------------------------------------------------------------
# Server Password Encryption Key
# Generate APP_FERNET_KEY:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Important: # If you want to reuse an existing administrator account from # an existing database, this key must be the same key that was # used when that account was created.
# Warning:
# If APP_FERNET_KEY is changed later, previously encrypted server passwords in the database will no longer be decryptable.
# ------------------------------------------------------------
APP_FERNET_KEY=replace_with_fernet_key


# ------------------------------------------------------------
# Login Token Expiration
# Unit: minutes
# 720 minutes = 12 hours
# ------------------------------------------------------------
ACCESS_TOKEN_EXPIRE_MINUTES=720
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
* If `APP_FERNET_KEY` is changed after users are registered, previously encrypted server passwords cannot be decrypted.
* If an existing administrator account should be reused, the original APP_FERNET_KEY must be used.

---

## 5. Shared Test Environment and Administrator Account

This project supports a shared test environment for demonstration and testing purposes.

For testing, a preconfigured administrator account is available in the existing project database:

Account: administrator
Password: 123456

This account can be used to log in to the WebApp after the application is connected to the correct database and environment configuration.

Important: This account is intended for testing only. Do not use this password in a production environment.

---

### 5.1 Required .env Configuration for Testing

The real .env file is not included in this GitHub repository because it contains sensitive configuration such as:

Database connection string
Application secret key
Fernet encryption key
Remote server settings
FATE runtime settings

To use the shared test environment, testers must obtain the real .env file from the project maintainer through a private and secure channel.

After receiving the .env file, place it in the project root directory:

FATE_WEBAPP/
├── app/
├── .env
├── .env.example
├── requirements.txt
└── README.md

The .env file must contain the following configuration keys:

DATABASE_URL=
APP_SECRET_KEY=
APP_FERNET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=

GRACE_HOST=
GRACE_PORT=

FATE_CONTAINER=
FATE_ROOT=

FATE_HOST=
FATE_PORT=
FATE_API_VERSION=

The values of these variables must match the original test environment.

---

### 5.2 Why the Original .env Is Required

The administrator account already exists in the database.

To use this account correctly, the application must connect to the same database that stores the administrator user record.

In addition, the existing remote server password stored in the database was encrypted using the original APP_FERNET_KEY.

Therefore, the following values must match the original environment:

DATABASE_URL
APP_FERNET_KEY
APP_SECRET_KEY
GRACE_HOST
GRACE_PORT
FATE_CONTAINER
FATE_ROOT

If DATABASE_URL points to a different database, the administrator account may not exist.

If APP_FERNET_KEY is changed, the WebApp may still verify the administrator login password, but it will not be able to decrypt the stored remote server password. In that case, FATE operations that require SSH access may fail.

---

### 5.3 Testing Procedure with the Administrator Account
Clone the repository:
git clone https://github.com/New-Paw/fate-webapp.git
cd fate-webapp
Create and activate a Python virtual environment:
python -m venv .venv
source .venv/bin/activate

On Windows:

.venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Obtain the real .env file from the project maintainer.
Put the .env file in the project root directory.
Start the WebApp:
uvicorn app.main:app --reload
Open the browser:
http://127.0.0.1:8000
Log in with the test account:
Account: administrator
Password: 123456

After login, testers can use the WebApp.

---

### 5.4 When to Register a New Account

Register a new account instead of using the administrator account if:

you are using a new empty database;
you do not have access to the original .env file;
you generated a new APP_FERNET_KEY;
the administrator account does not exist in your database;
you want to use a different remote server username and password.

During registration:

the WebApp password will be stored as a hash;
the remote server password will be encrypted using the current APP_FERNET_KEY.

---

### 5.5 Security Notes for the Test Account

I did not include any real passwords, real database connections, real Fernet Keys or administrator passwords. The README only describes the usage process and precautions. If you need to test using my original environment, please contact me: Jiangpw5379@outlook.com.

---

## 6. How to Run

### 6.1 Start the Web Application

From the project root directory:

```bash
uvicorn app.main:app --reload
```

Then open the browser:

```text
http://127.0.0.1:8000
```

---

### 6.2 First-Time Usage

1. Open the application in the browser.
2. Register a WebApp account.
3. Enter your remote server username and password during registration.
4. The WebApp password will be stored as a hash.
5. The remote server password will be encrypted before being stored in the database.
6. After login, use the web pages to upload datasets, create training jobs, manage models, and run predictions.

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
* Download original uploaded files
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
* Edit prediction notes
* Delete prediction records
* Delete generated prediction scripts from the remote server

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

| Method   | Path                                       | Description                                   |
| -------- | ------------------------------------------ | --------------------------------------------- |
| `GET`    | `/api/fate/prediction/models`              | List models available for prediction          |
| `GET`    | `/api/fate/prediction/datasets`            | List datasets available for prediction        |
| `POST`   | `/api/fate/prediction/create`              | Create a prediction job                       |
| `GET`    | `/api/fate/prediction/list`                | List prediction records                       |
| `POST`   | `/api/fate/prediction/status`              | Query prediction status                       |
| `POST`   | `/api/fate/prediction/result`              | Get prediction result                         |
| `PUT`    | `/api/fate/prediction/update`              | Update prediction note                        |
| `DELETE` | `/api/fate/prediction/{prediction_job_id}` | Delete prediction record and generated script |
| `POST`   | `/api/fate/prediction/start`               | Start prediction from a pipeline script       |

---

## 9. Notes and Important Considerations

### 9.1 Do Not Commit `.env`

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

## 10. License

This project is intended for academic and learning purposes.
