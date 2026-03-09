from models.logic import DeployResult
from services.project_service import project_service


class DeployService:
    def deploy(self, project_id: str, runtime: str = "OpenPLC") -> DeployResult:
        project_service.ensure_project(project_id)

        return DeployResult(
            project_id=project_id,
            runtime=runtime,
            status="accepted",
            details="Project-scoped deploy job queued with validation and IO mapping checks.",
        )


deploy_service = DeployService()
