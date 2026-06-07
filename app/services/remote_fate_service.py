import json
import re
import shlex
import base64
import paramiko
import time
from app.config import settings

# The WebApp backend remotely controls the actuators of FATE.
class RemoteFateService:
    
    # This constructor mainly reads the configuration of the remote server and the FATE container.
    def __init__(
        self,
        server_username: str | None = None,
        server_password: str | None = None
    ):
        self.host = settings.GRACE_HOST
        self.port = settings.GRACE_PORT

        # First, use the bound server account and password of the currently logged-in user.
        # If no input is provided, it will fall back to the .env file.
        self.username = server_username or settings.GRACE_USER
        self.password = server_password or settings.GRACE_PASSWORD

        self.container = settings.FATE_CONTAINER
        self.fate_root = settings.FATE_ROOT

    # This method creates an SSH connection.
    def _connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=20,
        )
        return client

    # This method executes ordinary shell commands on the remote server.
    def _run_ssh_command(self, command: str):
        client = self._connect()
        try:
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore")
            return {
                "success": len(error.strip()) == 0,
                "stdout": output,
                "stderr": error,
                "command": command,
            }
        finally:
            client.close()

    # This method ensures that the FATE container remains in a running state.
    def _ensure_container_running(self):
        cmd = (
            f"docker ps -a --format '{{{{.Names}}}}' | grep -w {self.container} >/dev/null 2>&1 "
            f"&& docker start {self.container} >/dev/null 2>&1 || true"
        )
        return self._run_ssh_command(cmd)

    # This method involves performing instructions within the container.
    def _run_in_container(self, command: str):
        self._ensure_container_running()

        full_inner_command = (
            f"cd {self.fate_root} && "
            f"source bin/init_env.sh && "
            f"{command}"
        )

        full_command = (
            f"docker exec {self.container} bash -lc "
            f"{shlex.quote(full_inner_command)}"
        )

        return self._run_ssh_command(full_command)

    # Ensure that the operating environment is functioning properly.
    def ensure_environment_ready(self):
        """
        For verification:
            1. Be able to SSH to the server
            2. The container can be started
            3. Be able to access /root/fate
            4. Be able to source bin/init_env.sh
        """
        return self._run_in_container("pwd && ls -la && echo FATE_ENV_READY")

    # This method checks whether fate-flow is currently running.
    def check_fate_flow_process(self):
        """
        Check if fate-flow is running.
        If not running, automatically try to start it and then check again.
        """
        check_result = self._run_in_container(
            "ps -ef | grep fate_flow_server.py | grep -v grep"
        )

        stdout = check_result.get("stdout", "")
        if "fate_flow_server.py" in stdout:
            return {
                "success": True,
                "running": True,
                "stdout": stdout,
                "stderr": check_result.get("stderr", ""),
                "message": "fate-flow is running",
            }

        # If not detected, automatically start it once
        start_result = self._run_in_container("bash bin/service.sh fate-flow start")

        recheck_result = self._run_in_container(
            "ps -ef | grep fate_flow_server.py | grep -v grep"
        )
        recheck_stdout = recheck_result.get("stdout", "")

        return {
            "success": "fate_flow_server.py" in recheck_stdout,
            "running": "fate_flow_server.py" in recheck_stdout,
            "stdout": recheck_stdout,
            "stderr": (
                check_result.get("stderr", "")
                + "\n"
                + start_result.get("stderr", "")
                + "\n"
                + recheck_result.get("stderr", "")
            ).strip(),
            "start_stdout": start_result.get("stdout", ""),
            "start_stderr": start_result.get("stderr", ""),
            "message": "fate-flow started successfully"
            if "fate_flow_server.py" in recheck_stdout
            else "fate-flow is not running",
        }
    
    # Execute "pwd" (to print the current working directory) and "ls -la" in the working directory of the FATE container.
    def list_fate_root(self):
        return self._run_in_container("pwd && ls -la")

    # Query the status and basic information of a specific FATE task.
    def query_job(self, job_id: str, role: str = "guest", party_id: str = "9999"):
        cmd = f"flow job query -j {job_id} -r {role} -p {party_id}"
        return self._run_in_container(cmd)

    def query_job_simple(self, job_id: str):
        cmd = f"flow job query -j {job_id}"
        return self._run_in_container(cmd)

    # Obtain the list of the most recently submitted FATE tasks within the system.
    def list_jobs(self, limit: int = 20):
        commands = [
            f"flow job list -l {limit}",
            "flow job query"
        ]

        last_result = {"success": False, "stdout": "", "stderr": ""}
        for cmd in commands:
            result = self._run_in_container(cmd)
            last_result = result
            stdout = result.get("stdout", "").strip()
            if stdout:
                return result

        return last_result

    # Export the log of the specific task to the ./logs/ directory within the container.
    def get_job_log(self, job_id: str):
        cmd = f"mkdir -p logs && flow job log -j {job_id} --output-path ./logs/"
        return self._run_in_container(cmd)

    # Search for the training model file.
    def list_trained_models_file(self):
        return self._run_in_container("ls -l trained_pipeline.pkl")

    # Check the output table.
    def query_output_table(self, job_id: str, role: str = "guest", party_id: str = "9999", table_name: str = "sbt_0"):
        cmd = f"flow output query-data-table -j {job_id} -r {role} -p {party_id} -tn {table_name}"
        return self._run_in_container(cmd)

    # Upload file.
    def upload_data(self, json_config_path: str):
        cmd = f"flow data upload -c {json_config_path}"
        return self._run_in_container(cmd)

    # Query the historical records of data uploads.
    def upload_history(self, limit: int = 20):
        return {
            "success": False,
            "stdout": "",
            "stderr": "This FATE version does not support flow data upload-history."
        }

    # Check whether a certain data table exists in the FATE system.
    def query_data(self, namespace: str, name: str):
        ns = shlex.quote(namespace)
        tn = shlex.quote(name)
        return self._run_in_container(
            f"flow table query --namespace {ns} --name {tn} --display 1"
        )

    # Export the internal data tables of the FATE system back to a CSV file.
    def download_data_preview(self, namespace: str, name: str):
        cmd = f"mkdir -p output && flow data download --namespace {namespace} --name {name} --path ./output/"
        return self._run_in_container(cmd)

    # Delete the specified data table from the FATE system to free up storage space.
    def delete_table(self, namespace: str, table_name: str):
        ns = shlex.quote(namespace)
        tn = shlex.quote(table_name)
        return self._run_in_container(
            f"flow table delete --namespace {ns} --name {tn}"
        )

    # Start Training.
    def start_training(self, pipeline_script: str = "train_pipeline.py"):
        cmd = f"python {pipeline_script}"
        return self._run_in_container(cmd)

    # Query the detailed information of the model.
    def model_query(self, model_id: str, model_version: str):
        cmd = f"flow model query --model-id {model_id} --model-version {model_version}"
        return self._run_in_container(cmd)

    # Export the model.
    def model_export(self, model_id: str, model_version: str):
        cmd = (
            f"mkdir -p model_export && "
            f"flow model export --model-id {model_id} --model-version {model_version} --dir ./model_export/"
        )
        return self._run_in_container(cmd)

    # Load the exported model to facilitate prediction.
    def model_load(self, publish_config: str = "publish_load_model.json"):
        cmd = f"flow model load -c {publish_config}"
        return self._run_in_container(cmd)

    # Obtain the configuration for the prediction.
    def get_predict_conf(self, model_id: str, model_version: str):
        cmd = (
            f"mkdir -p predict_files && "
            f"flow model get-predict-conf --model-id {model_id} --model-version {model_version} -o ./predict_files/"
        )
        return self._run_in_container(cmd)

    # The DSL file for obtaining the prediction results.
    def get_predict_dsl(self, model_id: str, model_version: str):
        cmd = (
            f"mkdir -p predict_files && "
            f"flow model get-predict-dsl --model-id {model_id} --model-version {model_version} -o ./predict_files/"
        )
        return self._run_in_container(cmd)

    # Start the prediction.
    def start_prediction(self, pipeline_script: str = "predict_pipeline.py"):
        cmd = f"python {pipeline_script}"
        return self._run_in_container(cmd)

    # This method involves attempting to parse JSON from stdout.
    def _extract_json_from_output(self, text: str):
        text = text.strip()
        if not text:
            return None

        # First, try using json.loads for the entire object.
        try:
            return json.loads(text)
        except Exception:
            pass

        # If it fails, try to extract information from the text.
        match_obj = re.search(r"(\{.*\})", text, re.S)
        if match_obj:
            try:
                return json.loads(match_obj.group(1))
            except Exception:
                pass

        # If it still fails, try extracting the information from arr.
        match_arr = re.search(r"(\[.*\])", text, re.S)
        if match_arr:
            try:
                return json.loads(match_arr.group(1))
            except Exception:
                pass

        # If all attempts fail, return None.
        return None
    
    # This method extracts the job_id from the FATE output.
    def extract_job_id(self, text: str):
        if not text:
            return None

        m = re.search(r"job_id\s*=\s*(\d{18,22})", text)
        if m:
            return m.group(1)

        m = re.search(r"Job id is\s+(\d{18,22})", text)
        if m:
            return m.group(1)

        parsed = self._extract_json_from_output(text)
        if isinstance(parsed, dict):
            data = parsed.get("data")
            if isinstance(data, dict):
                for key in ["job_id", "f_job_id", "id"]:
                    if data.get(key):
                        return str(data.get(key))

            for key in ["job_id", "f_job_id", "id"]:
                if parsed.get(key):
                    return str(parsed.get(key))

        match = re.search(r"\b\d{18,22}\b", text)
        if match:
            return match.group(0)

        return None

    # This method extracts the task status from the FATE output.
    def extract_job_status(self, text: str):
        if not text:
            return "UNKNOWN"

        parsed = self._extract_json_from_output(text)

        if isinstance(parsed, dict):
            data = parsed.get("data")
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                item = data[0]
                for key in ["f_status", "status", "job_status"]:
                    if item.get(key):
                        return str(item.get(key))
            elif isinstance(data, dict):
                for key in ["f_status", "status", "job_status"]:
                    if data.get(key):
                        return str(data.get(key))

            for key in ["f_status", "status", "job_status"]:
                if parsed.get(key):
                    return str(parsed.get(key))

        # Backtracking regular expression.
        match = re.search(r'"(?:f_status|status|job_status)"\s*:\s*"([^"]+)"', text)
        if match:
            return match.group(1)

        return "UNKNOWN"

    def query_job_status_only(self, job_id: str):
        result = self.query_job_simple(job_id)
        status = self.extract_job_status(result.get("stdout", ""))
        return {
            "job_id": job_id,
            "status": status,
            "raw": result
        }

    # This method is used to generate the data for the homepage Dashboard.
    def get_dashboard_summary(self, limit: int = 20):

        # Check if fate-flow is running.
        status_result = self.check_fate_flow_process()
        fate_running = status_result.get("running", False)

        jobs_result = self.list_jobs(limit=limit)
        parsed = self._extract_json_from_output(jobs_result.get("stdout", ""))

        # Query the latest job list.
        job_items = []

        if isinstance(parsed, dict):
            data = parsed.get("data", [])
            if isinstance(data, dict):
                data = data.get("jobs", []) or data.get("records", []) or []
            if isinstance(data, list):
                job_items = data
        elif isinstance(parsed, list):
            job_items = parsed

        normalized_jobs = []
        train_count = 0
        predict_count = 0

        # Analyze the job type, status, role, party_id, and creation time.
        for item in job_items:
            if not isinstance(item, dict):
                continue

            job_id = item.get("job_id") or item.get("f_job_id") or item.get("id") or "-"
            status = item.get("status") or item.get("f_status") or item.get("job_status") or "UNKNOWN"
            role = item.get("role") or item.get("f_role") or "-"
            party_id = str(item.get("party_id") or item.get("f_party_id") or "-")
            create_time = (
                item.get("create_time")
                or item.get("f_create_time")
                or item.get("start_time")
                or item.get("f_start_time")
                or "-"
            )

            raw_text = json.dumps(item, ensure_ascii=False).lower()
            if "predict" in raw_text:
                job_type = "Prediction"
                predict_count += 1
            else:
                job_type = "Training"
                train_count += 1

            normalized_jobs.append({
                "job_id": job_id,
                "type": job_type,
                "status": status,
                "role": role,
                "party_id": party_id,
                "time": str(create_time)
            })

        return {
            "success": True,
            "fate_flow_running": fate_running,
            "fate_flow_message": "Connected" if fate_running else "Disconnected",
            "recent_train_job_number": train_count,
            "recent_predicted_number": predict_count,
            "job_list": normalized_jobs,
            "debug_status_stdout": status_result.get("stdout", ""),
            "debug_status_stderr": status_result.get("stderr", ""),
            "debug_status_message": status_result.get("message", ""),
        }
    
    def write_remote_file(self, remote_path: str, content: str):
        quoted_path = shlex.quote(remote_path)
        return self._run_in_container_with_input(
            f"cat > {quoted_path}",
            content
        )

    # Generate a training script dynamically and then write it to the remote server.
    def build_training_pipeline_script(
        self,
        dataset_name: str,
        dataset_namespace: str,
        algorithm: str,
        learning_rate: float,
        epochs: int,
        batch_size: int,
        output_script: str,
        role: str = "guest",
        party_id: str = "9999"
    ):
        safe_epochs = max(int(epochs), 1)
        safe_batch_size = max(int(batch_size), 1)
        safe_learning_rate = float(learning_rate)

        # Select the corresponding algorithm.
        algorithm_map = {
            "Homo Logistic Regression": "HomoLR",
            "HomoLR": "HomoLR",
            "Hetero Logistic Regression": "HomoLR",
        }

        component_class = algorithm_map.get(algorithm)
        if not component_class:
            return {
                "success": False,
                "stdout": "",
                "stderr": (
                    f"Unsupported algorithm for current app flow: {algorithm}. "
                    "Please use Homo Logistic Regression first."
                )
            }

        int_party_id = int(party_id) if str(party_id).isdigit() else 9999

        script = f'''
import json
import traceback

from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader, HomoLR, Evaluation

DATA_NAMESPACE = {dataset_namespace!r}
DATA_NAME = {dataset_name!r}
PARTY_ID = {str(int_party_id)!r}

print("WEBAPP_DATA_NAMESPACE=" + DATA_NAMESPACE)
print("WEBAPP_DATA_NAME=" + DATA_NAME)

try:
    pipeline = FateFlowPipeline()
    pipeline.set_parties(
        guest={int_party_id},
        host={int_party_id},
        arbiter={int_party_id}
    )

    reader_0 = Reader(
        "reader_0",
        runtime_parties=dict(
            guest=[PARTY_ID],
            host=[PARTY_ID]
        )
    )

    reader_0.guest.task_parameters(
        namespace=DATA_NAMESPACE,
        name=DATA_NAME
    )

    reader_0.hosts[0].task_parameters(
        namespace=DATA_NAMESPACE,
        name=DATA_NAME
    )

    homo_lr_0 = HomoLR(
        "homo_lr_0",
        runtime_parties=dict(
            guest=[PARTY_ID],
            host=[PARTY_ID],
            arbiter=[PARTY_ID]
        ),
        epochs={safe_epochs},
        batch_size={safe_batch_size},
        train_data=reader_0.outputs["output_data"]
    )

    evaluation_0 = Evaluation(
        "evaluation_0",
        runtime_parties=dict(guest=[PARTY_ID]),
        default_eval_setting="binary",
        input_datas=[homo_lr_0.outputs["train_output_data"]]
    )

    pipeline.add_tasks([
        reader_0,
        homo_lr_0,
        evaluation_0
    ])

    pipeline.compile()
    print("DAG compiled")
    print(pipeline._dag.dag_spec.dict())

    pipeline.fit()

    PIPELINE_PATH = "/data/projects/fate/examples/webapp_train_pipeline_" + DATA_NAME + ".pkl"
    pipeline.dump_model(PIPELINE_PATH)
    print("PIPELINE_PATH=" + PIPELINE_PATH)

    LAST_PIPELINE_PATH = "/data/projects/fate/examples/webapp_last_train_pipeline.pkl"
    pipeline.dump_model(LAST_PIPELINE_PATH)
    print("LAST_PIPELINE_PATH=" + LAST_PIPELINE_PATH)

    job_id = str(getattr(pipeline, "job_id", "") or "")
    model_id = str(getattr(pipeline, "model_id", "") or "")
    model_version = str(getattr(pipeline, "model_version", "") or "")

    print("TRAINING_JOB_SUBMITTED")
    print("JOB_ID=" + job_id)
    print("MODEL_ID=" + model_id)
    print("MODEL_VERSION=" + model_version)

    print(json.dumps({{
        "webapp_job_id": job_id,
        "webapp_model_id": model_id,
        "webapp_model_version": model_version,
        "webapp_dataset_namespace": DATA_NAMESPACE,
        "webapp_dataset_name": DATA_NAME,
        "webapp_algorithm": "HomoLR"
    }}, ensure_ascii=False))

except Exception:
    print("WEBAPP_TRAINING_EXCEPTION_BEGIN")
    traceback.print_exc()
    print("WEBAPP_TRAINING_EXCEPTION_END")
    raise
'''
        return self.write_remote_file(output_script, script)

    # This method is the one ultimately called in the /training/create section of the fate_api.py file.
    def start_training_with_config(
        self,
        dataset_name: str,
        dataset_namespace: str,
        algorithm: str,
        learning_rate: float,
        epochs: int,
        batch_size: int,
        role: str = "guest",
        party_id: str = "9999"
    ):
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", dataset_name)
        remote_script = f"/data/projects/fate/examples/generated_train_{safe_name}.py"

        write_result = self.build_training_pipeline_script(
            dataset_name=dataset_name,
            dataset_namespace=dataset_namespace,
            algorithm=algorithm,
            learning_rate=learning_rate,
            epochs=epochs,
            batch_size=batch_size,
            output_script=remote_script,
            role=role,
            party_id=party_id
        )
        # Determine whether the training was successful.
        if not write_result.get("success", False):
            return write_result

        result = self._run_in_container(f"python {shlex.quote(remote_script)}")
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        combined = stdout + "\n" + stderr

        job_id = self.extract_job_id(combined)

        success = (
            "TRAINING_JOB_SUBMITTED" in stdout
            and "WEBAPP_TRAINING_EXCEPTION_BEGIN" not in stdout
            and "Traceback" not in stderr
            and "Job is failed" not in combined
        )

        result["success"] = success
        result["generated_script"] = remote_script
        result["job_id"] = job_id

        # Return an error report when the operation fails.
        if not success:
            task_errors = None
            if job_id:
                task_errors = self.get_task_error_reports(str(job_id))

            result["task_errors"] = task_errors

            result["stderr"] = (
                f"Training job failed.\n"
                f"job_id={job_id or '-'}\n"
                f"generated_script={remote_script}\n\n"
                f"Task errors:\n"
                f"{json.dumps(task_errors, ensure_ascii=False, indent=2) if task_errors else 'No task error report found.'}\n\n"
                f"Python stdout tail:\n{stdout[-3000:]}\n\n"
                f"Python stderr tail:\n{stderr[-3000:]}"
            )

        return result

    def extract_model_info(self, text: str):

        # Extracts from the training output: job_id,model_id, model_version.
        info = {"job_id": self.extract_job_id(text), "model_id": None, "model_version": None}

        # First uses regular expressions to search for: MODEL_ID=, MODEL_VERSION= .
        if not text:
            return info
        m = re.search(r"MODEL_ID=([^\n\r]+)", text)
        if m and m.group(1).strip():
            info["model_id"] = m.group(1).strip()
        m = re.search(r"MODEL_VERSION=([^\n\r]+)", text)
        if m and m.group(1).strip():
            info["model_version"] = m.group(1).strip()
        parsed = self._extract_json_from_output(text)

        # Try to parse the following in the JSON: webapp_job_id, webapp_model_id, webapp_model_version.
        if isinstance(parsed, dict):
            for src_key, dst_key in [("webapp_job_id", "job_id"), ("webapp_model_id", "model_id"), ("webapp_model_version", "model_version")]:
                val = parsed.get(src_key)
                if val:
                    info[dst_key] = str(val)
        if not info["model_id"]:
            info["model_id"] = info["job_id"]
        if not info["model_version"]:
            info["model_version"] = "v1.0"
        return info

    # Extract pipeline_path from model description.
    def extract_pipeline_path(self, text: str):
        if not text:
            return None

        m = re.search(r"pipeline_path=([^;\n\r]+)", text)
        if m:
            return m.group(1).strip()

        return None
    
    def list_pipeline_components(self):
        cmd = """
python - <<'PY2'
import fate_client.pipeline.components.fate as fc
names = [x for x in dir(fc) if not x.startswith('_')]
print('\n'.join(names))
PY2
"""
        return self._run_in_container(cmd)

    def stop_job(self, job_id: str):
        return self._run_in_container(f"flow job stop -j {job_id}")

    # This method is used to query the status of the Job.
    def get_training_progress(self, job_id: str):
        result = self.query_job_simple(job_id)
        status = self.extract_job_status(result.get("stdout", ""))

        progress = 0
        s = status.lower()
        if "success" in s or "complete" in s or "finished" in s:
            progress = 100
        elif "running" in s:
            progress = 60
        elif "waiting" in s or "submitted" in s:
            progress = 20
        elif "failed" in s or "canceled" in s or "error" in s:
            progress = 100

        return {
            "success": True,
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "raw_stdout": result.get("stdout", ""),
            "raw_stderr": result.get("stderr", "")
        }

    def get_job_logs_text(self, job_id: str):
        # First, call the flow job log.
        self.get_job_log(job_id)

        # Concatenate the contents of the log directory and return them.
        cmd = f'''
if [ -d logs/{job_id} ]; then
  find logs/{job_id} -type f | while read f; do
    echo "===== $f ====="
    cat "$f"
    echo ""
  done
else
  echo "No log files found for {job_id}"
fi
'''
        return self._run_in_container(cmd)

    def get_job_metrics(self, job_id: str, role: str = "guest", party_id: str = "9999", component_name: str = "evaluation_0"):

        # First, Do the flow tracking/component metric query approach.
        cmd = f"flow component metric-all -j {job_id} -r {role} -p {party_id} -cpn {component_name}"
        result = self._run_in_container(cmd)

        # If the parsing fails, these fields will be set to None.
        parsed = self._extract_json_from_output(result.get('stdout', ''))
        metrics = {
            "accuracy": None,
            "auc": None,
            "loss": None,
            "precision": None
        }

        if isinstance(parsed, dict):
            text = json.dumps(parsed).lower()
            for key in metrics.keys():
                m = re.search(rf'"{key}"\\s*:\\s*([0-9.]+)', text)
                if m:
                    metrics[key] = float(m.group(1))

        return {
            "success": True,
            "job_id": job_id,
            "metrics": metrics,
            "raw_stdout": result.get("stdout", ""),
            "raw_stderr": result.get("stderr", "")
        }
    
    # This method dynamically generates the prediction script based on: model_id, model_version, dataset_name, dataset_namespace, and pipeline_path.
    def build_prediction_pipeline_script(
        self,
        model_id: str,
        model_version: str,
        dataset_name: str,
        dataset_namespace: str,
        output_script: str,
        pipeline_path: str
    ):
        script = f"""
import json
import traceback

from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader

DATA_NAMESPACE = {dataset_namespace!r}
DATA_NAME = {dataset_name!r}
MODEL_ID = {model_id!r}
MODEL_VERSION = {model_version!r}

PIPELINE_PATH = {pipeline_path!r}
PARTY_ID = "9999"

print("WEBAPP_PREDICT_DATA_NAMESPACE=" + DATA_NAMESPACE)
print("WEBAPP_PREDICT_DATA_NAME=" + DATA_NAME)
print("WEBAPP_PIPELINE_PATH=" + PIPELINE_PATH)

try:
    # 1. Load trained pipeline dumped after training
    trained_pipeline = FateFlowPipeline.load_model(PIPELINE_PATH)

    # 2. Deploy the trained HomoLR component for prediction
    trained_pipeline.deploy([trained_pipeline.homo_lr_0])
    deployed_pipeline = trained_pipeline.get_deployed_pipeline()

    # 3. Build prediction pipeline
    predict_pipeline = FateFlowPipeline()
    predict_pipeline.set_parties(
        guest=9999,
        host=9999,
        arbiter=9999
    )

    reader_1 = Reader(
        "reader_1",
        runtime_parties=dict(
            guest=[PARTY_ID],
            host=[PARTY_ID]
        )
    )

    reader_1.guest.task_parameters(
        namespace=DATA_NAMESPACE,
        name=DATA_NAME
    )

    reader_1.hosts[0].task_parameters(
        namespace=DATA_NAMESPACE,
        name=DATA_NAME
    )

    deployed_pipeline.homo_lr_0.test_data = reader_1.outputs["output_data"]

    predict_pipeline.add_tasks([
        reader_1,
        deployed_pipeline
    ])

    predict_pipeline.compile()

    print("PREDICTION_DAG_COMPILED")
    print(json.dumps(predict_pipeline._dag.dag_spec.dict(), ensure_ascii=False))

    predict_pipeline.predict()

    job_id = str(getattr(predict_pipeline, "job_id", "") or "")

    print("PREDICTION_JOB_SUBMITTED")
    print("JOB_ID=" + job_id)

    print(json.dumps({{
        "webapp_prediction_job_id": job_id,
        "webapp_model_id": MODEL_ID,
        "webapp_model_version": MODEL_VERSION,
        "webapp_dataset_namespace": DATA_NAMESPACE,
        "webapp_dataset_name": DATA_NAME,
        "webapp_pipeline_path": PIPELINE_PATH
    }}, ensure_ascii=False))

except Exception:
    print("WEBAPP_PREDICTION_EXCEPTION_BEGIN")
    traceback.print_exc()
    print("WEBAPP_PREDICTION_EXCEPTION_END")
    raise
"""
        return self.write_remote_file(output_script, script)

    # The method process for implementing predictions.
    def start_prediction_with_config(
        self,
        model_id: str,
        model_version: str,
        dataset_name: str,
        dataset_namespace: str,
        pipeline_path: str
    ):
        
        # Generate generated_predict_xxx.py based on dataset_name.
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", dataset_name)
        remote_script = f"/data/projects/fate/examples/generated_predict_{safe_name}.py"

        # Write the prediction script.
        write_result = self.build_prediction_pipeline_script(
            model_id,
            model_version,
            dataset_name,
            dataset_namespace,
            remote_script,
            pipeline_path
        )
        # Determine whether it is successful.
        if not write_result.get("success", False):
            return write_result

        result = self._run_in_container(f"python {shlex.quote(remote_script)}")
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        combined = stdout + "\n" + stderr
        combined = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", combined)

        job_id = self.extract_job_id(combined)

        success = (
            "PREDICTION_JOB_SUBMITTED" in stdout
            and "WEBAPP_PREDICTION_EXCEPTION_BEGIN" not in stdout
            and "Traceback" not in stderr
            and "Job is failed" not in combined
        )

        result["success"] = success
        result["generated_script"] = remote_script
        result["job_id"] = job_id

        # When encountering failure, check the task error reports.
        if not success:
            task_errors = None
            if job_id:
                task_errors = self.get_task_error_reports(str(job_id))

            result["task_errors"] = task_errors
            result["stderr"] = (
                f"Prediction job failed.\n"
                f"job_id={job_id or '-'}\n"
                f"generated_script={remote_script}\n\n"
                f"Task errors:\n"
                f"{json.dumps(task_errors, ensure_ascii=False, indent=2) if task_errors else 'No task error report found.'}\n\n"
                f"Python stdout tail:\n{stdout[-3000:]}\n\n"
                f"Python stderr tail:\n{stderr[-3000:]}"
            )

        return result
    
    # Carry out the conversion between the underlying task status of FATE and the progress bar on the web front end.
    def get_prediction_progress(self, job_id: str):
        result = self.query_job_simple(job_id)
        status = self.extract_job_status(result.get("stdout", ""))

        progress = 0
        s = status.lower()
        if "success" in s or "complete" in s or "finished" in s:
            progress = 100
        elif "running" in s:
            progress = 60
        elif "waiting" in s or "submitted" in s:
            progress = 20
        elif "failed" in s or "canceled" in s or "error" in s:
            progress = 100  # If the task fails, force it to be pushed to 100%.

        return {
            "success": True,
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "raw_stdout": result.get("stdout", ""),
            "raw_stderr": result.get("stderr", "")
        }

    # Query and download the prediction result from FATE.
    def get_prediction_result_text(self, job_id: str):

        safe_job_id = shlex.quote(str(job_id))

        # Step 1: query output table information from the prediction component.
        query_cmd = (
            f"flow output query-data-table "
            f"-j {safe_job_id} "
            f"-r guest "
            f"-p 9999 "
            f"-tn homo_lr_0"
        )

        query_result = self._run_in_container(query_cmd)
        query_stdout = query_result.get("stdout", "")
        query_stderr = query_result.get("stderr", "")

        parsed = self._extract_json_from_output(query_stdout)

        if not isinstance(parsed, dict):
            return {
                "success": False,
                "stdout": query_stdout,
                "stderr": (
                    "Failed to parse prediction output table information.\n"
                    f"Query stderr:\n{query_stderr}"
                ),
                "query_stdout": query_stdout,
                "query_stderr": query_stderr,
                "query_command": query_cmd,
            }

        # Step 2: extract output table namespace and name.
        output_tables = []

        for key in ["test_output_data", "predict_output_data", "output_data", "data"]:
            value = parsed.get(key)

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("namespace") and item.get("name"):
                        output_tables.append({
                            "namespace": str(item.get("namespace")),
                            "name": str(item.get("name")),
                            "source_key": key,
                        })

            elif isinstance(value, dict):
                if value.get("namespace") and value.get("name"):
                    output_tables.append({
                        "namespace": str(value.get("namespace")),
                        "name": str(value.get("name")),
                        "source_key": key,
                    })

        if not output_tables:
            return {
                "success": False,
                "stdout": query_stdout,
                "stderr": (
                    "Prediction job succeeded, but no downloadable output table was found.\n"
                    "Expected keys include test_output_data / predict_output_data / output_data."
                ),
                "query_stdout": query_stdout,
                "query_stderr": query_stderr,
                "query_command": query_cmd,
            }

        output_table = output_tables[0]
        namespace = output_table["namespace"]
        table_name = output_table["name"]

        safe_namespace = shlex.quote(namespace)
        safe_table_name = shlex.quote(table_name)

        # Step 3: download result table.
        result_dir = f"./output/prediction_{job_id}"
        safe_result_dir = shlex.quote(result_dir)

        download_cmd = (
            f"rm -rf {safe_result_dir} && "
            f"mkdir -p {safe_result_dir} && "
            f"flow data download "
            f"--namespace {safe_namespace} "
            f"--name {safe_table_name} "
            f"--path {safe_result_dir}"
        )

        download_result = self._run_in_container(download_cmd)
        download_stdout = download_result.get("stdout", "")
        download_stderr = download_result.get("stderr", "")

        # Step 4: read downloaded result files.
        cat_cmd = f"""
    if [ -d {safe_result_dir} ]; then
    printf '%s\\n' 'Prediction output table:'
    printf '%s\\n' 'namespace={namespace}'
    printf '%s\\n' 'name={table_name}'
    printf '%s\\n' ''
    printf '%s\\n' 'Downloaded files:'
    find {safe_result_dir} -type f | sort
    printf '%s\\n' ''
    printf '%s\\n' 'Prediction result content:'
    printf '%s\\n' '=========================='
    find {safe_result_dir} -type f | sort | while read f; do
        printf '%s\\n' ''
        printf '%s\\n' "===== $f ====="
        cat "$f"
        printf '%s\\n' ''
    done
    else
    printf '%s\\n' 'Prediction result directory not found: {result_dir}'
    fi
    """

        cat_result = self._run_in_container(cat_cmd)
        cat_stdout = cat_result.get("stdout", "")
        cat_stderr = cat_result.get("stderr", "")

        success = (
            bool(cat_stdout.strip())
            and "Prediction result directory not found" not in cat_stdout
            and (
                "predict_score" in cat_stdout
                or "Prediction result content" in cat_stdout
                or "0.csv" in cat_stdout
            )
        )

        return {
            "success": success,
            "stdout": cat_stdout,
            "stderr": cat_stderr,
            "query_stdout": query_stdout,
            "query_stderr": query_stderr,
            "download_stdout": download_stdout,
            "download_stderr": download_stderr,
            "query_command": query_cmd,
            "download_command": download_cmd,
            "output_namespace": namespace,
            "output_table_name": table_name,
            "output_tables": output_tables,
        }
    
    # This method is responsible for writing the binary files uploaded by the browser to the remote FATE container.
    def write_temp_dataset_file(self, remote_path: str, content: bytes):
        quoted_path = shlex.quote(remote_path)
        encoded = base64.b64encode(content).decode("ascii")
        return self._run_in_container_with_input(
            f"base64 -d > {quoted_path}",
            encoded
        )

    # Perform compatibility processing for the current FATE HomoLR environment.
    def prepare_csv_with_match_id(
        self,
        remote_file_path: str,
        id_name: str = "id",
        match_id_name: str = "match_id"
    ):
        """
        FATE HomoLR in this server requires both sample_id and match_id.
        Original WebApp CSV only has id, so we create a processed CSV:
        id,match_id,...
        where match_id duplicates id.
        """
        safe_base = re.sub(r"[^A-Za-z0-9_]", "_", remote_file_path.split("/")[-1])
        script_path = f"/data/projects/fate/examples/prepare_match_id_{safe_base}.py"

        if remote_file_path.lower().endswith(".csv"):
            output_file_path = remote_file_path[:-4] + "_with_match_id.csv"
        else:
            output_file_path = remote_file_path + "_with_match_id.csv"

        script = f'''
import csv
import os
import shutil

src = {remote_file_path!r}
dst = {output_file_path!r}
id_name = {id_name!r}
match_id_name = {match_id_name!r}

if not os.path.exists(src):
    raise FileNotFoundError(src)

with open(src, "r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.reader(f))

if not rows:
    raise ValueError("CSV file is empty: " + src)

header = rows[0]

if id_name not in header:
    raise ValueError(f"id column {{id_name!r}} does not exist in CSV header: {{header}}")

# If match_id already exists, keep the file content but still copy to dst.
if match_id_name in header:
    shutil.copyfile(src, dst)
    print(dst)
else:
    id_idx = header.index(id_name)
    new_header = header[:id_idx + 1] + [match_id_name] + header[id_idx + 1:]

    new_rows = [new_header]
    for row in rows[1:]:
        # pad short rows
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))

        match_id_value = row[id_idx]
        new_row = row[:id_idx + 1] + [match_id_value] + row[id_idx + 1:]
        new_rows.append(new_row)

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(dst)
'''

        write_result = self.write_remote_file(script_path, script)
        if not write_result.get("success", False):
            return {
                "success": False,
                "stdout": write_result.get("stdout", ""),
                "stderr": "Failed to write match_id preparation script.\n" + write_result.get("stderr", ""),
            }

        run_result = self._run_in_container(f"python {shlex.quote(script_path)}")
        if not run_result.get("success", False):
            return {
                "success": False,
                "stdout": run_result.get("stdout", ""),
                "stderr": "Failed to prepare CSV with match_id.\n" + run_result.get("stderr", ""),
            }

        return {
            "success": True,
            "stdout": run_result.get("stdout", ""),
            "stderr": run_result.get("stderr", ""),
            "processed_file_path": output_file_path,
        }

    # The method for uploading files to FATE.
    def upload_dataset_to_fate(
        self,
        remote_file_path: str,
        namespace: str,
        table_name: str,
        has_header: int = 1,
        usage_type: str = "train",
        partitions: int = 4,
        id_name: str = "id",
        label_name: str = "label",
        delimiter: str = ","
    ):
        
        safe_table_name = re.sub(r"[^A-Za-z0-9_]", "_", table_name)
        config_path = f"/data/projects/fate/examples/generated_upload_{safe_table_name}.json"  # Dynamic Construction of JSON Configuration.

        match_id_name = "match_id"

        # Prepare a FATE-compatible CSV.
        prepare_result = self.prepare_csv_with_match_id(
            remote_file_path=remote_file_path,
            id_name=id_name,
            match_id_name=match_id_name
        )
        if not prepare_result.get("success", False):
            return prepare_result

        processed_file_path = prepare_result["processed_file_path"]

        meta = {
            "delimiter": delimiter,
            "sample_id_name": id_name,
            "match_id_name": match_id_name,
            "match_id_list": [match_id_name],
            "dtype": "float32",
        }

        # Construct FATE upload configuration.
        if usage_type == "train":
            meta["label_name"] = label_name
            meta["label_type"] = "int32"

        config_obj = {
            "file": processed_file_path,
            "head": bool(has_header),
            "namespace": namespace,
            "name": table_name,
            "partitions": partitions,
            "meta": meta,
        }

        config_content = json.dumps(config_obj, ensure_ascii=False, indent=2)

        write_cfg = self.write_remote_file(config_path, config_content)
        if not write_cfg.get("success", False):
            return write_cfg

        result = self._run_in_container(
            f"flow data upload -c {shlex.quote(config_path)}"
        )

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        parsed = self._extract_json_from_output(stdout)

        # Carry out flow data upload -c config.
        submit_success = False
        upload_job_id = None

        if isinstance(parsed, dict):
            retcode = parsed.get("retcode", parsed.get("code"))
            submit_success = retcode in (0, "0")
            upload_job_id = parsed.get("job_id")
            if not upload_job_id and isinstance(parsed.get("data"), dict):
                upload_job_id = parsed["data"].get("job_id")
        else:
            submit_success = result.get("success", False)

        if not upload_job_id:
            upload_job_id = self.extract_job_id(stdout)

        wait_result = None
        if submit_success and upload_job_id:
            wait_result = self.wait_job_finished(
                str(upload_job_id),
                timeout_seconds=120,
                interval_seconds=3
            )

        # Check whether the FATE table actually exists.
        verify_result = self.query_dataset_meta(namespace, table_name)
        verify_stdout = verify_result.get("stdout", "")
        verify_stderr = verify_result.get("stderr", "")

        verify_parsed = self._extract_json_from_output(verify_stdout)
        table_exists = (
            isinstance(verify_parsed, dict)
            and verify_parsed.get("code") in (0, "0")
            and "No found table" not in verify_stdout
        )

        task_errors = None
        if upload_job_id and not table_exists:
            task_errors = self.get_task_error_reports(str(upload_job_id))

        result["config_path"] = config_path
        result["upload_config"] = config_obj
        result["upload_job_id"] = str(upload_job_id) if upload_job_id else None
        result["wait_result"] = {
            "success": wait_result.get("success"),
            "status": wait_result.get("status"),
        } if isinstance(wait_result, dict) else wait_result
        result["verify_stdout"] = verify_stdout
        result["verify_stderr"] = verify_stderr
        result["task_errors"] = task_errors

        job_ok = True
        if wait_result is not None:
            job_ok = bool(wait_result.get("success", False))

        result["success"] = bool(submit_success and job_ok and table_exists)

        # If it fails, check the task error reports.
        if not result["success"]:
            compact_error = (
                "FATE upload did not produce a queryable table.\n"
                f"Submit success: {submit_success}\n"
                f"Upload job id: {upload_job_id}\n"
                f"Upload job status: {wait_result.get('status') if isinstance(wait_result, dict) else '-'}\n"
                f"Verify stdout:\n{verify_stdout}\n"
            )

            if task_errors:
                compact_error += "\nTask errors:\n" + json.dumps(task_errors, ensure_ascii=False, indent=2)

            if stderr:
                compact_error += "\nCLI stderr:\n" + stderr

            result["stderr"] = compact_error.strip()

        return result
    
    # This function is used to obtain the task error report.
    def get_task_error_reports(self, job_id: str):
        result = self._run_in_container(f"flow task query -j {shlex.quote(job_id)}")
        stdout = result.get("stdout", "")
        parsed = self._extract_json_from_output(stdout)

        reports = []

        if isinstance(parsed, dict):
            data = parsed.get("data", [])
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    error_report = item.get("error_report") or ""
                    status = item.get("status") or item.get("party_status") or "-"
                    task_name = item.get("task_name") or item.get("component") or "-"

                    if error_report or str(status).lower() in ["failed", "error"]:
                        reports.append({
                            "task_name": task_name,
                            "status": status,
                            "error_report": error_report[-2000:] if error_report else ""
                        })

        return {
            "success": result.get("success", False),
            "reports": reports,
            "raw_stderr": result.get("stderr", "")
        }
    
    # This function is used to query the dataset_meta data.
    def query_dataset_meta(self, namespace: str, table_name: str):
        ns = shlex.quote(namespace)
        name = shlex.quote(table_name)
        return self._run_in_container(
            f"flow table query --namespace {ns} --name {name} --display 1"
        )

    # This letter deletes the data tables in FATE.
    def delete_dataset_from_fate(self, namespace: str, table_name: str):
        ns = shlex.quote(namespace)
        name = shlex.quote(table_name)
        return self._run_in_container(
            f"flow table delete --namespace {ns} --name {name}"
        )

    # Delete the files generated by the WebApp on the server.
    def delete_dataset_files_from_server(
        self,
        file_id: int,
        file_name: str,
        table_name: str
    ):
        safe_table_name = re.sub(r"[^A-Za-z0-9_]", "_", table_name)
        safe_file_base = re.sub(r"[^A-Za-z0-9_]", "_", f"webapp_upload_{file_id}_{file_name}")

        original_path = f"/data/projects/fate/examples/webapp_upload_{file_id}_{file_name}"

        if file_name.lower().endswith(".csv"):
            processed_path = original_path[:-4] + "_with_match_id.csv"
        else:
            processed_path = original_path + "_with_match_id.csv"

        generated_upload = f"/data/projects/fate/examples/generated_upload_{safe_table_name}.json"
        generated_train = f"/data/projects/fate/examples/generated_train_{safe_table_name}.py"
        generated_predict = f"/data/projects/fate/examples/generated_predict_{safe_table_name}.py"

        # Prepare script name is created from sanitized remote file basename
        prepare_script = f"/data/projects/fate/examples/prepare_match_id_{safe_file_base}.py"

        paths = [
            original_path,
            processed_path,
            generated_upload,
            generated_train,
            generated_predict,
            prepare_script,
        ]

        quoted_paths = " ".join(shlex.quote(p) for p in paths)

        cmd = f"""
rm -f {quoted_paths}
echo "Deleted WebApp files for file_id={file_id}, table_name={table_name}"
"""
        return self._run_in_container(cmd)
    
    # Delete WebApp-generated model pipeline file from server.
    def delete_model_files_from_server(self, pipeline_path: str | None):
        if not pipeline_path:
            return {
                "success": True,
                "stdout": "No pipeline_path provided. Nothing deleted.",
                "stderr": ""
            }

        pipeline_path = pipeline_path.strip()

        if not pipeline_path.startswith("/data/projects/fate/examples/webapp_train_pipeline_"):
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Refuse to delete unsafe model path: {pipeline_path}"
            }

        if not pipeline_path.endswith(".pkl"):
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Refuse to delete non-pkl model path: {pipeline_path}"
            }

        quoted_path = shlex.quote(pipeline_path)
        cmd = f"""
rm -f {quoted_path}
echo "Deleted model pipeline file: {pipeline_path}"
"""
        return self._run_in_container(cmd)
    
    # Delete WebApp-generated prediction script.
    def delete_prediction_files_from_server(self, dataset_table_name: str):
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", dataset_table_name)
        script_path = f"/data/projects/fate/examples/generated_predict_{safe_name}.py"

        quoted_path = shlex.quote(script_path)
        cmd = f"""
rm -f {quoted_path}
echo "Deleted prediction script: {script_path}"
"""
        return self._run_in_container(cmd)
    
    # Run the input within the container.
    def _run_in_container_with_input(self, command: str, input_data: str):
        self._ensure_container_running()

        # Obtain the required tokens within the input.
        full_inner = f"cd {self.fate_root} && source bin/init_env.sh && {command}"
        full_command = f"docker exec -i {self.container} bash -lc {shlex.quote(full_inner)}"

        client = self._connect()
        try:
            stdin, stdout, stderr = client.exec_command(full_command)
            if input_data:
                stdin.write(input_data)
            stdin.channel.shutdown_write()

            output = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore")
            return {
                "success": len(error.strip()) == 0,
                "stdout": output,
                "stderr": error,
                "command": full_command,
            }
        finally:
            client.close()

    # This method is used to wait for the completion of a FATE Job. Check the status every 3 seconds, with a maximum waiting time of 120 seconds.
    def wait_job_finished(self, job_id: str, timeout_seconds: int = 120, interval_seconds: int = 3):
        start = time.time()
        last_result = None

        while time.time() - start < timeout_seconds:
            result = self.query_job_simple(job_id)
            last_result = result
            stdout = result.get("stdout", "")
            status = self.extract_job_status(stdout)
            status_lower = str(status).lower()

            if any(x in status_lower for x in ["success", "finished", "complete"]):
                return {
                    "success": True,
                    "status": status,
                    "stdout": stdout,
                    "stderr": result.get("stderr", "")
                }

            if any(x in status_lower for x in ["failed", "error", "canceled", "cancelled"]):
                return {
                    "success": False,
                    "status": status,
                    "stdout": stdout,
                    "stderr": result.get("stderr", "")
                }

            time.sleep(interval_seconds)

        return {
            "success": False,
            "status": "TIMEOUT",
            "stdout": last_result.get("stdout", "") if last_result else "",
            "stderr": last_result.get("stderr", "") if last_result else "Timeout waiting for job"
        }
    
    # This method clears up "orphans" files. Used to clean up the redundant files generated during the test.
    def cleanup_orphan_webapp_files(self, active_file_ids: list[int]):
        """
        Clean WebApp-generated files whose id is not in database anymore.
        Only files matching webapp-generated patterns are removed.
        """
        active_ids_text = " ".join(str(x) for x in active_file_ids)

        cmd = f'''
python - <<'PY'
import os
import re

base = "/data/projects/fate/examples"
active_ids = set({active_file_ids!r})

patterns = [
    re.compile(r"^webapp_upload_(\\d+)_.*"),
    re.compile(r"^generated_upload_.*_(\\d+)\\.json$"),
    re.compile(r"^generated_train_.*_(\\d+)\\.py$"),
    re.compile(r"^generated_predict_.*_(\\d+)\\.py$"),
    re.compile(r"^prepare_match_id_webapp_upload_(\\d+)_.*\\.py$"),
]

deleted = []

for name in os.listdir(base):
    matched_id = None
    for p in patterns:
        m = p.match(name)
        if m:
            try:
                matched_id = int(m.group(1))
            except Exception:
                matched_id = None
            break

    if matched_id is not None and matched_id not in active_ids:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            os.remove(path)
            deleted.append(path)

print("deleted_count=", len(deleted))
for p in deleted:
    print(p)
PY
'''
        return self._run_in_container(cmd)