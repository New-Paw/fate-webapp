# 1. Introduction

Federated learning is an important machine learning approach that allows multiple parties to collaboratively train models without directly sharing their raw data. This makes it especially useful in scenarios where data privacy, data ownership, and distributed data storage are important concerns. However, federated learning frameworks usually require a relatively complex runtime environment, including data preparation, task configuration, job submission, model management, and result querying.

FATE is a federated learning framework that provides support for data management, training jobs, model storage, prediction workflows, and task monitoring. In this project, FATE is used in a standalone environment running inside a Docker container on a remote server. Although FATE provides command-line tools such as `flow`, operating the system directly through SSH, Docker commands, and FATE command-line instructions can be inconvenient for users who are not familiar with the internal environment.

The original manual workflow usually requires the user to perform several steps repeatedly:

```text
1. Log in to the remote server through SSH.
2. Start or enter the FATE Docker container.
3. Load the FATE runtime environment.
4. Upload or prepare dataset files.
5. Execute FATE Flow commands manually.
6. Query job status, logs, metrics, models, and prediction results.
7. Clean database records, FATE tables, and generated server files manually.
```

This process is not user-friendly and can easily lead to operational mistakes. For example, a user may delete a dataset record from the WebApp database but forget to delete the corresponding generated file on the server or the related table inside FATE. Similarly, training and prediction jobs may be difficult to track if job identifiers, model records, and output files are not managed consistently.

To address these problems, this year project designs and implements a web-based management system named **FATE WebApp UI**. The system provides a browser-based interface for managing the main workflow of FATE federated learning experiments. Instead of requiring users to manually execute commands inside the remote server, the WebApp encapsulates these operations into backend services and exposes them through web pages and API endpoints.

The application is implemented using **FastAPI** as the backend framework, **SQLAlchemy** for database operations, **Jinja2 templates** and JavaScript for the frontend interface, and an SSH-based service layer for remote FATE execution. The WebApp communicates with the remote server, starts or checks the FATE Docker container, executes FATE commands, dynamically generates training and prediction pipeline scripts, and stores experiment-related records in the database.

The main purpose of this project is to build a complete and usable management system for a remote standalone FATE environment. The system focuses on simplifying the following tasks:

* user registration and login;
* secure storage of WebApp passwords and remote server credentials;
* dataset upload and FATE table registration;
* training task creation and job tracking;
* trained model record management;
* prediction task creation, result querying, and local result download;
* synchronization between database records, FATE tables, and generated server files;
* preparation for GitHub-based project sharing and Docker Oracle-based testing.

In summary, this project transforms a command-line-based federated learning workflow into a structured WebApp workflow. It improves usability, reduces repetitive manual operations, and provides a clearer foundation for managing FATE experiments in a year project environment.

---

# 2. Project Objectives

The main objective of this project is to design and implement a web-based management system that simplifies the operation of a standalone FATE federated learning environment. The system aims to replace repeated manual command-line operations with a structured browser-based workflow.

In the original FATE working environment, users need to interact with several layers manually, including the remote server, Docker container, FATE runtime environment, FATE Flow commands, dataset files, generated scripts, and database records. This project aims to integrate these operations into a single WebApp so that users can manage the full experimental process more conveniently.

The project objectives can be divided into several specific goals.

---

## 2.1 Build a Web-Based User Interface for FATE Operations

The first objective is to provide a browser-based interface for common FATE operations. Instead of requiring users to manually log in to the server and execute FATE commands, the WebApp should allow users to perform these operations through pages and buttons.

The WebApp should provide pages for:

* user login and registration;
* dataset management;
* training task management;
* model management;
* prediction task management;
* dashboard monitoring.

This objective focuses on improving usability and reducing the difficulty of operating FATE in a remote Docker-based environment.

---

## 2.2 Implement Secure User Authentication

The second objective is to implement a basic user authentication system.

The system should support:

* user registration;
* user login;
* user logout;
* protected pages;
* protected backend APIs.

For security reasons, WebApp login passwords should not be stored in plain text. Instead, they should be stored as password hashes. After successful login, the system should generate an access token and store it in an HTTP-only cookie so that protected pages and APIs can verify the current user.

---

## 2.3 Store Remote Server Credentials Securely

Because the WebApp needs to connect to the remote FATE server, it must store the remote server username and password for each registered user.

However, the remote server password cannot be stored as plain text. Therefore, the project uses encryption to store the remote server password in the database.

The goal is to support the following workflow:

```text id="wj17bz"
User registers a WebApp account
        ↓
User provides remote server username and password
        ↓
WebApp hashes the WebApp login password
        ↓
WebApp encrypts the remote server password
        ↓
Encrypted credentials are stored in the database
        ↓
Backend decrypts the remote server password only when SSH access is required
```

This design separates WebApp authentication from remote server access while keeping sensitive credentials protected.

---

## 2.4 Manage Uploaded Datasets

Another important objective is to provide dataset management functions.

The system should allow users to:

* upload CSV files through the browser;
* choose whether the uploaded file is used for training or prediction;
* store file metadata in the database;
* store the file content or related information for later access;
* generate FATE-compatible table names and namespaces;
* upload the dataset into FATE automatically;
* view dataset details and FATE metadata;
* delete the dataset from the database, FATE table storage, and generated server files.

This objective is important because dataset preparation is one of the first steps in a FATE experiment. The WebApp should reduce the need for manual file transfer and manual `flow data upload` commands.

---

## 2.5 Create and Track Training Jobs

The project should support creating FATE training jobs from the WebApp.

The training module should allow users to:

* select an uploaded training dataset;
* select a supported algorithm;
* dynamically generate a FATE training pipeline script;
* execute the training script inside the remote FATE Docker container;
* extract the generated FATE Job ID;
* save the training job record in the database;
* save the trained model information in the database;
* check training progress, logs, and metrics.

The current implementation mainly focuses on supporting:

```text id="yu5h60"
Homo Logistic Regression / HomoLR
```

The objective is not only to start a training job, but also to keep the job traceable through database records and WebApp pages.

---

## 2.6 Manage Trained Models

After a training job is submitted and completed, the system should save model-related information so that users can manage and reuse trained models.

The model management module should support:

* listing trained models;
* viewing local model records;
* querying model information from FATE;
* editing model name, version, and description;
* storing the generated training pipeline path;
* deleting local model records and related generated pipeline files.

This objective helps users organize trained models and select them later for prediction tasks.

---

## 2.7 Create and Track Prediction Jobs

The project should also provide prediction management functions.

The prediction module should allow users to:

* select a trained model;
* select an uploaded prediction dataset;
* dynamically generate a prediction pipeline script;
* execute the prediction task inside the remote FATE Docker container;
* extract the prediction Job ID;
* save prediction records in the database;
* query prediction status;
* view prediction results;
* edit prediction notes;
* delete prediction records and related generated scripts.

This objective completes the full machine learning workflow from dataset upload to training and then to prediction.

---

## 2.8 Integrate Remote SSH, Docker, and FATE Flow Commands

A core technical objective of this project is to hide the complexity of the remote execution environment.

The backend service should be able to:

* connect to the remote server through SSH;
* start the FATE Docker container if necessary;
* execute commands inside the Docker container;
* enter the FATE root directory;
* load the FATE runtime environment;
* run FATE Flow commands;
* run dynamically generated Python pipeline scripts;
* return command output, error messages, Job IDs, and execution status to the WebApp.

This objective is implemented mainly through the `RemoteFateService` service layer.

---

## 2.9 Keep Database, FATE Tables, and Server Files Consistent

During development, one important issue was that deleting a database record did not automatically delete the corresponding generated files on the server or the related FATE table.

Therefore, another objective is to improve consistency between:

* WebApp database records;
* FATE internal tables;
* generated upload configuration files;
* generated training scripts;
* generated prediction scripts;
* uploaded temporary files on the remote server.

The system should delete related files and FATE tables when a dataset, model, or prediction record is removed from the WebApp.

This objective reduces file accumulation and prevents ID or file conflicts during repeated experiments.

---

## 2.10 Summary of Objectives

Overall, the project aims to provide a complete WebApp-based management workflow for FATE experiments.

The expected outcome is a system that can:

```text id="7w6swg"
Register and authenticate users
        ↓
Manage uploaded datasets
        ↓
Upload data into FATE
        ↓
Create and monitor training jobs
        ↓
Manage trained models
        ↓
Create and monitor prediction jobs
```

By achieving these objectives, the project provides a practical management layer above a remote standalone FATE environment and improves the usability, maintainability, and reliability of the experimental workflow.

---

# 3. Background and Related Technologies

This project combines federated learning, web application development, database management, remote server operation, and container-based execution. 

The system is not only a normal WebApp, but also a management layer built on top of a remote FATE federated learning environment. Therefore, several technologies are involved in different parts of the system, including FATE, FastAPI, SQLAlchemy, Jinja2, JavaScript, SSH, Docker, and environment-based configuration.

---

## 3.1 Federated Learning

Federated learning is a machine learning approach that allows multiple parties to train a shared model without directly exchanging raw data. Instead of collecting all data into one central location, each party keeps its own data locally and participates in the training process through model updates or intermediate information.

This approach is useful in scenarios where data cannot be freely shared due to privacy, ownership, legal, or organizational restrictions.

In a traditional machine learning workflow, data is usually collected into one central dataset:

```text id="rzocvx"
Data from Party A
        ↓
Data from Party B
        ↓
Centralized Dataset
        ↓
Model Training
```

In a federated learning workflow, the data can remain distributed:

```text id="fng5w3"
Party A Data        Party B Data
     ↓                  ↓
Local Processing    Local Processing
     ↓                  ↓
Federated Training Coordination
        ↓
Shared Model
```

The main advantage of federated learning is that it provides a way to train models while reducing the need to directly transfer raw data between participants.

In this project, federated learning is the application background. The WebApp does not implement federated learning algorithms by itself. Instead, it provides a management interface for operating FATE, which is responsible for the actual federated learning execution.

---

## 3.2 FATE Framework

FATE is a federated learning framework that provides tools for data management, task submission, model training, model management, prediction, and job monitoring.

In this project, FATE is used as the underlying federated learning platform. The WebApp sends commands to FATE to perform operations such as:

* uploading data;
* querying FATE tables;
* creating training jobs;
* querying job status;
* retrieving logs and metrics;
* managing models;
* creating prediction jobs;
* retrieving prediction results.

The FATE environment used in this project is a standalone environment running inside a Docker container on a remote server. Users normally need to access it manually through commands such as:

```bash id="7v42pv"
ssh username@remote-server
docker start standalone_fate
docker exec -it standalone_fate bash
source bin/init_env.sh
flow job query -j <job_id> -r guest -p 9999
```

This manual process is one of the main reasons why this WebApp was developed. The system encapsulates these steps in the backend service layer so that users can operate FATE through a browser instead of manually typing all commands.

---

## 3.3 FATE Flow and `flow` Commands

FATE Flow is the task scheduling and management component of FATE. It provides command-line tools for managing jobs, data, models, logs, metrics, and prediction tasks.

The project uses FATE Flow commands indirectly through backend service functions.

Typical commands include:

```bash id="y0vtif"
flow job query -j <job_id> -r guest -p 9999
flow data upload -c <config_file>
flow table delete --namespace <namespace> --name <table_name>
flow component metric-all -j <job_id> -r guest -p 9999 -cpn evaluation_0
```

Instead of exposing these commands directly to users, the WebApp provides API endpoints and frontend buttons.

For example:

```text id="kcw4h0"
Frontend button: Create Training
        ↓
POST /api/fate/training/create
        ↓
Backend generates and executes a FATE pipeline script
        ↓
FATE Flow creates a training job
        ↓
Job ID is returned and saved in the database
```

This design makes FATE easier to use and reduces the chance of command-line mistakes.

---

## 3.4 FastAPI

FastAPI is the backend web framework used in this project. It is responsible for creating the web application, defining API routes, handling HTTP requests, returning HTML pages, and validating request data.

The project uses FastAPI for two main types of routes:

```text id="s37ds5"
1. Page routes
   These routes return HTML pages rendered by Jinja2 templates.

2. API routes
   These routes return JSON data and are called by frontend JavaScript.
```

Examples of page routes include:

```text id="g8vil0"
GET /login
GET /
GET /data
GET /training
GET /model
GET /predicted
```

Examples of API routes include:

```text id="kwnvll"
POST /api/files/upload
GET  /api/files/list
POST /api/fate/training/create
GET  /api/fate/models/list
POST /api/fate/prediction/create
```

FastAPI is also used together with dependency injection. For example, the project uses dependencies to provide database sessions and authentication checks:

```python id="10oknq"
db: Session = Depends(get_db)
current_user: AppUser = Depends(get_current_user)
```

This structure makes route functions cleaner and separates common logic such as database connection and user authentication.

---

## 3.5 SQLAlchemy

SQLAlchemy is used as the Object Relational Mapping framework in this project.

It allows database tables to be represented as Python classes. For example, the user table is represented by the `AppUser` model, and uploaded files are represented by the `UploadedFile` model.

The main database models include:

```text id="sbzpuy"
AppUser
UploadedFile
JobRecord
ModelRecord
PredictionRecord
```

These models are used to store the main data of the WebApp:

* user accounts;
* uploaded dataset information;
* FATE job records;
* trained model records;
* prediction records.

The database connection is configured in `app/db.py`, which defines:

```text id="kh09pi"
engine
SessionLocal
Base
get_db()
```

The `get_db()` function is used as a FastAPI dependency to provide database sessions to route functions.

Example usage:

```python id="4dba7b"
def list_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files
```

SQLAlchemy is important in this project because it provides a structured way to persist data and link WebApp operations with FATE experiment records.

---

## 3.6 Database System

The project stores WebApp-side application data in an Oracle database. In the latest version of the project, the database is provided through a local Docker Oracle XE container instead of relying on the original external database.

This change improves the reproducibility of the project. Other testers do not need access to the original development database. Instead, they can start their own local Oracle XE database by using Docker Compose.

The local Docker Oracle database is started with:

```bash
docker compose up -d oracle-db
```

The WebApp connects to this database through the `DATABASE_URL` value in the `.env` file.

The default local Docker Oracle connection is:

```env
DATABASE_URL=oracle+oracledb://FATE_APP:fate_app_password@127.0.0.1:1521/?service_name=XEPDB1
```

The application database user is:

```text
Username: FATE_APP
Password: fate_app_password
Service name: XEPDB1
```

This user is created by the SQL initialization script:

```text
docker/oracle/init/01_create_app_user.sql
```

The database is used to store WebApp-side records, including:

```text
AppUser
UploadedFile
JobRecord
ModelRecord
PredictionRecord
```

FATE still stores its own internal data tables and job information separately inside the remote FATE environment. Therefore, the WebApp needs to maintain consistency between:

```text
Docker Oracle WebApp database records
FATE internal tables
Generated files on the remote FATE server
```

The Docker Oracle database makes GitHub-based testing easier because each tester can create the same database environment locally.

---

## 3.7 Jinja2 Templates

Jinja2 is used to render HTML pages on the backend side.

The project contains several template files:

```text id="iqdls5"
base.html
login.html
register.html
mainpage.html
datapage.html
trainingpage.html
modelpage.html
predictedpage.html
```

The page routes in `app/routers/pages.py` return these templates. For example:

```python id="a8q7z6"
return templates.TemplateResponse(
    request,
    "mainpage.html",
    context
)
```

Jinja2 provides the static structure of each page, while dynamic data is loaded by JavaScript through API calls after the page is opened.

This design separates page rendering from data loading:

```text id="swb0g8"
Jinja2 templates
        ↓
Render page layout
        ↓
JavaScript fetch API
        ↓
Load dynamic data from backend APIs
```

---

## 3.8 JavaScript and Fetch API

The frontend dynamic behavior is implemented mainly in `app/static/js/app.js`.

The JavaScript file is responsible for:

* loading dashboard data;
* loading uploaded dataset lists;
* submitting file upload forms;
* creating training jobs;
* loading model lists;
* creating prediction jobs;
* showing details in modal windows;
* refreshing job and prediction status.

The frontend communicates with the backend using the Fetch API.

Example workflow:

```text id="iyzl5g"
User clicks a button
        ↓
JavaScript sends a fetch request
        ↓
FastAPI route processes the request
        ↓
Backend returns JSON
        ↓
JavaScript updates the page
```

For example, when the dashboard page is loaded, JavaScript calls:

```text id="72aodp"
GET /api/fate/dashboard/main-summary
```

Then it updates the FATE Flow status, job statistics, and recent job list on the page.

This approach keeps the pages interactive without requiring the whole page to reload after every operation.

---

## 3.9 SSH and Paramiko

The WebApp needs to execute commands on a remote server where FATE is installed. To do this, the backend uses SSH-based remote execution.

In the project, this logic is implemented in the `RemoteFateService` service layer. The service connects to the remote server, runs shell commands, starts the Docker container, and executes FATE commands inside the container.

The remote execution workflow can be summarized as:

```text id="4i7gpi"
WebApp backend
        ↓
SSH connection
        ↓
Remote server
        ↓
Docker container
        ↓
FATE runtime environment
        ↓
FATE Flow command or Python pipeline script
```

This layer is one of the most important parts of the project because it bridges the WebApp and the remote FATE environment.

---

## 3.10 Docker

Docker is used in two different parts of this project.

The first Docker environment is the local Docker Oracle database. It is used to provide a reproducible database environment for the WebApp.

```text
Local machine
    ↓
Docker Oracle XE container
    ↓
WebApp database tables
```

This local database stores users, uploaded file records, job records, model records, and prediction records.

The second Docker environment is the remote FATE Docker container. FATE runs inside a Docker container on the remote server.

```text
Remote server
    ↓
FATE Docker container
    ↓
FATE runtime environment
```

The FATE container name is configured in `.env`:

```env
FATE_CONTAINER=standalone_fate
```

The WebApp backend connects to the remote server through SSH, checks or starts the FATE container, and executes FATE commands inside it.

Therefore, the two Docker environments have different purposes:

```text
Docker Oracle container:
    local database for WebApp records

Remote FATE container:
    remote runtime for federated learning operations
```

This distinction is important because starting the Docker Oracle database does not start FATE. FATE operations still depend on the remote server and its FATE Docker container.

---

## 3.11 Environment Variables and `.env`

The project uses environment variables to manage configuration.

Sensitive configuration is stored in a local `.env` file, including:

* database connection string;
* application secret key;
* Fernet encryption key;
* remote server settings;
* FATE runtime settings.

The real `.env` file is not committed to GitHub. Instead, the repository provides a `.env.example` file as a template.

The `.gitignore` file include:

```gitignore id="r017i4"
.env
*.env
!.env.example
```

This ensures that private configuration remains local while still giving other users a clear template for setting up their environment.

The `APP_SECRET_KEY` is used for JWT token signing, while `APP_FERNET_KEY` is used to encrypt and decrypt remote server passwords stored in the database.

---

## 3.12 Authentication and Security Technologies

The project uses several security-related mechanisms.

### Password Hashing

WebApp login passwords are not stored in plain text. They are hashed before being saved to the database.

The project uses password hashing in `auth_service.py`:

```text id="6qn7bq"
hash_password()
verify_password()
```

This means that during login, the system verifies the input password against the stored password hash instead of comparing plain text passwords.

### Fernet Encryption

Remote server passwords must be recoverable because the backend needs them to connect to the remote FATE server. Therefore, they are encrypted rather than hashed.

The project uses Fernet encryption for this purpose:

```text id="szn0tu"
encrypt_server_password()
decrypt_server_password()
```

The encryption key is stored in `APP_FERNET_KEY`.

### JWT Access Token

After a user logs in successfully, the backend creates a JWT access token. The token is stored in an HTTP-only cookie and used to verify protected pages and APIs.

This authentication flow allows the WebApp to control access to important operations such as file upload, training creation, model management, and prediction execution.

---

## 3.13 Summary

The project combines multiple technologies to provide a complete management layer for FATE federated learning experiments.

The main technology stack can be summarized as follows:

```text id="frvlmk"
Frontend:
    HTML templates, CSS, JavaScript, Fetch API

Backend:
    FastAPI, Jinja2, Pydantic schemas

Database:
    SQLAlchemy ORM, relational database

Authentication:
    Password hashing, JWT token, HTTP-only cookie

Credential Security:
    Fernet encryption for remote server passwords

Remote Execution:
    SSH, Docker, FATE Flow commands

Federated Learning Platform:
    FATE standalone environment
```

Together, these technologies allow the system to transform complex command-line FATE operations into a structured WebApp workflow.

---

# 4. Requirement Analysis

The FATE WebApp UI is designed as a management system for a remote standalone FATE environment. Therefore, the requirements are not limited to normal web application functions. The system must also handle dataset upload, FATE command execution, remote server access, Docker container operation, experiment tracking, credential security, and cleanup of generated files.

The requirements can be divided into two main categories:

```text
1. Functional requirements
2. Non-functional requirements
```

Functional requirements describe what the system should do. Non-functional requirements describe how the system should behave in terms of security, usability, maintainability, reliability, and deployment.

---

## 4.1 User Management Requirements

The system should provide a basic user management module so that only authenticated users can access the main WebApp functions.

### 4.1.1 User Registration

The system should allow a new user to register a WebApp account.

During registration, the user should provide:

```text
WebApp account
WebApp password
Remote server username
Remote server password
```

The WebApp account and password are used for logging in to the WebApp. The remote server username and password are used by the backend service to connect to the remote FATE server.

The system should store the WebApp password as a hash rather than plain text.

The system should encrypt the remote server password before saving it into the database.

---

### 4.1.2 User Login

The system should allow registered users to log in with their WebApp account and password.

The login process should:

```text
1. Receive the account and password from the login form.
2. Query the user record from the database.
3. Verify the input password against the stored password hash.
4. Generate an access token after successful verification.
5. Store the access token in an HTTP-only cookie.
6. Redirect the user to the main dashboard page.
```

If the account does not exist or the password is incorrect, the system will show an error message and prevent login.

---

### 4.1.3 User Logout

The system should provide a logout function.

After logout, the access token cookie should be deleted, and the user should be redirected to the login page.

---

### 4.1.4 Protected Pages and APIs

The system should prevent unauthenticated users from accessing protected pages and APIs.

Protected pages include:

```text
/
 /data
 /training
 /model
 /predicted
```

Protected APIs include:

```text
/api/files/*
/api/fate/*
```

If a user is not logged in, page routes should redirect the user to the login page. API routes will return an authentication error.

---

## 4.2 Dataset Management Requirements

Dataset management is one of the core functions of the WebApp. The system should allow users to upload CSV files and register them as FATE datasets.

### 4.2.1 Dataset Upload

The system should allow users to upload dataset files through the browser.

For each uploaded file, the user should be able to specify whether it is used for:

```text
training
prediction
```

The system should store dataset metadata in the database, including:

```text
file name
content type
file size
usage type
description
FATE namespace
FATE table name
created time
updated time
```

---

### 4.2.2 FATE Dataset Registration

After a file is uploaded, the system should automatically import the dataset into FATE.

The upload process should:

```text
1. Save the uploaded file record in the WebApp database.
2. Generate a FATE namespace based on the usage type.
3. Generate a FATE table name based on the file name and database ID.
4. Write the file to the remote FATE server.
5. Prepare a FATE-compatible CSV file if necessary.
6. Generate a FATE upload configuration file.
7. Execute the FATE data upload command.
8. Verify whether the FATE table has been created successfully.
```

The system will return the FATE namespace and table name to the frontend after successful upload.

---

### 4.2.3 Dataset Listing and Details

The system should allow users to view uploaded datasets.

The dataset list should show:

```text
file ID
file name
file size
usage type
description
updated time
available actions
```

The system should also allow users to view dataset details, including both local database information and FATE metadata.

---

### 4.2.4 Dataset Update

The system should allow users to update dataset descriptions.

This operation should only modify the local database metadata and should not re-upload the dataset to FATE.

---

### 4.2.5 Dataset Deletion and Cleanup

When a dataset is deleted, the system should not only delete the local database record. It should also delete the corresponding FATE table and generated server files.

The deletion process should include:

```text
1. Query the dataset record from the database.
2. Delete the corresponding FATE table.
3. Delete uploaded temporary files from the remote server.
4. Delete generated upload configuration files.
5. Delete generated training or prediction scripts related to the dataset.
6. Delete the database record.
```

This requirement is important because otherwise the server may accumulate unused files even after the database record has been removed.

---

## 4.3 Training Management Requirements

The system should allow users to create and monitor FATE training jobs through the WebApp.

### 4.3.1 Training Dataset Selection

The training page should load datasets whose usage type is `train`.

Users should be able to select one uploaded training dataset as the input data for a training task.

---

### 4.3.2 Algorithm Selection

The system should provide a list of supported algorithms.

The current implementation mainly supports:

```text
Homo Logistic Regression / HomoLR
```

The algorithm selection should be designed in a way that can be extended in the future.

---

### 4.3.3 Training Job Creation

When the user creates a training job, the system should:

```text
1. Receive the selected dataset ID and training parameters.
2. Query the dataset record from the database.
3. Get the FATE namespace and table name from the dataset record.
4. Dynamically generate a FATE training pipeline script.
5. Execute the generated script inside the remote FATE Docker container.
6. Extract the FATE Job ID from the output.
7. Extract model information if available.
8. Save the training job record into the database.
9. Save the trained model record into the database.
10. Return the result to the frontend.
```

This process should hide all internal FATE command-line operations from the user.

---

### 4.3.4 Training Progress Query

The system should allow users to query training progress by Job ID.

The progress may be estimated from the FATE job status, such as:

```text
SUBMITTED
WAITING
RUNNING
SUCCESS
FAILED
CANCELED
```

---

## 4.4 Model Management Requirements

After training, the system should provide model management functions.

### 4.4.1 Model Record Creation

When a training job is created successfully, the system should create a model record in the database.

The model record should include:

```text
model ID
model name
algorithm
version
description
created time
```

The description may also store useful information such as:

```text
source dataset
training Job ID
FATE table information
generated pipeline path
```

---

### 4.4.2 Model Listing

The model page should display all local model records.

The list should show:

```text
model ID
model name
algorithm
version
created time
available actions
```

---

### 4.4.3 Model Details

The system should allow users to view model details.

The detail view should include:

```text
local model metadata
FATE model query output
model description
version information
```

---

### 4.4.4 Model Update

The system should allow users to update local model metadata, including:

```text
description
```

This operation updates the WebApp database record but does not change FATE internal model storage.

---

### 4.4.5 Model Deletion

The system should allow users to delete a model record.

When deleting a model, the system should also remove the generated pipeline `.pkl` file if it was created by the WebApp.

---

## 4.5 Prediction Management Requirements

The system should allow users to run prediction tasks using trained models and uploaded prediction datasets.

### 4.5.1 Prediction Model Selection

The prediction page should load available model records from the database.

Users should be able to select a trained model for prediction.

---

### 4.5.2 Prediction Dataset Selection

The prediction page should load datasets whose usage type is `predict`.

Users should be able to select one uploaded prediction dataset as the input data for prediction.

---

### 4.5.3 Prediction Job Creation

When the user creates a prediction job, the system should:

```text
1. Receive the selected model ID and prediction dataset ID.
2. Query the model record from the database.
3. Query the dataset record from the database.
4. Extract the saved training pipeline path from the model record.
5. Dynamically generate a prediction pipeline script.
6. Execute the prediction script inside the remote FATE Docker container.
7. Extract the prediction Job ID.
8. Save the prediction record into the database.
9. Save the prediction job into the general job record table.
10. Return the result to the frontend.
```

This allows users to run predictions without manually writing or executing FATE prediction scripts.

---

### 4.5.4 Prediction Status, Result Query, and Result Download

The system should allow users to query prediction status and prediction results by prediction Job ID.

The prediction result should be displayed in the WebApp so that users can inspect the output without entering the remote server manually.

In the current implementation, the Predicted Page also provides a **Download** button. This button allows users to download the prediction result to a local text file.

The prediction result is not stored directly in the WebApp database. The database stores the prediction record and prediction Job ID. When the user views or downloads a result, the backend queries the FATE output table and downloads the result data from FATE.

The result retrieval process is:

```text
Prediction Job ID
        ↓
Query FATE output table of homo_lr_0
        ↓
Extract output table namespace and name
        ↓
Download output table by flow data download
        ↓
Read downloaded CSV/meta files
        ↓
Return readable result text to frontend
        ↓
Display in modal or download as local .txt file
```

This requirement makes prediction results easier to inspect and export from the WebApp.

---

### 4.5.5 Prediction Record Update

The system should allow users to update notes for a prediction record.

This is useful for adding experiment comments or result descriptions.

---

### 4.5.6 Prediction Record Deletion

The system should allow users to delete prediction records.

When a prediction record is deleted, the system should also remove generated prediction scripts from the remote server if they were created by the WebApp.

---

## 4.6 Dashboard Requirements

The dashboard should provide a summary of the system and recent experiment records.

The dashboard should show:

```text
FATE Flow connection status
recent training job count
recent prediction job count
recent job list
job status
role
party ID
execution time
```

The dashboard should refresh automatically so that users can monitor the system without manually reloading the page.

The system should also attempt to check or start the FATE Flow process when necessary.

---

## 4.7 API Requirements

The system should provide structured backend APIs for frontend interaction.

The APIs should cover:

```text
authentication
page rendering
dataset management
FATE status checking
training management
job querying
model management
prediction management
data table management
```

The API responses should be JSON-based for frontend JavaScript to process.

For request bodies, the system should use schema classes to define and validate expected input fields.

---

## 4.8 Security Requirements

Security is an important requirement because the system stores user accounts, remote server credentials, and environment configuration.

The system should satisfy the following security requirements:

```text
1. WebApp login passwords must not be stored in plain text.
2. Remote server passwords must not be stored in plain text.
3. Remote server passwords must be encrypted before saving.
4. JWT access tokens should be stored in HTTP-only cookies.
5. Protected pages and APIs should require authentication.
6. The real `.env` file is not committed to GitHub.
7. .env.example is provided as a safe configuration template.
8. Sensitive values such as APP_SECRET_KEY and APP_FERNET_KEY should remain private.
```

The system should also warn users that changing `APP_FERNET_KEY` will make previously encrypted server passwords impossible to decrypt.

---

## 4.9 Usability Requirements

The system should be easier to use than the original manual FATE workflow.

Usability requirements include:

```text
1. Users should be able to operate the system from a browser.
2. Users should not need to manually enter Docker commands.
3. Users should not need to manually execute FATE Flow commands.
4. Common operations should be available through buttons and forms.
5. Job status and logs should be displayed clearly.
6. Dataset, model, and prediction records should be shown in tables.
7. Error messages should be shown when operations fail.
```

The main purpose is to reduce the learning cost for operating FATE.

---

## 4.10 Maintainability Requirements

The system should be organized in a modular structure so that future extensions are easier.

The project should separate:

```text
routers
services
models
schemas
templates
static files
configuration
database setup
```

Each module should have a clear responsibility.

For example:

```text
routers handle HTTP requests
services handle business logic and remote execution
models define database tables
schemas define request data structures
templates define page layouts
app.js handles frontend dynamic behavior
```

This layered design makes the project easier to debug, maintain, and extend.

---

## 4.11 Reliability Requirements

The system should handle failures in remote execution and database operations as safely as possible.

Reliability requirements include:

```text
1. If file upload to FATE fails, the database record should be cleaned.
2. If remote file writing fails, the database record should not remain as a false success.
3. If a dataset is deleted, related FATE tables and server files should also be deleted.
4. If a training or prediction job fails, the system should return stdout, stderr, and task error information.
5. The system should attempt to verify that a FATE table exists after upload.
6. Generated files should follow safe naming patterns to avoid accidental deletion of unrelated files.
```

These requirements help keep the WebApp database, FATE environment, and remote server files consistent.

---

## 4.12 Deployment and GitHub Submission

This project should be suitable for GitHub submission and local testing by other people.

To support this, the project now provides a Docker-based Oracle database setup. Testers can create their own local Oracle database instead of connecting to the original development database.

The real `.env` file is not uploaded to GitHub.

The intended testing workflow is:

```text
Clone the repository
        ↓
Create Python virtual environment
        ↓
Install dependencies
        ↓
Copy .env.example to .env
        ↓
Fill in local secrets and remote FATE server credentials
        ↓
Start Docker Oracle database
        ↓
Run scripts/seed_admin.py
        ↓
Start the WebApp
        ↓
Login with administrator / 123456
```

The administrator account is not distributed inside a pre-filled database volume. Instead, it is created locally by `scripts/seed_admin.py`.

This is safer because the remote FATE server password is not stored in GitHub or inside a shared database image. The password is read from the local `.env` file, encrypted using `APP_FERNET_KEY`, and then saved into the local Docker Oracle database.

The default testing account is:

```text
Account: administrator
Password: 123456
```

This account works after `scripts/seed_admin.py` has been executed successfully.

---

## 4.13 Summary

The requirements of this project focus on building a complete WebApp management layer for a remote standalone FATE environment.

The system should support:

```text
User authentication
        ↓
Dataset upload and FATE registration
        ↓
Training job creation and tracking
        ↓
Model record management
        ↓
Prediction job creation and result query
        ↓
Database, FATE table, and server file cleanup
        ↓
GitHub-ready documentation and configuration
```

---

# 5. System Architecture

The FATE WebApp UI is designed with a layered architecture. The purpose of this design is to separate page rendering, API handling, business logic, database operations, and remote FATE execution.

The overall system can be divided into five main layers:

```text id="6flkea"
Frontend Layer
        ↓
Router Layer
        ↓
Service Layer
        ↓
Database Layer
        ↓
Remote FATE Execution Layer
```

Each layer has a clear responsibility. The frontend provides user interaction. The router layer receives HTTP requests. The service layer handles authentication, encryption, SSH execution, and FATE command logic. The database layer stores WebApp records. The remote execution layer communicates with the FATE environment running inside Docker.

---

## 5.1 Overall Architecture

The system architecture can be summarized as follows:

```text
User Browser
    ↓
Jinja2 Templates + app.js
    ↓
FastAPI Routers
    ↓
Service Layer
    ↓
Local Docker Oracle Database
    ↓
SSH Connection
    ↓
Remote Server
    ↓
Remote FATE Docker Container
    ↓
FATE Runtime Environment
```

The WebApp itself does not directly implement federated learning algorithms. Instead, it acts as a management interface above FATE.

The local Docker Oracle database stores WebApp-side records, such as users, uploaded files, jobs, models, and predictions.

The remote FATE Docker container performs the actual FATE operations, including data upload, training, prediction, job query, and table cleanup.

This architecture separates record management from federated learning execution:

```text
Local Docker Oracle:
    WebApp records and metadata

Remote FATE Docker:
    federated learning execution
```

---

## 5.2 Frontend Layer

The frontend layer is responsible for user interaction.

It consists of:

```text id="90qcrp"
app/templates/
app/static/css/
app/static/js/app.js
```

The HTML pages are rendered by Jinja2 templates. The main pages include:

```text id="ddnuck"
main.html
login.html
register.html
mainpage.html
datapage.html
trainingpage.html
modelpage.html
predictedpage.html
```

The frontend JavaScript file `app.js` is responsible for dynamic behavior after the page is loaded. It calls backend APIs using `fetch()` and updates tables, forms, status messages, modals, and log areas.

For example:

```text id="ebkyk1"
Dashboard page
    ↓
app.js calls /api/fate/dashboard/main-summary
    ↓
Page displays FATE status and recent jobs
```

The frontend does not directly communicate with FATE. All FATE-related operations are sent to the backend APIs.

---

## 5.3 Router Layer

The router layer is implemented using FastAPI routers. It receives HTTP requests from the frontend and calls the corresponding backend logic.

The main router modules are:

| Router File       | Responsibility                                                 |
| ----------------- | -------------------------------------------------------------- |
| `auth.py`         | Login, registration, and logout                                |
| `pages.py`        | HTML page rendering                                            |
| `file_storage.py` | Dataset upload, list, detail, update, delete, and cleanup APIs |
| `fate_api.py`     | FATE status, training, model, prediction, and job APIs         |

The page router mainly returns HTML templates, while the API routers return JSON responses.

Example:

```text id="ueaz56"
GET /training
    ↓
pages.py returns trainingpage.html

POST /api/fate/training/create
    ↓
fate_api.py creates a FATE training job
```

This separation keeps page rendering and business operations independent.

---

## 5.4 Service Layer

The service layer contains the core business logic of the system.

The main service files are:

| Service File             | Responsibility                                                                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| `auth_service.py`        | Password hashing, password verification, JWT token generation, server password encryption/decryption |
| `remote_fate_service.py` | SSH connection, Docker command execution, FATE command execution, dynamic pipeline generation        |
| `fate_client.py`         | Optional FATE Flow SDK client wrapper                                                                |

The most important service is `RemoteFateService`. It hides the complexity of the remote FATE environment. Instead of writing SSH and Docker commands directly in routers, the routers call methods from this service.

For example:

```text id="19pybg"
fate_api.py
    ↓
service.start_training_with_config()
    ↓
remote_fate_service.py
    ↓
SSH + Docker + FATE pipeline execution
```

This design keeps the router files cleaner and makes the remote execution logic reusable.

---

## 5.5 Database Layer

The database layer stores WebApp-side records. It does not replace FATE internal storage. Instead, it records the information needed by the WebApp to manage datasets, jobs, models, and predictions.

In the current version, the database is provided by a local Docker Oracle XE container.

The database container is started by:

```bash
docker compose up -d oracle-db
```

The database is configured in:

```text
app/db.py
```

The connection string is controlled by:

```env
DATABASE_URL=oracle+oracledb://FATE_APP:fate_app_password@127.0.0.1:1521/?service_name=XEPDB1
```

The main SQLAlchemy models are:

| Model | Purpose |
|---|---|
| `AppUser` | Stores WebApp users and encrypted remote server credentials |
| `UploadedFile` | Stores uploaded dataset metadata and FATE table mapping |
| `JobRecord` | Stores training and prediction job records |
| `ModelRecord` | Stores trained model metadata |
| `PredictionRecord` | Stores prediction task records |

The database layer is used by both `file_storage.py` and `fate_api.py`.

Example:

```text
User uploads a dataset
    ↓
UploadedFile record is created in Docker Oracle
    ↓
FATE namespace and table_name are saved
    ↓
Training and prediction modules can reuse this dataset record
```

---

## 5.6 Remote FATE Execution Layer

The remote FATE execution layer is responsible for interacting with the actual FATE environment.

In this project, FATE runs:

```text id="ja196v"
on a remote server
inside a Docker container
with FATE Flow commands and Python pipeline scripts
```

The backend connects to this environment through SSH.

The general remote execution process is:

```text id="7x9pnw"
Backend receives API request
        ↓
RemoteFateService opens SSH connection
        ↓
Backend checks or starts the FATE Docker container
        ↓
Backend executes command inside the container
        ↓
FATE returns stdout, stderr, Job ID, or result data
        ↓
Backend sends response to frontend
```

This layer is used for:

* checking FATE Flow status;
* uploading datasets into FATE;
* creating training jobs;
* querying job logs and metrics;
* creating prediction jobs;
* deleting FATE tables and generated server files.

---

## 5.7 Data Flow of Main Functions

This section summarizes the main data flow of the system.

### 5.7.1 Dataset Upload Flow

```text id="9vqz53"
User uploads CSV file
        ↓
Frontend sends POST /api/files/upload
        ↓
file_storage.py saves file metadata in database
        ↓
RemoteFateService writes file to remote server
        ↓
RemoteFateService uploads dataset to FATE
        ↓
FATE namespace and table_name are saved
        ↓
Frontend refreshes dataset list
```

The current UI supports uploading, listing, viewing details, editing description, deleting datasets, and cleaning related remote files. The backend also contains a file download endpoint, but this function is not emphasized as a main UI feature in the current version.

---

### 5.7.2 Training Flow

```text id="d7vwvj"
User selects training dataset and parameters
        ↓
Frontend sends POST /api/fate/training/create
        ↓
fate_api.py reads UploadedFile record
        ↓
RemoteFateService generates training pipeline script
        ↓
Script runs inside FATE Docker container
        ↓
FATE returns Job ID and model information
        ↓
JobRecord and ModelRecord are saved
        ↓
Frontend displays training result and logs
```

This flow converts a manual FATE training process into a WebApp operation.

---

### 5.7.3 Prediction Flow

```text id="4ab9t5"
User selects model and prediction dataset
        ↓
Frontend sends POST /api/fate/prediction/create
        ↓
fate_api.py reads ModelRecord and UploadedFile
        ↓
RemoteFateService generates prediction script
        ↓
Script runs inside FATE Docker container
        ↓
FATE returns Prediction Job ID
        ↓
PredictionRecord and JobRecord are saved
        ↓
Frontend displays prediction status and result
```

Prediction depends on the pipeline file saved during training. Therefore, the model record must contain the correct generated pipeline path.

---

### 5.7.4 Deletion and Cleanup Flow

```text id="1d36zv"
User deletes a dataset/model/prediction record
        ↓
Backend locates related database record
        ↓
Backend deletes related FATE table or generated server file if applicable
        ↓
Backend deletes local database record
        ↓
Frontend refreshes the corresponding list
```

This flow helps keep the WebApp database, FATE tables, and generated server files consistent.

---

## 5.8 Authentication Flow

Authentication is required for protected pages and APIs.

The login process is:

```text id="fh1jxc"
User submits account and password
        ↓
auth.py queries AppUser
        ↓
auth_service.py verifies password hash
        ↓
JWT access token is generated
        ↓
Token is stored in HTTP-only cookie
        ↓
User accesses protected pages and APIs
```

For remote FATE operations, the system also needs the encrypted remote server password:

```text id="jym31z"
Protected API is called
        ↓
get_current_user verifies token
        ↓
get_fate_service decrypts server password
        ↓
RemoteFateService is created for current user
        ↓
FATE operation is executed remotely
```

This design separates WebApp login authentication from remote server access.

---

## 5.9 Architecture Benefits

The layered architecture provides several benefits:

* **Separation of responsibilities**: templates, routers, services, models, and schemas have different roles.
* **Maintainability**: new functions can be added by extending routers and services.
* **Reusability**: `RemoteFateService` can be reused by dataset, training, model, and prediction APIs.
* **Security**: authentication, password hashing, and credential encryption are handled in dedicated service functions.
* **Consistency**: deletion and cleanup logic reduces mismatch between database records, FATE tables, and server files.
* **Usability**: users can operate FATE through a browser instead of command-line instructions.

---

## 5.10 Summary

The system architecture is designed to bridge a browser-based WebApp and a remote Docker-based FATE environment.

The frontend provides user interaction, FastAPI routers expose pages and APIs, the service layer handles core logic, the database stores WebApp records, and `RemoteFateService` executes FATE operations remotely.

This architecture allows the project to transform a complex command-line FATE workflow into a structured and more user-friendly web-based workflow.

---

# 6. Database Design and Implementation

During the development of this project, There needed a database structure that could record the main objects used by the WebApp. These objects include users, uploaded datasets, FATE jobs, trained models, and prediction records.

I used SQLAlchemy to define the database models. The database connection, session factory, and ORM base class are configured in `app/db.py`. All model classes are placed under `app/models/`.

The main database models are:

```text id="hhmnv1"
AppUser
UploadedFile
JobRecord
ModelRecord
PredictionRecord
```

---

## 6.1 User Table

The user table is represented by `AppUser`.

This table stores WebApp login information and remote server credentials. The important fields include:

```text id="cry6q4"
account
password_hash
server_username
server_password_encrypted
is_active
created_at
updated_at
```

I separated the WebApp password and the remote server password because they have different purposes. The WebApp password is only used for login verification, so it is stored as a hash. The remote server password must be used later for SSH connection, so it is stored in encrypted form.

This design allows the system to authenticate users and also connect to the remote FATE environment on behalf of the current user.

---

## 6.2 Uploaded File Table

The uploaded file table is represented by `UploadedFile`.

This table records datasets uploaded through the WebApp. It stores both file metadata and FATE mapping information.

The key fields include:

```text id="pk8lyk"
file_name
content_type
size_bytes
usage_type
namespace
table_name
description
file_data
created_at
updated_at
```

The field `usage_type` is used to distinguish whether the dataset is used for training or prediction.

The fields `namespace` and `table_name` are especially important because FATE uses them to locate a registered dataset. After a CSV file is uploaded and imported into FATE, the WebApp saves its FATE namespace and table name in this table. Later, the training and prediction modules can reuse this information directly.

---

## 6.3 Job, Model, and Prediction Tables

To track experiments, I created three additional tables.

`JobRecord` is used to store general FATE job information, including both training and prediction jobs.

```text id="emkq64"
job_id
job_type
name
role
party_id
status
source_script
created_at
updated_at
```

`ModelRecord` is used to store trained model information.

```text id="yit6hx"
model_id
name
algorithm
version
description
created_at
```

The `description` field is also used to store additional training information, such as the training job ID, FATE table name, and generated pipeline path.

`PredictionRecord` is used to store prediction task history.

```text id="v6hje8"
prediction_job_id
model_id
model_name
dataset_file_id
dataset_name
status
note
created_at
updated_at
```

With these tables, the WebApp can show previous jobs, trained models, and prediction records without requiring users to manually search FATE logs or command outputs.

---

## 6.4 Database Initialization

The project uses two steps to initialize the database.

The first step is Oracle user initialization. This is handled by the Docker Oracle setup script:

```text
docker/oracle/init/01_create_app_user.sql
```

This script creates the WebApp database user:

```text
FATE_APP / fate_app_password
```

It also grants the required permissions and assigns quota on the `USERS` tablespace.

The second step is WebApp table initialization. In `app/main.py` and `scripts/seed_admin.py`, the project calls:

```python
Base.metadata.create_all(bind=engine)
```

This allows SQLAlchemy to create the required tables based on the model definitions.

The default administrator account is created by:

```bash
python scripts/seed_admin.py
```

This script:

```text
1. connects to Docker Oracle through DATABASE_URL;
2. creates database tables if they do not exist;
3. checks whether administrator already exists;
4. hashes the WebApp login password;
5. encrypts the remote FATE server password;
6. saves the administrator user into APP_USERS.
```

---

# 7. Backend Design and Implementation

The backend is implemented with FastAPI. I divided the backend into routers, services, schemas, models, and dependencies so that each file has a clear responsibility.

The main backend structure is:

```text id="9g1wne"
routers/       HTTP routes and API endpoints
services/      business logic and remote execution
models/        database table definitions
schemas/       request body validation models
dependencies/ shared authentication and service dependencies
```

This structure helped me avoid placing all logic in a single file.

---

## 7.1 Application Entry Point

The application starts from `app/main.py`.

In this file, I:

```text id="l27f1m"
1. create the FastAPI application;
2. import all database models;
3. create database tables;
4. mount the static file directory;
5. register authentication routes;
6. register page routes;
7. register FATE API routes;
8. register file storage routes.
```

This makes `main.py` the central assembly point of the whole application.

---

## 7.2 Authentication Routes

The authentication routes are implemented in `app/routers/auth.py`.

This file provides:

```text id="9qvo65"
GET  /login
POST /login
GET  /register
POST /register
GET  /logout
```

During registration, the backend hashes the WebApp password and encrypts the remote server password. During login, the backend verifies the password and creates an access token.

The access token is stored in an HTTP-only cookie, which is then used to access protected pages and APIs.

---

## 7.3 Page Routes

The page routes are implemented in `app/routers/pages.py`.

These routes return HTML templates, such as:

```text id="pkmsn6"
mainpage.html
datapage.html
trainingpage.html
modelpage.html
predictedpage.html
```

Originally, some pages contained static test data. Later, I removed these static values and changed the design so that pages only provide the basic layout. Real data is now loaded by frontend JavaScript through API calls.

This makes the pages more realistic and avoids showing outdated or fake data.

---

## 7.4 File Storage APIs

The dataset-related APIs are implemented in `app/routers/file_storage.py`.

This file handles:

```text id="etnmwq"
dataset upload
dataset list
dataset detail query
dataset description update
dataset deletion
orphan file cleanup
```

The upload process does more than just save a file. It also writes the file to the remote FATE server and imports it into FATE.

When deleting a dataset, the backend also deletes the related FATE table and generated server files. This was added because I found that deleting only the database record would leave unused files on the server.

---

## 7.5 FATE APIs

The FATE-related APIs are implemented in `app/routers/fate_api.py`.

This file provides API endpoints for:

```text id="hx5vz9"
FATE status checking
dashboard summary
training creation
training logs and metrics
model listing and details
model update and deletion
prediction creation
prediction list and result query
job query
table query
```

The router itself does not directly execute SSH or Docker commands. Instead, it calls `RemoteFateService`, which contains the remote execution logic.

This separation makes the API routes easier to read and maintain.

---

## 7.6 Request Schemas

The request models are defined in `app/schemas/fate.py`.

I used Pydantic models to define request body structures, such as:

```text id="5xdi84"
TrainingCreateRequest
PredictionCreateRequest
JobIdRequest
ModelDetailRequest
ModelUpdateRequest
```

This allows FastAPI to validate request data automatically before executing route logic.

---

# 8. Frontend Design and Implementation

The frontend is implemented using Jinja2 templates, CSS, Bootstrap-style components, and JavaScript.

The frontend is not a separate single-page application. Instead, the backend renders the main HTML pages, and JavaScript dynamically loads data from the backend APIs.

---

## 8.1 Page Layout

The main page templates are stored in `app/templates/`.

The application contains pages for:

```text id="yt4p8n"
login
registration
dashboard
dataset management
training management
model management
prediction management
```

A shared `base.html` template is used to keep the common layout consistent across pages.

---

## 8.2 Dynamic Frontend Logic

Most dynamic frontend behavior is implemented in:

```text id="2ugytl"
app/static/js/app.js
```

This file initializes different functions depending on the current page.

The main frontend initialization functions include:

```text id="7dl76k"
initMainPageDashboard()
initDataPageCrud()
initTrainingPage()
initModelPage()
initPredictionPage()
```

For example, when the dataset page is opened, `app.js` loads the dataset list from:

```text id="zwu4p2"
GET /api/files/list
```

When the training page is opened, it loads training datasets from:

```text id="l0kg19"
GET /api/fate/training/datasets
```

When a user clicks the training button, JavaScript sends a JSON request to:

```text id="bqpsor"
POST /api/fate/training/create
```

This design allows each page to load real backend data after rendering.

---

## 8.3 UI Functions Implemented

The frontend currently supports:

```text
dashboard status display
dataset upload
dataset list display
dataset detail viewing
dataset description editing
dataset deletion
training job creation
training log request
model list display
model detail viewing
model editing
model deletion
prediction job creation
prediction list display
prediction result viewing
prediction result download
prediction note editing
prediction deletion
```

---

# 9. FATE Integration Design

The FATE integration is the most important technical part of this project. Since the FATE environment runs inside a Docker container on a remote server, the WebApp cannot simply call FATE as a local library.

To solve this, I implemented a service layer named `RemoteFateService`.

---

## 9.1 Remote Execution Method

The basic idea is:

```text id="q5p1b5"
FastAPI backend
        ↓
SSH connection
        ↓
remote server
        ↓
Docker container
        ↓
FATE environment
        ↓
FATE command or Python pipeline script
```

The service first connects to the remote server through SSH. Then it checks whether the FATE container is running. After that, it executes commands inside the container.

Each command is executed after entering the FATE root directory and loading the FATE environment.

This avoids the need for users to manually run:

```bash id="8r6s3l"
docker exec -it standalone_fate bash
source bin/init_env.sh
flow job query ...
```

---

## 9.2 Dataset Upload to FATE

When a user uploads a dataset, the WebApp performs several steps automatically.

```text id="qxrl9b"
1. Save the uploaded file record in the database.
2. Write the file to the remote server.
3. Prepare a FATE-compatible CSV file.
4. Generate a FATE upload configuration file.
5. Run flow data upload inside the FATE container.
6. Wait for the upload job to finish.
7. Save the FATE namespace and table name in the database.
```

One practical issue I met was that the FATE HomoLR environment required a `match_id` column. The original CSV files may only contain an `id` column. To solve this, I added a preprocessing step that creates a new CSV file with a `match_id` column copied from `id`.

---

## 9.3 Training Integration

For training, the backend dynamically generates a Python training pipeline script.

The script is generated based on:

```text id="j0kznb"
selected dataset
FATE namespace
FATE table name
selected algorithm
training parameters
role
party ID
```

Then the script is executed inside the FATE Docker container.

After execution, the backend extracts:

```text id="xdl09x"
job ID
model ID
model version
generated pipeline path
```

The system then creates a `JobRecord` and a `ModelRecord` in the database.

The current implementation mainly supports Homo Logistic Regression. The design can be extended later to support more algorithms.

---

## 9.4 Prediction Integration

Prediction uses the model record created during training.

The backend reads the selected model and prediction dataset from the database, extracts the saved pipeline path, and generates a prediction script.

The prediction workflow is:

```text
1. Load the saved training pipeline.
2. Deploy the trained component.
3. Connect a prediction dataset through Reader.
4. Run the prediction pipeline.
5. Extract the prediction Job ID.
6. Save PredictionRecord and JobRecord.
```

This allows users to start prediction tasks from the WebApp without manually writing prediction scripts.

After the prediction job is completed, the WebApp can also query and download the prediction result.

The result retrieval workflow is:

```text
Prediction Job ID
        ↓
flow output query-data-table -j <job_id> -r guest -p 9999 -tn homo_lr_0
        ↓
Extract result table namespace and name
        ↓
flow data download --namespace <namespace> --name <name> --path <output_path>
        ↓
Read downloaded files such as data/0.csv and data/0.meta
        ↓
Return readable prediction result text to the frontend
```

The Predicted Page provides two result-related actions:

```text
View:
    display the prediction result in a modal window

Download:
    download the prediction result as a local text file
```

---

## 9.5 Cleanup Integration

A key improvement in this project is the cleanup logic.

At first, deleting database records did not remove files generated on the remote server. This caused file accumulation and increasing IDs during repeated testing.

To solve this, I added cleanup functions to remove:

```text id="twb2c5"
uploaded temporary files
processed CSV files
generated upload configuration files
generated training scripts
generated prediction scripts
generated pipeline files
FATE tables
```

This makes the database, FATE environment, and server files more consistent.

---

# 10. Security Design

Security was considered mainly in three areas:

```text id="de3293"
user login security
remote server credential protection
GitHub environment file protection
```

---

## 10.1 WebApp Password Protection

The WebApp login password is not stored as plain text.

During registration, the password is processed by `hash_password()` in `auth_service.py`. During login, the input password is verified by `verify_password()`.

This means the database stores only the password hash.

---

## 10.2 Remote Server Password Encryption

The remote server password must be recoverable because the backend needs it to connect to the remote server through SSH.

For this reason, I did not hash the remote server password. Instead, I encrypted it using Fernet encryption.

The encrypted password is stored in the `server_password_encrypted` field of the `AppUser` table.

When the user calls a FATE-related API, the backend decrypts the server password and creates a `RemoteFateService` instance for that user.

A very important limitation is that the same `APP_FERNET_KEY` must be used. If this key is changed, previously encrypted server passwords cannot be decrypted.

---

## 10.3 Access Token and Protected Routes

After login, the backend creates a JWT access token. This token is stored in an HTTP-only cookie.

Protected pages and APIs use authentication dependencies to check the current user.

The protected routes include:

```text id="ypw137"
main page
dataset page
training page
model page
prediction page
file APIs
FATE APIs
```

If the user is not authenticated, page routes redirect to the login page, and API routes reject the request.

---

## 10.4 Environment File Protection

The project uses a `.env` file to store local configuration and sensitive values.

The `.env` file may contain:

```text
Docker Oracle database password
DATABASE_URL
APP_SECRET_KEY
APP_FERNET_KEY
remote FATE server host
remote FATE server username
remote FATE server password
FATE runtime settings
```

Therefore, `.env` must not be uploaded to GitHub.

The repository provides `.env.example` as a safe template. Testers should copy it to `.env` and fill in their own local values.

The intended usage is:

```text
.env           local real configuration, not committed
.env.example  public template, committed to GitHub
```

The administrator account is created locally by `scripts/seed_admin.py`. The script reads the remote FATE server credentials from `.env`, encrypts the remote server password, and stores it in the local Docker Oracle database.

This is to avoid storing real server credentials in GitHub or in a shared database image.

---

## 10.5 Security Summary

The security design is simple but necessary for this project.

The main protections are:

```text id="q22b9m"
WebApp password hashing
remote server password encryption
JWT access token authentication
HTTP-only cookie storage
protected pages and APIs
.env exclusion from GitHub
.env.example as public template
```

These mechanisms are used for the project testing environment, although a production system would need stronger measures such as HTTPS enforcement, role-based access control, audit logs, and stricter password policies.

---

# 11. Main Functional Workflows

This chapter summarizes the main workflows implemented in the FATE WebApp UI. These workflows describe how the frontend, backend, database, and remote FATE environment work together during actual use.

---

## 11.1 User Login Workflow

The login workflow starts when a user opens the login page and submits an account and password.

```text
User opens /login
        ↓
User submits account and password
        ↓
auth.py queries AppUser from the database
        ↓
auth_service.py verifies the password hash
        ↓
JWT access token is generated
        ↓
Token is stored in an HTTP-only cookie
        ↓
User is redirected to the main dashboard
```

The WebApp password is never stored as plain text. During login, the system compares the input password with the stored password hash.

After login, the access token is used to verify protected pages and APIs.

---

## 11.2 User Registration Workflow

During registration, the user provides both WebApp login information and remote server credentials.

```text
User opens /register
        ↓
User enters WebApp account and password
        ↓
User enters remote server username and password
        ↓
WebApp password is hashed
        ↓
Remote server password is encrypted
        ↓
User record is saved into APP_USERS
        ↓
JWT access token is generated
        ↓
User is redirected to the dashboard
```

This workflow allows the system to authenticate the WebApp user and later connect to the remote FATE server for that user.

---

## 11.3 Dataset Upload Workflow

Dataset upload is one of the core workflows of the system.

```text
User selects a CSV file
        ↓
User selects usage type: train or predict
        ↓
Frontend sends POST /api/files/upload
        ↓
Backend saves file metadata into UploadedFile
        ↓
Backend writes the file to the remote server
        ↓
Backend prepares a FATE-compatible CSV file
        ↓
Backend generates FATE upload configuration
        ↓
Backend runs flow data upload inside the FATE container
        ↓
FATE creates a table with namespace and table_name
        ↓
Database record is updated
        ↓
Frontend refreshes the dataset list
```

The uploaded file is linked with FATE by storing its `namespace` and `table_name` in the database.

The current UI mainly supports dataset upload, list display, detail viewing, description editing, deletion, and cleanup.
---

## 11.4 Training Workflow

The training workflow starts from the training page.

```text
User selects a training dataset
        ↓
User selects algorithm and parameters
        ↓
Frontend sends POST /api/fate/training/create
        ↓
Backend reads UploadedFile record
        ↓
Backend gets FATE namespace and table_name
        ↓
RemoteFateService generates a training pipeline script
        ↓
Script is executed inside the FATE Docker container
        ↓
FATE returns Job ID and model information
        ↓
Backend saves JobRecord
        ↓
Backend saves ModelRecord
        ↓
Frontend displays Job ID, model information, stdout, and logs
```

This workflow hides the manual FATE training commands from the user. The user only needs to select a dataset and start training from the WebApp.

The current implementation mainly supports Homo Logistic Regression.

---

## 11.5 Training Log and Status Workflow

After creating a training job, the user can check logs or check status.

```text
User requests logs or status
        ↓
Frontend sends Job ID to backend
        ↓
Backend executes FATE Flow query/log command
        ↓
FATE returns status or log output
        ↓
Backend returns result to frontend
        ↓
Frontend displays the output
```

This is useful for debugging failed jobs and confirming whether a task is running, successful, or failed.

---

## 11.6 Model Management Workflow

After training, the WebApp saves trained model information into `ModelRecord`.

```text
Training job is submitted successfully
        ↓
Backend extracts model_id and model_version
        ↓
Backend creates ModelRecord
        ↓
Model page loads records from database
        ↓
User can view, edit, or delete model records
```

The model record stores not only basic metadata but also training-related information, such as the generated pipeline path. This path is required later for prediction.

---

## 11.7 Prediction Workflow

The prediction workflow uses both a trained model and a prediction dataset.

```text
User selects a trained model
        ↓
User selects a prediction dataset
        ↓
Frontend sends POST /api/fate/prediction/create
        ↓
Backend reads ModelRecord
        ↓
Backend reads UploadedFile
        ↓
Backend extracts saved pipeline path
        ↓
RemoteFateService generates prediction script
        ↓
Script is executed inside the FATE Docker container
        ↓
FATE returns prediction Job ID
        ↓
Backend saves PredictionRecord
        ↓
Backend saves JobRecord
        ↓
Frontend refreshes prediction list
```

Prediction depends on the training pipeline file generated during the training stage. If the pipeline file is missing, the prediction task cannot be created successfully.

After the prediction job succeeds, the user can view or download the result from the Predicted Page.

```text
User clicks View or Download
        ↓
Frontend sends POST /api/fate/prediction/result
        ↓
Backend queries FATE output table by prediction Job ID
        ↓
Backend obtains output table namespace and name
        ↓
Backend downloads the result table from FATE
        ↓
Backend reads the downloaded CSV/meta files
        ↓
Frontend displays the result or downloads it as a local text file
```

This workflow turns the original manual prediction result retrieval process into a WebApp operation.

---

## 11.8 Deletion and Cleanup Workflow

A key workflow in this project is synchronized deletion.

At first, deleting records only from the database caused files to remain on the remote server. To solve this, deletion was extended to include the database, FATE tables, and generated server files.

```text
User deletes a dataset
        ↓
Backend finds UploadedFile record
        ↓
Backend deletes related FATE table
        ↓
Backend deletes uploaded and generated server files
        ↓
Backend deletes database record
        ↓
Frontend refreshes dataset list
```

For models and predictions, the system also attempts to delete related generated pipeline files or prediction scripts.

This workflow improves consistency between the WebApp database and the remote FATE environment.

---

# 12. Testing and Validation

This chapter describes how the system was tested during development. The goal of testing was to verify that each module works correctly and that the complete workflow can be executed from the browser.

---

## 12.1 Authentication Test

The authentication module was tested with both successful and failed login attempts.

Test cases included:

| Test Case                               | Expected Result                                 |
| --------------------------------------- | ----------------------------------------------- |
| Open login page                         | Login page is displayed                         |
| Login with correct account and password | User enters dashboard                           |
| Login with wrong password               | Error message is shown                          |
| Logout                                  | Token is removed and user returns to login page |
| Access protected page without login     | User is redirected to login page                |

The test administrator account was also used for shared testing:

```text
Account: administrator
Password: 123456
```

This account is created locally by running `scripts/seed_admin.py` after Docker Oracle and `.env` have been configured.

The administrator account does not depend on a shared pre-filled database. Instead, each tester can create the account in their own local Docker Oracle database.

---

## 12.2 Dataset Upload Test

The dataset upload function was tested by uploading CSV files for both training and prediction.

Test cases included:

| Test Case                | Expected Result                                                     |
| ------------------------ | ------------------------------------------------------------------- |
| Upload training CSV      | File is saved and imported into FATE                                |
| Upload prediction CSV    | File is saved with `predict` usage type                             |
| View dataset list        | Uploaded files are displayed                                        |
| View dataset details     | Local metadata and FATE metadata are shown                          |
| Edit dataset description | Description is updated in database                                  |
| Delete dataset           | Database record, FATE table, and generated server files are removed |

During testing, I also checked whether uploaded files remained on the remote server after deletion. This test helped identify and solve the server file cleanup issue. And several methods were developed to specifically clear some redundant files left over from the initial testing.

---

## 12.3 Training Test

Training was tested through the WebApp training page.

Test cases included:

| Test Case              | Expected Result                             |
| ---------------------- | ------------------------------------------- |
| Load training datasets | Datasets with `train` usage type are listed |
| Create training task   | FATE training job is submitted              |
| Extract Job ID         | Job ID is returned and displayed            |
| Save job record        | New JobRecord is created                    |
| Save model record      | New ModelRecord is created                  |
| Request training logs  | Logs are returned from FATE                 |
| Query training status  | Status is displayed correctly               |

The main training algorithm tested was Homo Logistic Regression.

The training test verified that the WebApp could generate a pipeline script, execute it inside the FATE container, extract the job information, and save records into the database.

---

## 12.4 Model Management Test

The model management page was tested after training jobs created model records.

Test cases included:

| Test Case           | Expected Result                                                      |
| ------------------- | -------------------------------------------------------------------- |
| Load model list     | Model records are displayed                                          |
| View model detail   | Local and FATE model information is shown                            |
| Edit model metadata | Name, version, and description are updated                           |
| Delete model        | Local record and generated pipeline file are deleted when applicable |

This test confirmed that trained models can be reused later for prediction tasks.

---

## 12.5 Prediction Test

Test cases included:

| Test Case                  | Expected Result                                      |
| -------------------------- | ---------------------------------------------------- |
| Load prediction models     | Available models are listed                          |
| Load prediction datasets   | Datasets with `predict` usage type are listed        |
| Create prediction task     | FATE prediction job is submitted                     |
| Save prediction record     | PredictionRecord is created                          |
| Query prediction status    | Prediction status is updated correctly               |
| View prediction result     | Prediction result is displayed in the WebApp         |
| Download prediction result | Prediction result is downloaded as a local text file |
| Edit prediction note       | Note is updated                                      |
| Delete prediction record   | Record and generated prediction script are deleted   |

During testing, I found that `flow output query-data-table` only returned the prediction output table location, not the real prediction rows.

For example, it returned a namespace and table name for the prediction output table:

```text
namespace=<prediction_job_id>_homo_lr_0
name=<generated_output_table_name>
```

Therefore, I added an additional backend step to download the real result table by using:

```bash
flow data download --namespace <namespace> --name <name> --path <output_path>
```

After downloading the output table, the backend reads the generated files, such as:

```text
data/0.csv
data/0.meta
```

The frontend can then display the result through the **View** button or save it locally through the **Download** button.

This test verified that the prediction workflow can reuse the trained pipeline generated during training and that the prediction result can be retrieved and exported from the WebApp.

---

## 12.6 Dashboard Test

The dashboard was tested to confirm that it can display the current system status and recent jobs.

Test cases included:

| Test Case         | Expected Result                           |
| ----------------- | ----------------------------------------- |
| Open dashboard    | Dashboard page is displayed               |
| Check FATE status | Connected or disconnected status is shown |
| Load recent jobs  | Recent jobs are displayed in table        |
| Refresh dashboard | Data is updated                           |
| Auto-refresh      | Dashboard updates periodically            |

The dashboard test also helped verify whether FATE Flow was running correctly.

---

## 12.7 GitHub, Docker Oracle, and Environment Configuration Test

Because the project needed to be uploaded to GitHub, I tested whether the repository could be cloned and configured again using a local Docker Oracle database.

The test steps included:

```text
1. Clone the repository.
2. Create a Python virtual environment.
3. Install requirements.
4. Copy .env.example to .env.
5. Fill in APP_SECRET_KEY, APP_FERNET_KEY, and remote FATE server credentials.
6. Start Docker Oracle with docker compose.
7. Wait until the Oracle container becomes healthy.
8. Run scripts/seed_admin.py to create the administrator account.
9. Start the WebApp with uvicorn.
10. Log in using administrator / 123456.
```

This confirmed that the project can be reused without connecting to the original external database.

The Docker Oracle database provides a reproducible local database environment, while the remote FATE server configuration is still required for actual FATE operations.

---

# 13. Problems Encountered and Solutions

During development, several practical problems were encountered. This chapter summarizes the main problems and how they were solved.

---

## 13.1 Uploaded Files Remained on the Server After Database Deletion

### Problem

During testing, I found that deleting a dataset from the database did not delete the corresponding files on the FATE server. As a result, uploaded CSV files and generated configuration files remained in the server directory.

This caused server file accumulation and made repeated testing messy.

### Solution

I extended the deletion logic in `file_storage.py` and `remote_fate_service.py`.

When a dataset is deleted, the system now attempts to delete:

```text
database UploadedFile record
FATE table
uploaded temporary CSV file
processed CSV file with match_id
generated upload JSON file
generated training script
generated prediction script
related helper scripts
```

I also added an orphan cleanup function that compares active database file IDs with files on the server and removes WebApp-generated files that no longer belong to existing records.

---

## 13.2 Dataset ID Kept Increasing After Repeated Uploads

### Problem

When files were uploaded and deleted repeatedly, the database ID continued to increase. This is normal database behavior, but it became confusing when old server files were still present.

The real problem was not the increasing ID itself, but the mismatch between database records and server files.

### Solution

Instead of trying to reset database IDs, I focused on cleaning the related server files properly.

The final solution was:

```text
keep database ID behavior unchanged
use file ID to generate unique table names
delete server files when database record is deleted
provide orphan cleanup for old generated files
```

This made repeated testing cleaner and safer.

---

## 13.3 FATE Web Entry or Path Enumeration Returned 404

### Problem

During the service exploitation and WebApp connection stage, some paths returned `404 Not Found`. At one point, all tested paths appeared to return 404, which made it unclear where the actual FATE or WebApp entry was.

### Solution

I separated the problem into two parts:

```text
WebApp page routes
FATE backend service routes
```

For the WebApp, I confirmed that FastAPI page routes such as `/`, `/data`, `/training`, `/model`, and `/predicted` were registered in `pages.py` and included in `main.py`.

For FATE, I stopped relying on random web path enumeration and instead used controlled backend service methods and FATE Flow commands through `RemoteFateService`.

This made the system less dependent on manually finding web paths and more dependent on verified backend execution.

---

## 13.4 Chrome DevTools `.well-known` 404 Messages

### Problem

While running the WebApp locally, the terminal sometimes showed messages such as:

```text
GET /.well-known/appspecific/com.chrome.devtools.json 404 Not Found
```

At first, this looked like a possible backend error.

### Solution

I identified that this request was generated by Chrome DevTools and was not part of the WebApp logic.

It did not affect the application, because the main page and API requests were still working. Therefore, I treated it as harmless browser behavior and focused only on actual application routes and API errors.

---

## 13.5 Page Kept Loading Because Static Data and Real API Data Were Mixed

### Problem

Some pages originally contained static test data in `pages.py`. Later, when real backend APIs were added, the frontend needed to load actual data dynamically.

This caused confusion because some displayed values were not real database or FATE data.

### Solution

I removed the static demonstration data from `pages.py`.

The page routes now mainly provide page layout and basic context. Real data is loaded by `app.js` through APIs such as:

```text
/api/fate/dashboard/main-summary
/api/files/list
/api/fate/training/datasets
/api/fate/models/list
/api/fate/prediction/list
```

This made the UI more consistent with the real backend state.

---

## 13.6 FATE Required `match_id` in Uploaded CSV Files

### Problem

During dataset upload and training tests, the original CSV files only contained an `id` column. However, the FATE HomoLR environment required a `match_id` column.

Without this column, the FATE upload or training process could fail.

### Solution

I added a preprocessing step in `RemoteFateService`.

The system now checks the uploaded CSV. If `match_id` does not exist, it creates a new processed CSV file where `match_id` is copied from the `id` column.

Example:

```csv
id,feature1,feature2,label
1,0.5,1.2,0
2,0.8,2.1,1
```

is converted internally to:

```csv
id,match_id,feature1,feature2,label
1,1,0.5,1.2,0
2,2,0.8,2.1,1
```

This made the uploaded datasets compatible with the current FATE HomoLR pipeline.

---

## 13.7 Extracting Job ID from FATE Output Was Unstable

### Problem

FATE command outputs were not always in the same format. Sometimes the Job ID appeared in JSON, and sometimes it appeared in plain text.

This made it difficult to reliably save job records.

### Solution

I implemented output parsing methods in `RemoteFateService`.

The service attempts to extract Job ID from:

```text
JSON fields
text patterns
common FATE output formats
long numeric Job ID strings
```

This improved the reliability of training and prediction job creation.

---

## 13.8 Prediction Required Saved Pipeline File

### Problem

Prediction could not be started using only the model ID. The system also needed the pipeline file generated during training.

If the pipeline path was missing from the model record, prediction failed.

### Solution

During training, I saved the generated pipeline path into the `ModelRecord.description` field.

During prediction, the backend extracts this path and uses it to load the trained pipeline.

Although this solution works, there should be better solutions available that can be utilized.

---

## 13.9 Prediction Result Could Not Be Displayed or Downloaded Directly

### Problem

After a prediction job was successfully created, the WebApp database stored the prediction record and the prediction Job ID. The prediction status was also shown as successful.

However, clicking the **View** or **Download** button failed to return the actual prediction result.

At first, the backend only executed:

```bash
flow output query-data-table -j <prediction_job_id> -r guest -p 9999
```

Later, I found that for the current prediction pipeline, the correct component name should be:

```text
homo_lr_0
```

So the output table query should be:

```bash
flow output query-data-table -j <prediction_job_id> -r guest -p 9999 -tn homo_lr_0
```

This command did not directly return the prediction rows. It only returned the output table location, including:

```text
namespace
name
```

For example:

```text
namespace=<prediction_job_id>_homo_lr_0
name=<generated_output_table_name>
```

The real prediction result was stored inside this FATE output table.

### Solution

I updated the prediction result retrieval logic in `RemoteFateService`.

The new process is:

```text
1. Query the prediction output table from homo_lr_0.
2. Extract the output table namespace and name.
3. Use flow data download to export the FATE output table.
4. Read the downloaded CSV/meta files.
5. Return the readable text to the frontend.
```

The backend now executes a workflow similar to:

```bash
flow output query-data-table -j <prediction_job_id> -r guest -p 9999 -tn homo_lr_0
flow data download --namespace <namespace> --name <name> --path ./output/prediction_<prediction_job_id>
```

Then it reads the downloaded files such as:

```text
data/0.csv
data/0.meta
```

After this change, the **View** button can display the prediction result in the browser, and the **Download** button can download the prediction result as a local text file.

This solved the problem where the database contained a prediction record but the WebApp could not show the actual prediction output.

---

## 13.10 `.env` and GitHub Security Issue

### Problem

The project needed to be uploaded to GitHub, but the `.env` file contains sensitive values such as database connection string, application secret key, Fernet key, and remote server configuration.

Uploading `.env` would be unsafe.

In the earlier version, testing also depended on connecting to the original existing database. This was inconvenient because other testers could not easily reproduce the same environment.

### Solution

I configured `.gitignore` to exclude real environment files:

```gitignore
.env
*.env
!.env.example
```

Then I created `.env.example` as a public template.

To make testing easier, I migrated the WebApp database to Docker Oracle. Testers can now start a local Oracle XE database with Docker Compose and then run:

```bash
python scripts/seed_admin.py
```

This creates the default administrator account locally:

```text
Account: administrator
Password: 123456
```

The remote FATE server password is read from the local `.env` file, encrypted with `APP_FERNET_KEY`, and stored in the local Docker Oracle database.

This avoids committing real credentials or a pre-filled database to GitHub.

---

## 13.11 Summary of Problems and Solutions

The main problems encountered during the project were practical integration issues rather than only programming syntax issues.

Most of them came from connecting the WebApp with a real remote FATE environment.

The most important solutions were:

```text
encapsulating SSH and Docker commands in RemoteFateService
synchronizing database deletion with FATE and server file deletion
adding match_id preprocessing for CSV files
removing static page data and using real API data
protecting .env before GitHub submission
migrating the WebApp database to Docker Oracle for reproducible testing
using scripts/seed_admin.py to create the administrator account locally
improving Job ID extraction from FATE output
adding prediction result retrieval and local download support
```

These solutions made the project more stable, easier to test, and more suitable for final submission.

---

# 14. Limitations

Although the FATE WebApp UI implements a complete basic workflow for dataset management, training, model management, and prediction, the current version still has several limitations. These limitations are mainly related to algorithm support, performance, deployment complexity, remote environment dependency, and incomplete advanced features.

---

## 14.1 Limited Algorithm Support

The current implementation mainly supports one training algorithm:

```text
Homo Logistic Regression / HomoLR
```

Although the frontend and backend structure are designed to allow algorithm selection, the dynamic pipeline generation is currently built mainly around HomoLR.

This means that the system does not yet provide full support for other FATE algorithms such as:

```text
Hetero Logistic Regression
SecureBoost
Neural Network models
Linear Regression
Other federated learning components
```

To support more algorithms, the backend pipeline generation logic in `RemoteFateService` needs to be extended.

---

## 14.2 Metrics Function Is Not Fully Implemented

The current system has API structure for querying training metrics, but metric display is not fully implemented in the UI.

The backend can call FATE metric-related commands, but the frontend does not yet provide a complete visualized metrics panel.

As a result, users cannot currently view training metrics such as:

```text
accuracy
AUC
loss
precision
recall
```

in a clear chart-based or table-based interface.

This is one of the important missing functions in the current version.

---

## 14.3 Slow Operation Response

Some operations are relatively slow, especially:

```text
dataset upload
FATE data registration
training job creation
prediction job creation
log query
status query
cleanup operations
```

This is because these operations depend on several remote steps:

```text
FastAPI backend
        ↓
SSH connection
        ↓
remote server command execution
        ↓
Docker container execution
        ↓
FATE Flow command execution
        ↓
return stdout and stderr
```

Each step adds extra latency. Therefore, the WebApp response time is slower than a purely local application.

---

## 14.4 Strong Network Dependency

The system relies heavily on network connectivity.

The backend must be able to connect to the remote server through SSH. If the network is unstable, the following operations may fail:

```text
checking FATE Flow status
uploading datasets
creating training jobs
creating prediction jobs
querying logs
deleting server files
```

This means the system is not fully independent. Its reliability depends on the availability of the remote server, SSH connection, Docker container, and FATE services.

---

## 14.5 Setup Still Requires Docker and Remote FATE Configuration

The project is easier to test than before because it now provides a Docker Oracle database. Testers no longer need access to the original external database.

However, the setup is still more complex than a normal standalone WebApp because testers still need:

```text
Docker Desktop
Oracle XE image access
Python environment
required dependencies
local .env configuration
remote FATE server access
valid SSH username and password
network connection to the remote server
```

The local Docker Oracle database solves the database reproducibility problem, but it does not remove the dependency on the remote FATE environment.

---

## 14.6 Dependency on the Existing Remote FATE Environment

The WebApp is closely connected to the current remote FATE environment.

Several configurations are environment-specific, such as:

```text
FATE_CONTAINER
FATE_ROOT
remote server path
generated script location
FATE Flow command behavior
required CSV format
role and party ID
```

If the FATE environment changes, some backend service functions may need to be adjusted.

For example, if the FATE root path or Docker container name is different, the `.env` configuration and remote execution commands must be updated.

---

## 14.7 Model Deletion Is Not a Complete FATE Model Deletion

When deleting a model from the WebApp, the system deletes the local `ModelRecord` and tries to delete the generated pipeline `.pkl` file.

However, this does not necessarily remove all internal FATE model storage files.

Therefore, the current model deletion function should be understood as:

```text
delete local model record
delete WebApp-generated pipeline file if applicable
```

rather than a complete cleanup of all FATE internal model artifacts.

---

## 14.8 Prediction Depends on Saved Pipeline File

The prediction workflow depends on the training pipeline file generated during training.

If the pipeline `.pkl` file is deleted, moved, or missing, prediction cannot be created successfully even if the model record still exists in the database.

This creates a dependency between:

```text
ModelRecord
generated pipeline file
remote server file path
prediction pipeline generation
```

---

## 14.10 Summary of Limitations

The main limitations of the current system are:

```text
limited algorithm support
metrics display not fully implemented
slow response for remote FATE operations
strong dependency on network and remote server availability
setup still requires Docker Oracle and remote FATE configuration
environment-specific FATE integration
limited multi-user data isolation
incomplete FATE model deletion
prediction dependency on generated pipeline files
prediction result display is still mainly raw text
lack of database migration support
```

These limitations provide clear directions for future improvement.

---

# 15. Future Work

Based on the current limitations, several improvements can be made in future versions of the project. These improvements can make the system more complete, easier to use, and closer to a production-ready FATE management platform.

---

## 15.1 Add Support for More Algorithms

The first important improvement is to support more FATE algorithms.

Future versions can add support for:

```text
Hetero Logistic Regression
SecureBoost
Linear Regression
Neural Network models
Federated feature selection
Other FATE pipeline components
```

To achieve this, the backend should provide different pipeline generation templates for different algorithms.

The frontend should also provide algorithm-specific parameter forms.

---

## 15.2 Complete Metrics Visualization

The metrics function should be fully implemented.

Future improvements may include:

```text
querying metrics from FATE automatically
displaying metrics in tables
drawing loss curves
showing accuracy, AUC, precision, recall
refreshing metrics during training
exporting metrics results
```

This would make the training page more useful for experiment analysis.

---

## 15.3 Improve Operation Speed and User Feedback

Because many operations are slow due to SSH and FATE execution, the UI should provide better feedback.

Possible improvements include:

```text
loading indicators
progress bars
background task processing
asynchronous job submission
status polling
operation timeout messages
better frontend notifications
```

Instead of waiting for long operations synchronously, the backend could submit a task and return immediately with a task ID. The frontend could then poll the task status.

---

## 15.4 Reduce Network Dependency Where Possible

The system cannot completely avoid network dependency because FATE is remote. However, reliability can be improved.

Possible improvements include:

```text
SSH connection retry
timeout handling
connection health check
clearer error messages when remote server is unreachable
automatic FATE Flow restart
remote command execution logs
```

This would make the system more robust under unstable network conditions.

---

## 15.5 Simplify Testing and Deployment for Other Users

The project is easier to test than before because the WebApp database can now run through Docker Oracle.

However, the WebApp itself is still started manually with:

```bash
uvicorn app.main:app --reload
```

Future improvements may include:

```text
containerizing the FastAPI WebApp itself
providing a full Docker Compose setup for both WebApp and Oracle database
providing a mock FATE mode for UI testing
providing setup scripts
providing clearer test data samples
providing example CSV files
providing screenshots and user manual
```

A mock mode would be especially useful because testers could explore the UI without needing access to the real remote FATE server.

A full Docker Compose setup would also make the project easier to run because testers could start both the WebApp and the Oracle database with one command.

---

## 15.6 Add User-Level Data Isolation

To support multiple users properly, the database should add `user_id` fields to important tables, such as:

```text
UploadedFile
JobRecord
ModelRecord
PredictionRecord
```

Then each query should filter records by the current user.

This would prevent one user from seeing or modifying another user's datasets, jobs, models, or prediction records.

---

## 15.7 Improve Model Management

Future model management can be improved in several ways:

```text
store pipeline_path in a separate database field
verify whether the pipeline file exists before prediction
support full FATE model deletion
support model export and download
support model version comparison
support model performance summary
```

This would make the model module more reliable and easier to maintain.

---

## 15.8 Improve Prediction Result Display

The current system can already retrieve prediction results from FATE and download them as a local text file.

However, the prediction result is still displayed mainly as raw text. Future improvements may include:

```text
parsing prediction output into structured HTML tables
showing prediction labels and probabilities in separate columns
supporting CSV download directly
adding result filtering
adding result sorting
adding result visualization
linking prediction results with input dataset rows
showing only the main CSV result instead of all downloaded meta files
```

These improvements would make the prediction page more useful for real analysis.

---

## 15.9 Add Better Error Handling and Logging

The system should provide clearer error handling for users and developers.

Future improvements may include:

```text
structured error messages
separate frontend error panels
backend log files
operation history logs
FATE command history
automatic task error collection
debug mode switch
```

This would make troubleshooting easier when FATE jobs fail.

---

## 15.10 Add Database Migration Support

The project should use Alembic or another migration tool to manage database schema changes.

This would allow the database structure to evolve safely when new fields or tables are added.

For example, future fields such as `user_id` or `pipeline_path` could be added through migration scripts instead of manually modifying the database.

---

## 15.11 Summary of Future Work

The most important future improvements are:

```text
support more algorithms
complete metrics visualization
improve operation speed and frontend feedback
simplify testing for other users
add user-level data isolation
improve model and prediction result management
add better logging and error handling
add database migration support
```

These improvements would make the FATE WebApp UI more complete, stable, and suitable for broader usage beyond the current year project environment.

---

# 16. Conclusion

This year project designed and implemented **FATE WebApp UI**, a web-based management system for operating a remote standalone FATE federated learning environment. The main purpose of the project was to reduce the complexity of using FATE through command-line operations and provide a clearer browser-based workflow for dataset management, training, model management, prediction, and job monitoring.

During the development process, the system was built with a layered architecture. The frontend uses Jinja2 templates, CSS, and JavaScript to provide interactive pages. The backend uses FastAPI to provide page routes and API endpoints. SQLAlchemy is used to manage database models and records. The service layer, especially `RemoteFateService`, connects the WebApp with the remote FATE environment through SSH, Docker, and FATE Flow commands.

The project successfully implemented the main workflow of a FATE experiment:

```text
User login
        ↓
Dataset upload
        ↓
FATE table registration
        ↓
Training job creation
        ↓
Model record management
        ↓
Prediction job creation
        ↓
Job status, logs, and result checking
        ↓
Database, FATE table, and server file cleanup
```

A key achievement of the project is that it hides many repeated manual operations from the user. Instead of manually logging into the remote server, entering the Docker container, loading the FATE environment, and executing `flow` commands, users can complete the main operations through the WebApp interface.

Another important achievement is the integration between the WebApp database and the remote FATE environment. Uploaded datasets are not only stored as local database records, but are also imported into FATE with corresponding namespaces and table names. Training jobs generate both job records and model records. Prediction jobs generate prediction records and can be tracked from the WebApp. Deletion functions were also improved so that database records, FATE tables, and generated server files can be cleaned more consistently.

Security was also considered in the implementation. WebApp login passwords are stored as hashes, while remote server passwords are encrypted before being saved in the database. JWT access tokens are used for authentication, and sensitive configuration values are stored in `.env` rather than committed to GitHub. The project also provides `.env.example` and README instructions to support safer project sharing and testing.

During the project, several practical problems were encountered and solved. These included remote FATE command execution, server file residue after database deletion, FATE CSV format requirements, inconsistent Job ID extraction, static test data in pages, GitHub environment file protection, and remote/local version conflicts. Solving these issues helped make the system more stable and closer to a usable project.

Another improvement added was the prediction result download function. Initially, the WebApp could save prediction records and prediction Job IDs, but it could not directly show the real prediction output because FATE returned only the output table location. I solved this by adding a backend workflow that queries the output table of `homo_lr_0`, downloads the result table with `flow data download`, reads the downloaded CSV/meta files, and returns the result to the frontend. As a result, users can now view prediction results in the WebApp and download them locally as text files.

The last change was replacing the external database dependency with a Docker Oracle database. In the earlier version, testing depended on connecting to the original database and using the original environment configuration. After the change, testers can start a local Oracle XE container, configure their own `.env` file, run `scripts/seed_admin.py`, and create the default administrator account locally. This improves the reproducibility of the project and makes GitHub-based testing more practical.

However, the current system still has limitations. The algorithm support is mainly limited to Homo Logistic Regression, the metrics visualization function is not fully implemented, remote operations may respond slowly, and the system depends strongly on network availability and the remote FATE server. In addition, testing the project on another machine still requires the correct `.env` file, database access, and FATE environment configuration.

Overall, this project provides a complete foundation for a WebApp-based FATE experiment management system. It demonstrates how a complex command-line federated learning workflow can be transformed into a more structured and user-friendly web application. Although further improvements are still needed, the implemented system successfully meets the main goals of the year project and provides a clear direction for future extension.