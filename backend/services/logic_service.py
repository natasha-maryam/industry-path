from models.logic import LogicArtifact
from services.project_service import project_service

class LogicService:
    def generate(self, project_id: str, strategy: str = "default") -> LogicArtifact:
        paths = project_service.workspace_paths(project_id)
        file_name = "main.st"
        code = f"PROGRAM Main\n(* Generated strategy: {strategy} *)\nEND_PROGRAM\n"
        output_file = paths.control_logic / file_name
        output_file.write_text(code)

        return LogicArtifact(project_id=project_id, file_name=file_name, code=code)

    def get_latest(self, project_id: str) -> LogicArtifact:
        paths = project_service.workspace_paths(project_id)
        logic_file = paths.control_logic / "main.st"
        code = logic_file.read_text() if logic_file.exists() else ""
        return LogicArtifact(project_id=project_id, file_name="main.st", code=code)


logic_service = LogicService()
