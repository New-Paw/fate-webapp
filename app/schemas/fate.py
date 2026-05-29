from pydantic import BaseModel
from typing import Optional

# This class is used for querying FATE Jobs.
class JobQueryRequest(BaseModel):
    job_id: str
    role: str = "guest"
    party_id: str = "9999"

# This class is used to query the FATE data table.
class DataQueryRequest(BaseModel):
    namespace: str
    name: str

# This class is used to delete the FATE data table.
class DeleteTableRequest(BaseModel):
    namespace: str
    table_name: str

# This class is used to query the output table of a specific FATE Job.
class OutputTableRequest(BaseModel):
    job_id: str
    role: str = "guest"
    party_id: str = "9999"
    table_name: str = "sbt_0"

# This class is used for querying, exporting the model, or generating prediction configuration/DSL.
class ModelQueryRequest(BaseModel):
    model_id: str
    model_version: str

# This class is used to upload FATE data based on the remote JSON configuration.
class UploadDataRequest(BaseModel):
    json_config_path: str

# This class is used to directly run a pipeline script.
class PipelineRequest(BaseModel):
    pipeline_script: str

# This is training to create an interface request model.
class TrainingCreateRequest(BaseModel):
    dataset_file_id: int
    algorithm: str
    learning_rate: float = 0.1
    epochs: int = 10
    batch_size: int = 32
    role: str = "guest"
    party_id: str = "9999"

# This class is used for interfaces that only require the Job ID.
class JobIdRequest(BaseModel):
    job_id: str

# This class is used to query training metrics.
class MetricsRequest(BaseModel):
    job_id: str
    role: str = "guest"
    party_id: str = "9999"
    component_name: str = "evaluation_0"

# This class is used to update the local model records.
class ModelUpdateRequest(BaseModel):
    model_id: str
    name: str
    version: str
    description: Optional[str] = ""

# This class is used to view the details of the model.
class ModelDetailRequest(BaseModel):
    model_id: str
    version: str = "v1.0"

# This class is used to create prediction tasks.
class PredictionCreateRequest(BaseModel):
    model_id: str
    dataset_file_id: int
    role: str = "guest"
    party_id: str = "9999"

# This class is used to query the status or result of a certain prediction.
class PredictionDetailRequest(BaseModel):
    prediction_job_id: str

# This class is used to update the remarks of the prediction records.
class PredictionUpdateRequest(BaseModel):
    prediction_job_id: str
    note: Optional[str] = ""