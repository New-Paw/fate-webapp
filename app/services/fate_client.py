from fate_client.flow_sdk.client import FlowClient
from app.config import settings

# This class is a secondary encapsulation of the FlowClient.
class FateManager:
    def __init__(self):
        self.client = FlowClient(
            settings.FATE_HOST,
            settings.FATE_PORT,
            settings.FATE_API_VERSION
        )

    # This method is used to query the list of FATE Jobs.
    def list_jobs(self, limit: int = 10):
        return self.client.job.list(limit=limit)

    # This method is used to query the detailed information of a specific FATE Job based on the job_id.
    def query_job(self, job_id: str):
        return self.client.job.query(job_id=job_id)

    # This method is used to download or obtain the logs of a certain Job.
    def get_job_log(self, job_id: str, output_path: str):
        return self.client.job.log(job_id=job_id, output_path=output_path)

    # This method is used to query all the indicators of a certain component.
    def get_metrics(self, job_id: str, role: str, party_id: str, component_name: str):
        return self.client.component.metric_all(
            job_id=job_id,
            role=role,
            party_id=party_id,
            component_name=component_name
        )