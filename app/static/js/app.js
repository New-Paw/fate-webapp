// "DOMContentLoaded" indicates that the page structure has been fully loaded and it is safe to obtain the page elements.
document.addEventListener("DOMContentLoaded", function () {
    console.log("FATE WebApp UI loaded.");
    // Initialize the interface content.
    initTrainingProgressBar();
    initMainPageDashboard();
    initDataPageCrud();
    initTrainingPage();
    initModelPage();
    initPredictionPage();
});

// This equation is used to initialize the training progress bar.
function initTrainingProgressBar() {
    // Search for all progress bar elements that have the "training-progress-bar" class and the "data-progress" attribute.
    const bars = document.querySelectorAll(".training-progress-bar[data-progress]");
    bars.forEach(bar => {
        const progress = bar.getAttribute("data-progress") || "0";
        bar.style.width = progress + "%";
    });
}

// This function is used to initialize the main page dashboard.
function initMainPageDashboard() {
    // Obtain the elements displayed on the interface.
    const stateEl = document.getElementById("fate-flow-state");
    const trainEl = document.getElementById("train-job-number");
    const predictEl = document.getElementById("predicted-job-number");
    const jobListBody = document.getElementById("job-list-body");
    const refreshBtn = document.getElementById("refresh-mainpage-btn");

    // If these core elements are absent, it indicates that the current page is not the home page. In such cases, exit immediately to prevent any errors.
    if (!stateEl || !trainEl || !predictEl || !jobListBody) {
        return;
    }

    // Load the summary information of the home page.
    async function loadMainSummary(showLoading = false) {
        if (showLoading) {
            stateEl.textContent = "Loading...";
            stateEl.className = "display-6 fw-bold text-secondary";
        }

        try {
            // Request the backend Dashboard summary interface.
            const response = await fetch("/api/fate/dashboard/main-summary?limit=20");
            if (!response.ok) {
                throw new Error("HTTP error: " + response.status);
            }

            const data = await response.json();

            // Determine whether the FATE Flow has been successfully connected based on the value of fate_flow_running.
            if (data.fate_flow_running) {
                stateEl.textContent = "Connected";
                stateEl.className = "display-6 fw-bold text-success";
            } else {
                stateEl.textContent = "Disconnected";
                stateEl.className = "display-6 fw-bold text-danger";
            }

            // Update the number of training tasks.
            trainEl.textContent = data.recent_train_job_number ?? 0;

            // Update the number of prediction tasks.
            predictEl.textContent = data.recent_predicted_number ?? 0;

            const jobs = Array.isArray(data.job_list) ? data.job_list : [];

            // If there are no tasks, display an empty state.
            if (jobs.length === 0) {
                jobListBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">No jobs found.</td>
                    </tr>
                `;
                return;
            }

            // Generate HTML table based on the task list.
            jobListBody.innerHTML = jobs.map(job => {
                let badgeClass = "bg-secondary";
                const status = String(job.status || "").toLowerCase();

                if (status.includes("success") || status.includes("complete") || status.includes("finished")) {
                    badgeClass = "bg-success";
                } else if (status.includes("running") || status.includes("waiting")) {
                    badgeClass = "bg-warning text-dark";
                } else if (status.includes("failed") || status.includes("error") || status.includes("canceled")) {
                    badgeClass = "bg-danger";
                }

                // Use escapeHtml to prevent XSS attacks caused by the backend returning content that contains HTML.
                return `
                    <tr>
                        <td>${escapeHtml(job.job_id ?? "-")}</td>
                        <td>${escapeHtml(job.type ?? "-")}</td>
                        <td><span class="badge ${badgeClass}">${escapeHtml(job.status ?? "-")}</span></td>
                        <td>${escapeHtml(job.role ?? "-")}</td>
                        <td>${escapeHtml(job.party_id ?? "-")}</td>
                        <td>${escapeHtml(job.time ?? "-")}</td>
                    </tr>
                `;
            }).join("");
        } catch (error) {
            // If the request fails or the parsing fails, display the error status.
            console.error("Failed to load main summary:", error);
            stateEl.textContent = "Disconnected";
            stateEl.className = "display-6 fw-bold text-danger";
            trainEl.textContent = "0";
            predictEl.textContent = "0";
            jobListBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">Request failed.</td>
                </tr>
            `;
        }
    }

    // If the refresh button exists, bind the click event.
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => loadMainSummary(true));
    }

    loadMainSummary(true);

    // The homepage status is automatically refreshed every 15 seconds.
    setInterval(() => loadMainSummary(false), 15000);
}

// Initialize the dataset management page for CRUD operations.
function initDataPageCrud() {
    const tableBody = document.getElementById("dataset-table-body");
    const addFileInput = document.getElementById("add-file-input");

    // If there is no explicit "add-dataset-form", then search for the nearest form from the file "input" upwards.
    const addForm =
        document.getElementById("add-dataset-form") ||
        (addFileInput ? addFileInput.closest("form") : null);

    const editForm = document.getElementById("edit-dataset-form");

    // Debugging output, used to check whether the page elements have been correctly retrieved.
    console.log("DataPage elements:", {
        tableBody,
        addForm,
        addFileInput,
        editForm,
    });

    // If there is no dataset table, it indicates that this is not the data page. Exit directly.
    if (!tableBody) {
        return;
    }

    // Load file list.
    async function loadFiles() {
        try {
            // Request the interface for retrieving the list of backend files.
            const response = await fetch("/api/files/list");

            if (!response.ok) {
                throw new Error("Failed to load files");
            }

            const data = await response.json();
            const files = data.files || [];

            // If there is no file, display an empty state.
            if (files.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted">No files stored in database.</td>
                    </tr>
                `;
                return;
            }

            // Render the list of files.
            tableBody.innerHTML = files.map(file => `
                <tr>
                    <td>${file.id}</td>
                    <td>${escapeHtml(file.file_name || "-")}</td>
                    <td>${file.size_bytes ?? 0}</td>
                    <td>${file.usage_type === "predict" ? "Predict" : "Train"}</td>
                    <td>${escapeHtml(file.description || "-")}</td>
                    <td>${escapeHtml(formatDate(file.updated_at || file.created_at))}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" onclick="viewFile(${file.id})">View</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="openEditModal(${file.id})">Edit</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteFile(${file.id})">Delete</button>
                    </td>
                </tr>
            `).join("");
        } catch (error) {
            // Display an error message when loading fails.
            console.error(error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">Failed to load files.</td>
                </tr>
            `;
        }
    }

    // Handle the submission of new files.
    async function handleAddSubmit(e) {

        // Prevent the form from submitting by default and instead use fetch for asynchronous submission.
        if (e) e.preventDefault();

        const fileInput = document.getElementById("add-file-input");
        const descInput = document.getElementById("add-description-input");
        const messageEl = document.getElementById("add-dataset-message");
        const usageTypeInput = document.getElementById("add-usage-type-input");
        const formData = new FormData();

        // Check if a file has been selected.
        if (!fileInput || fileInput.files.length === 0) {
            if (messageEl) {
                messageEl.textContent = "Please choose a file.";
                messageEl.className = "small text-danger";
            }
            return;
        }

        // Add the corresponding fields.
        formData.append("file", fileInput.files[0]);
        formData.append("description", descInput ? descInput.value : "");
        formData.append("usage_type", usageTypeInput ? usageTypeInput.value : "train");

        try {
            // Request the backend upload interface.
            const response = await fetch("/api/files/upload", {
                method: "POST",
                body: formData
            });

            // First, read the text, and then attempt to parse the JSON.
            const text = await response.text();
            let data = null;

            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(`Upload failed: ${text}`);
            }

            // If HTTP request fails or the backend returns success=false, an error is thrown.
            if (!response.ok || !data.success) {
                throw new Error(data.detail || data.message || "Upload failed");
            }

            if (messageEl) {
                messageEl.textContent = "File uploaded successfully.";
                messageEl.className = "small text-success";
            }

            if (addForm) addForm.reset();
            await loadFiles();

            // Delay the closing of the new dataset pop-up window.
            setTimeout(() => {
                const modalEl = document.getElementById("addDatasetModal");
                const modal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
                if (modal) modal.hide();
                if (messageEl) messageEl.textContent = "";
            }, 800);
        } catch (error) {
            console.error("Upload error:", error);

            // Display error message when upload fails.
            if (messageEl) {
                const msg = String(error.message || "Upload failed");
                messageEl.textContent = msg.length > 900
                    ? msg.slice(0, 900) + "\n...\n[Error truncated. Check browser console or backend logs for full details.]"
                    : msg;
                messageEl.className = "small text-danger";
                messageEl.style.whiteSpace = "pre-wrap";
                messageEl.style.maxHeight = "220px";
                messageEl.style.overflowY = "auto";
            }
        }
    }

    // Process the submission of the edited document description.
    async function handleEditSubmit(e) {
        if (e) e.preventDefault();

        const fileId = document.getElementById("edit-file-id")?.value;
        const descInput = document.getElementById("edit-description-input");
        const messageEl = document.getElementById("edit-dataset-message");

        const formData = new FormData();
        formData.append("description", descInput ? descInput.value : "");

        try {
            // Request the backend to update the file description interface.
            const response = await fetch(`/api/files/${fileId}`, {
                method: "PUT",
                body: formData
            });

            const text = await response.text();
            let data = null;

            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(text || "Update failed");
            }

            if (!response.ok || !data.success) {
                throw new Error(data.detail || data.message || "Update failed");
            }

            if (messageEl) {
                messageEl.textContent = "File updated successfully.";
                messageEl.className = "small text-success";
            }

            // Reload the list.
            await loadFiles();

            // Delay the closing of the editing pop-up window.
            setTimeout(() => {
                const modalEl = document.getElementById("editDatasetModal");
                const modal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
                if (modal) modal.hide();
                if (messageEl) messageEl.textContent = "";
            }, 800);
        } catch (error) {
            console.error("Update error:", error);
            if (messageEl) {
                messageEl.textContent = error.message;
                messageEl.className = "small text-danger";
            }
        }
    }

    // Bind the new form event. If a form exists, listen for the submit event.
    if (addForm) {
        addForm.addEventListener("submit", handleAddSubmit);
    } else {
        const addBtn = document.getElementById("add-dataset-save-btn");
        if (addBtn) {
            addBtn.addEventListener("click", handleAddSubmit);
        }
    }

    // Bind the event of the editing form.
    if (editForm) {
        editForm.addEventListener("submit", handleEditSubmit);
    } else {
        const editBtn = document.getElementById("edit-dataset-save-btn");
        if (editBtn) {
            editBtn.addEventListener("click", handleEditSubmit);
        }
    }

    // View file details.
    window.viewFile = async function (fileId) {
        try {
            // Request file details.
            const response = await fetch(`/api/files/${fileId}`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.detail || "Failed to load file detail");
            }

            const file = data.file;

            // Fill the file details into the viewing pop-up window.
            document.getElementById("view-file-id").textContent = file.id;
            document.getElementById("view-file-name").textContent = file.file_name || "-";
            document.getElementById("view-file-usage-type").textContent = file.usage_type === "predict" ? "Predict" : "Train";
            document.getElementById("view-file-type").textContent = file.content_type || "-";
            document.getElementById("view-file-size").textContent = file.size_bytes ?? 0;
            document.getElementById("view-file-description").textContent = file.description || "-";
            document.getElementById("view-file-namespace").textContent = file.namespace || "-";
            document.getElementById("view-file-table-name").textContent = file.table_name || "-";
            document.getElementById("view-file-created-at").textContent = formatDate(file.created_at);
            document.getElementById("view-file-updated-at").textContent = formatDate(file.updated_at || file.created_at);
            document.getElementById("view-download-link").href = `/api/files/${fileId}/download`;  // Download link.
            document.getElementById("view-file-fate-meta").textContent =
                data.fate_meta_stdout || data.fate_meta_stderr || "No metadata returned.";

            // Open the Bootstrap pop-up window.
            const modal = new bootstrap.Modal(document.getElementById("viewDatasetModal"));
            modal.show();
        } catch (error) {
            alert(error.message);
        }
    };

    // Open the pop-up window for editing file description.
    window.openEditModal = async function (fileId) {
        try {
            const response = await fetch(`/api/files/${fileId}`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.detail || "Failed to load file detail");
            }

            const file = data.file;

            // Fill in the current file information into the editing form.
            document.getElementById("edit-file-id").value = file.id;
            document.getElementById("edit-description-input").value = file.description || "";
            document.getElementById("edit-dataset-message").textContent = "";

            const modal = new bootstrap.Modal(document.getElementById("editDatasetModal"));
            modal.show();
        } catch (error) {
            alert(error.message);
        }
    };

    // Delete file.
    window.deleteFile = async function (fileId) {
        const ok = confirm(`Delete file ${fileId}?`);
        if (!ok) return;

        try {
            // Corresponding to the backend: DELETE /api/files/{file_id}
            const response = await fetch(`/api/files/${fileId}`, {
                method: "DELETE"
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.detail || "Delete failed");
            }

            // Refresh the file list after deletion.
            await loadFiles();
        } catch (error) {
            alert(error.message);
        }
    };

    // Load the file list immediately when the page loads.
    loadFiles();
}

// Date Formatting Utility Function.
function formatDate(value) {
    if (!value) return "-";
    return value.replace("T", " ").slice(0, 19);
}

// HTML Escaping Utility Functions.
function escapeHtml(value) {
    // Prevent the content returned by the backend from being executed by the browser as HTML.
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// Initialize the training page.
function initTrainingPage() {
    const datasetSelect = document.getElementById("training-dataset-select");
    const algorithmSelect = document.getElementById("training-algorithm-select");
    const createBtn = document.getElementById("create-training-btn");
    const logsBtn = document.getElementById("request-logs-btn");
    const logBox = document.getElementById("training-log-box");

    // If the key element does not exist, it indicates that the current page is not a training page, so exit directly.
    if (!datasetSelect || !algorithmSelect || !createBtn) {
        return;
    }

    // Save the ID of the currently created training job.
    let currentJobId = null;

    // Load the dataset that can be used for training.
    async function loadDatasetsForTraining() {
        try {
            const response = await fetch("/api/fate/training/datasets");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load datasets");
            }

            const datasets = data.datasets || [];

            // Display a prompt when there is no training dataset.
            if (datasets.length === 0) {
                datasetSelect.innerHTML = `<option value="">No uploaded training datasets</option>`;
                return;
            }

            // Render the dropdown box for the training dataset.
            datasetSelect.innerHTML = datasets.map(ds => `
                <option value="${ds.id}">
                    ${escapeHtml(ds.file_name)} | ${escapeHtml(ds.namespace || "-")}.${escapeHtml(ds.table_name || "-")}
                </option>
            `).join("");
        } catch (error) {
            console.error("Failed to load training datasets:", error);
            datasetSelect.innerHTML = `<option value="">Failed to load datasets</option>`;

            if (logBox) {
                logBox.textContent = "Failed to load training datasets:\n" + error.message;
            }
        }
    }

    // Create training task.
    async function createTraining() {
        const datasetFileId = datasetSelect.value;
        const algorithm = algorithmSelect.value;

        // Obtain the input box for training parameters.
        const learningRateInput = document.getElementById("param-learning-rate");
        const epochsInput = document.getElementById("param-epochs");
        const batchSizeInput = document.getElementById("param-batch-size");

        // Parse the training parameters.
        const learningRate = parseFloat(learningRateInput ? learningRateInput.value || "0.1" : "0.1");
        const epochs = parseInt(epochsInput ? epochsInput.value || "10" : "10", 10);
        const batchSize = parseInt(batchSizeInput ? batchSizeInput.value || "32" : "32", 10);

        // Select the dataset.
        if (!datasetFileId) {
            alert("Please choose a dataset first.");
            return;
        }

        if (logBox) {
            logBox.textContent = "Creating training job...\nPlease wait.";
        }

        // Prevent users from clicking repeatedly.
        createBtn.disabled = true;
        createBtn.textContent = "Creating...";

        try {
            // Request the backend to create the training interface.
            const response = await fetch("/api/fate/training/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    dataset_file_id: parseInt(datasetFileId, 10),
                    algorithm: algorithm,
                    learning_rate: learningRate,
                    epochs: epochs,
                    batch_size: batchSize
                })
            });

            const text = await response.text();
            let data = null;

            // Attempt to parse JSON.
            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(text);
            }

            currentJobId = data.job_id || null;

            // If the training fails, construct a detailed error message.
            if (!response.ok || !data.success) {
                const detail = [
                    "Training job failed.",
                    `job_id=${data.job_id || "-"}`,
                    data.generated_script ? `generated_script=${data.generated_script}` : "",
                    "",
                    "Task errors:",
                    data.task_errors ? JSON.stringify(data.task_errors, null, 2) : "No task error report found.",
                    "",
                    "Python stderr / message:",
                    data.stderr || data.message || "Create training failed",
                    "",
                    "Python stdout:",
                    data.stdout || ""
                ].join("\n");

                if (logBox) {
                    logBox.textContent = detail;
                }

                throw new Error("Training failed. Check Request of Logs panel for details.");
            }

            // After the training submission is successful, the results will be displayed.
            const successText = [
                "Training submitted successfully.",
                `Job ID: ${data.job_id || "-"}`,
                `Model ID: ${data.model_id || "-"}`,
                `Model Version: ${data.model_version || "-"}`,
                "",
                "Raw stdout:",
                data.stdout || "No stdout returned."
            ].join("\n");

            if (logBox) {
                logBox.textContent = successText;
            }

            alert(`Training submitted successfully.\nJob ID: ${data.job_id || "-"}`);
        } catch (error) {
            console.error("Training create error:", error);

            if (logBox && (!logBox.textContent || logBox.textContent === "Creating training job...\nPlease wait.")) {
                logBox.textContent = error.message;
            }

            alert(error.message);
        } finally {
            // Restore the button's state.
            createBtn.disabled = false;
            createBtn.textContent = "Create Training";
        }
    }

    // Request for training log.
    async function requestLogs() {
        if (!currentJobId) {
            alert("No job_id available yet. Please create a training job first.");
            return;
        }

        try {
            // Corresponding to the backend: POST /api/fate/training/logs.
            const response = await fetch("/api/fate/training/logs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id: currentJobId })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to get logs");
            }

            if (logBox) {
                logBox.textContent = data.stdout || data.stderr || "No logs returned.";
            }
        } catch (error) {
            console.error("Request logs error:", error);
            alert(error.message);
        }
    }

    // Bind the event for the "Create Training" button.
    createBtn.addEventListener("click", createTraining);

    if (logsBtn) {
        logsBtn.addEventListener("click", requestLogs);
    }

    // Load the training dataset when the page is loaded.
    loadDatasetsForTraining();
}

// Initialize the model management page.
function initModelPage() {
    const tableBody = document.getElementById("model-table-body");
    const refreshBtn = document.getElementById("refresh-models-btn");
    const editForm = document.getElementById("edit-model-form");

    // If the model table does not exist, it indicates that this is not the model page.
    if (!tableBody) {
        return;
    }

    // Load the list of models.
    async function loadModels() {
        try {
            const response = await fetch("/api/fate/models/list");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load models");
            }

            const models = data.models || [];

            if (models.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">No trained models found.</td>
                    </tr>
                `;
                return;
            }

            // List of rendered models.
            tableBody.innerHTML = models.map(model => `
                <tr>
                    <td>${escapeHtml(model.model_id)}</td>
                    <td>${escapeHtml(model.name)}</td>
                    <td>${escapeHtml(model.algorithm)}</td>
                    <td>${escapeHtml(model.version)}</td>
                    <td>${escapeHtml(model.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" onclick="viewModelDetail('${escapeHtml(model.model_id)}', '${escapeHtml(model.version)}')">View</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="openModelEdit('${escapeHtml(model.model_id)}', '${escapeHtml(model.name)}', '${escapeHtml(model.version)}', '${escapeHtml(model.description || "")}')">Edit</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteModel('${escapeHtml(model.model_id)}')">Delete</button>
                    </td>
                </tr>
            `).join("");
        } catch (error) {
            console.error(error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">Failed to load models.</td>
                </tr>
            `;
        }
    }

    // View model details.
    window.viewModelDetail = async function (modelId, version) {
        try {
            // Corresponding to the backend: POST /api/fate/models/detail.
            const response = await fetch("/api/fate/models/detail", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model_id: modelId,
                    version: version || "v1.0"
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load model detail");
            }

            // Display the model details pop-up window.
            document.getElementById("view-model-id").textContent = data.local.model_id || "-";
            document.getElementById("view-model-name").textContent = data.local.name || "-";
            document.getElementById("view-model-algorithm").textContent = data.local.algorithm || "-";
            document.getElementById("view-model-version").textContent = data.local.version || "-";
            document.getElementById("view-model-description").textContent = data.local.description || "-";
            document.getElementById("view-model-fate-output").textContent =
                data.fate_stdout || data.fate_stderr || "No detail returned.";

            const modal = new bootstrap.Modal(document.getElementById("viewModelModal"));
            modal.show();
        } catch (error) {
            alert(error.message);
        }
    };

    // Open the model editing pop-up window.
    window.openModelEdit = function (modelId, name, version, description) {
        document.getElementById("edit-model-id").value = modelId;
        document.getElementById("edit-model-name").value = name || "";
        document.getElementById("edit-model-version").value = version || "v1.0";
        document.getElementById("edit-model-description").value = description || "";
        document.getElementById("edit-model-message").textContent = "";

        const modal = new bootstrap.Modal(document.getElementById("editModelModal"));
        modal.show();
    };

    // Delete model.
    window.deleteModel = async function (modelId) {
        const ok = confirm(`Delete model ${modelId}? This will also delete its server pipeline .pkl file.`);
        if (!ok) return;

        try {
            // Corresponding to the backend: DELETE /api/fate/models/{model_id}.
            const response = await fetch(`/api/fate/models/${encodeURIComponent(modelId)}`, {
                method: "DELETE"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || data.server_delete_stderr || "Delete model failed");
            }

            // Refresh the model list after deletion.
            await loadModels();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    };

    // Save model editing.
    async function saveModelEdit(e) {
        e.preventDefault();

        const modelId = document.getElementById("edit-model-id").value;
        const name = document.getElementById("edit-model-name").value;
        const version = document.getElementById("edit-model-version").value;
        const description = document.getElementById("edit-model-description").value;
        const msg = document.getElementById("edit-model-message");

        try {
            // Corresponding to the backend: PUT /api/fate/models/update.
            const response = await fetch("/api/fate/models/update", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model_id: modelId,
                    name: name,
                    version: version,
                    description: description
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to update model");
            }

            msg.textContent = "Model updated successfully.";
            msg.className = "small text-success";

            await loadModels();

            // Delay the closing of the editing pop-up window.
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById("editModelModal"));
                if (modal) modal.hide();
                msg.textContent = "";
            }, 800);
        } catch (error) {
            msg.textContent = error.message;
            msg.className = "small text-danger";
        }
    }

    // Bind the refresh button.
    if (refreshBtn) {
        refreshBtn.addEventListener("click", loadModels);
    }

    // Bind the editing form.
    if (editForm) {
        editForm.addEventListener("submit", saveModelEdit);
    }

    // Load the model list when the page is loaded.
    loadModels();
}

// Initialize the prediction page.
function initPredictionPage() {
    const modelSelect = document.getElementById("prediction-model-select");
    const datasetSelect = document.getElementById("prediction-dataset-select");
    const startBtn = document.getElementById("start-prediction-btn");
    const tableBody = document.getElementById("prediction-table-body");
    const editForm = document.getElementById("edit-prediction-form");

    // If the key element does not exist, it indicates that this is not the prediction page.
    if (!modelSelect || !datasetSelect || !startBtn || !tableBody) {
        return;
    }

    // Load the model that can be used for prediction.
    async function loadPredictionModels() {
        try {
            // Corresponding to the backend: GET /api/fate/prediction/models.
            const response = await fetch("/api/fate/prediction/models");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load models");
            }

            const models = data.models || [];

            if (models.length === 0) {
                modelSelect.innerHTML = `<option value="">No models available</option>`;
                return;
            }

            // Render the dropdown box for the model.
            modelSelect.innerHTML = models.map(m => `
                <option value="${m.model_id}">
                    ${escapeHtml(m.name)} (${escapeHtml(m.version)})
                </option>
            `).join("");
        } catch (error) {
            console.error(error);
            modelSelect.innerHTML = `<option value="">Failed to load models</option>`;
        }
    }

    // Load the dataset that can be used for prediction.
    async function loadPredictionDatasets() {
        try {
            // Corresponding to the backend: GET /api/fate/prediction/datasets.
            const response = await fetch("/api/fate/prediction/datasets");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load datasets");
            }

            const datasets = data.datasets || [];

            if (datasets.length === 0) {
                datasetSelect.innerHTML = `<option value="">No datasets available</option>`;
                return;
            }

            // Render the dropdown box for the predicted data set.
            datasetSelect.innerHTML = datasets.map(d => `
                <option value="${d.id}">
                    ${escapeHtml(d.file_name)}
                </option>
            `).join("");
        } catch (error) {
            console.error(error);
            datasetSelect.innerHTML = `<option value="">Failed to load datasets</option>`;
        }
    }

    // Load the list of prediction tasks.
    async function loadPredictionList() {
        try {
            // Corresponding to the backend: GET /api/fate/prediction/list.
            const response = await fetch("/api/fate/prediction/list");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to load prediction list");
            }

            const records = data.predictions || [];

            if (records.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">No prediction tasks found.</td>
                    </tr>
                `;
                return;
            }

            // Render the prediction record table.
            tableBody.innerHTML = records.map(item => {
                let badgeClass = "bg-secondary";
                const status = String(item.status || "").toLowerCase();

                if (status.includes("success") || status.includes("complete") || status.includes("finished")) {
                    badgeClass = "bg-success";
                } else if (status.includes("running") || status.includes("waiting")) {
                    badgeClass = "bg-warning text-dark";
                } else if (status.includes("failed") || status.includes("error") || status.includes("canceled")) {
                    badgeClass = "bg-danger";
                }

                return `
                    <tr>
                        <td>${escapeHtml(item.prediction_job_id)}</td>
                        <td>${escapeHtml(item.model_name)}</td>
                        <td>${escapeHtml(item.dataset_name)}</td>
                        <td><span class="badge ${badgeClass}">${escapeHtml(item.status)}</span></td>
                        <td>${escapeHtml(item.time)}</td>
                    <td>
                        <div class="d-flex flex-wrap gap-1 justify-content-start action-buttons">
                            <button class="btn btn-sm btn-outline-info" onclick="viewPredictionResult('${escapeHtml(item.prediction_job_id)}')">
                                View
                            </button>

                            <button class="btn btn-sm btn-outline-success" onclick="downloadPredictionResult('${escapeHtml(item.prediction_job_id)}')">
                                Download
                            </button>

                            <button class="btn btn-sm btn-outline-secondary" onclick="openPredictionEdit('${escapeHtml(item.prediction_job_id)}', '${escapeHtml(item.note || "")}')">
                                Edit
                            </button>

                            <button class="btn btn-sm btn-outline-danger" onclick="deletePrediction('${escapeHtml(item.prediction_job_id)}')">
                                Delete
                            </button>
                        </div>
                    </td>
                    </tr>
                `;
            }).join("");
        } catch (error) {
            console.error(error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">Failed to load prediction list.</td>
                </tr>
            `;
        }
    }

    // Initiate the prediction task.
    async function startPrediction() {
        const modelId = modelSelect.value;
        const datasetFileId = datasetSelect.value;

        if (!modelId) {
            alert("Please choose a model.");
            return;
        }

        if (!datasetFileId) {
            alert("Please choose a dataset.");
            return;
        }

        try {
            // Corresponding to the backend: POST /api/fate/prediction/create.
            const response = await fetch("/api/fate/prediction/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model_id: modelId,
                    dataset_file_id: parseInt(datasetFileId, 10)
                })
            });

            const text = await response.text();
            let data = null;

            // Attempt to parse the JSON. If the parsing fails, display the original text directly.
            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(text);
            }

            if (!response.ok || !data.success) {
                const detail = [
                    data.stderr || data.message || "Prediction create failed",
                    data.task_errors ? "\n\nTASK_ERRORS:\n" + JSON.stringify(data.task_errors, null, 2) : "",
                    data.generated_script ? "\n\nGenerated script:\n" + data.generated_script : ""
                ].join("");

                throw new Error(detail);
            }

            alert(`Prediction job submitted: ${data.job_id || "-"}`);

            // Refresh the list of predicted records after creating the prediction.
            await loadPredictionList();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    // View prediction results.
    window.viewPredictionResult = async function (predictionJobId) {
        try {
            // Corresponding to the backend: POST /api/fate/prediction/result.
            const response = await fetch("/api/fate/prediction/result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prediction_job_id: predictionJobId })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const detail = [
                    data.message || "Failed to load prediction result",
                    "",
                    "STDOUT:",
                    data.stdout || data.raw_stdout || "-",
                    "",
                    "STDERR:",
                    data.stderr || data.raw_stderr || "-",
                    "",
                    "QUERY_STDOUT:",
                    data.query_stdout || "-",
                    "",
                    "QUERY_STDERR:",
                    data.query_stderr || "-",
                    "",
                    "DOWNLOAD_STDOUT:",
                    data.download_stdout || "-",
                    "",
                    "DOWNLOAD_STDERR:",
                    data.download_stderr || "-",
                    "",
                    "OUTPUT TABLE:",
                    `${data.output_namespace || "-"} / ${data.output_table_name || "-"}`
                ].join("\n");

                document.getElementById("prediction-result-box").textContent = detail;

                const modal = new bootstrap.Modal(document.getElementById("viewPredictionModal"));
                modal.show();

                return;
            }

            // Display the prediction results in the text area of the pop-up window.
            document.getElementById("prediction-result-box").textContent =
                data.stdout || data.raw_stdout || data.raw_stderr || "No prediction result returned.";

            const modal = new bootstrap.Modal(document.getElementById("viewPredictionModal"));
            modal.show();
        } catch (error) {
            alert(error.message);
        }
    };

    // Download prediction results.
    window.downloadPredictionResult = async function (predictionJobId) {
        try {
            if (!predictionJobId) {
                alert("Prediction Job ID is missing.");
                return;
            }

            // Request prediction result from backend.
            const response = await fetch("/api/fate/prediction/result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prediction_job_id: predictionJobId })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const detail = [
                    data.message || "Failed to load prediction result",
                    "",
                    "STDOUT:",
                    data.stdout || data.raw_stdout || "-",
                    "",
                    "STDERR:",
                    data.stderr || data.raw_stderr || "-",
                    "",
                    "QUERY_STDOUT:",
                    data.query_stdout || "-",
                    "",
                    "QUERY_STDERR:",
                    data.query_stderr || "-",
                    "",
                    "DOWNLOAD_STDOUT:",
                    data.download_stdout || "-",
                    "",
                    "DOWNLOAD_STDERR:",
                    data.download_stderr || "-",
                    "",
                    "OUTPUT TABLE:",
                    `${data.output_namespace || "-"} / ${data.output_table_name || "-"}`
                ].join("\n");

                throw new Error(detail);
            }

            // Use the same result fields as the View button.
            const resultText =
                data.stdout ||
                data.raw_stdout ||
                data.raw_stderr ||
                "No prediction result returned.";

            // Build a readable text file.
            const fileContent = [
                "FATE WebApp UI - Prediction Result",
                "====================================",
                `Prediction Job ID: ${predictionJobId}`,
                `Downloaded At: ${new Date().toLocaleString()}`,
                "",
                "Result:",
                "-------",
                resultText
            ].join("\n");

            // Create a browser-side text file.
            const blob = new Blob([fileContent], {
                type: "text/plain;charset=utf-8"
            });

            const url = window.URL.createObjectURL(blob);

            // Trigger download.
            const link = document.createElement("a");
            link.href = url;
            link.download = `prediction_${predictionJobId}_result.txt`;

            document.body.appendChild(link);
            link.click();

            // Clean temporary object URL.
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error("Download prediction result error:", error);
            alert(error.message);
        }
    };

    // Open the prediction note editing pop-up window.
    window.openPredictionEdit = function (predictionJobId, note) {
        document.getElementById("edit-prediction-id").value = predictionJobId;
        document.getElementById("edit-prediction-note").value = note || "";
        document.getElementById("edit-prediction-message").textContent = "";

        const modal = new bootstrap.Modal(document.getElementById("editPredictionModal"));
        modal.show();
    };

    // Delete prediction records.
    window.deletePrediction = async function (predictionJobId) {
        const ok = confirm(`Delete prediction record ${predictionJobId}? This will also delete its generated prediction script.`);
        if (!ok) return;

        try {
            // Corresponding to the backend: DELETE /api/fate/prediction/{prediction_job_id}.
            const response = await fetch(`/api/fate/prediction/${encodeURIComponent(predictionJobId)}`, {
                method: "DELETE"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || data.server_delete_stderr || "Delete prediction failed");
            }

            // Refresh the prediction list after deletion.
            await loadPredictionList();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    };

    // Save the editing of the prediction remarks.
    async function savePredictionEdit(e) {
        e.preventDefault();

        const predictionJobId = document.getElementById("edit-prediction-id").value;
        const note = document.getElementById("edit-prediction-note").value;
        const msg = document.getElementById("edit-prediction-message");

        try {
            // Corresponding to the backend: PUT /api/fate/prediction/update.
            const response = await fetch("/api/fate/prediction/update", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prediction_job_id: predictionJobId,
                    note: note
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Failed to update prediction record");
            }

            msg.textContent = "Prediction record updated successfully.";
            msg.className = "small text-success";

            await loadPredictionList();

            // Delay the closing of the editing pop-up window.
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById("editPredictionModal"));
                if (modal) modal.hide();
                msg.textContent = "";
            }, 800);
        } catch (error) {
            msg.textContent = error.message;
            msg.className = "small text-danger";
        }
    }

    // Bind the start prediction button.
    startBtn.addEventListener("click", startPrediction);

    // Bind the prediction remarks editing form.
    if (editForm) {
        editForm.addEventListener("submit", savePredictionEdit);
    }

    loadPredictionModels();
    loadPredictionDatasets();
    loadPredictionList();
    setInterval(loadPredictionList, 5000);
}