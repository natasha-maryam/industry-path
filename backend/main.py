import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_integration_behavior_patch import register_behavior_routes
from api.production_api import router as production_api_router
from api.routes.deploy import router as deploy_router
from api.engineering_table import router as engineering_table_router
from api.routes.control_loops import router as control_loops_router
from api.routes.direct_plc_deploy import router as direct_plc_deploy_router
from api.routes.fault_analysis import router as fault_analysis_router
from api.routes.export import router as export_router
from api.routes.graph import router as graph_router
from api.routes.health import router as health_router
from api.routes.io_mapping import router as io_mapping_router
from api.routes.logic import router as logic_router
from api.routes.monitoring import router as monitoring_router
from api.routes.parse import router as parse_router
from api.routes.pid_reconcile import router as pid_reconcile_router
from api.routes.pipeline import router as pipeline_router
from api.routes.plc_export import router as plc_export_router
from api.routes.plc_reverse_engineering import router as plc_reverse_engineering_router
from api.routes.project_io_mapping import router as project_io_mapping_router
from api.routes.projects import router as projects_router
from api.routes.replay import router as replay_router
from api.routes.runtime import router as runtime_router
from api.routes.runtime_deploy import router as runtime_deploy_router
from api.routes.simulation import router as simulation_router
from api.routes.st_verify import router as st_verify_router
from api.system_layer import router as system_layer_router
from api.system_layer_upgrade import router as system_layer_upgrade_router
from api.tag_intelligence_api import router as tag_intelligence_router
from api.views_api import router as views_api_router
from api.routes.uploads import router as uploads_router
from api.routes.versions import router as versions_router
from core.metrics import RequestMetricsMiddleware
from db.postgres import postgres_client
from services.deterministic_behavior_service import deterministic_behavior_service


logger = logging.getLogger(__name__)

app = FastAPI(title="CrossLayerX API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestMetricsMiddleware)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "CrossLayerX project-based backend running"}


@app.on_event("startup")
def startup() -> None:
    postgres_client.init_schema()
    logger.info("backend startup complete")
    logger.info("system router registered prefix=/api")
    logger.info("behavior rows currently loaded count=%s", deterministic_behavior_service.get_rows_loaded_count())


app.include_router(health_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(parse_router, prefix="/api")
app.include_router(pid_reconcile_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(replay_router, prefix="/api")
app.include_router(runtime_deploy_router, prefix="/api")
app.include_router(runtime_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(logic_router, prefix="/api")
app.include_router(io_mapping_router, prefix="/api")
app.include_router(project_io_mapping_router, prefix="/api")
app.include_router(deploy_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(st_verify_router, prefix="/api")
app.include_router(control_loops_router, prefix="/api")
app.include_router(fault_analysis_router, prefix="/api")
app.include_router(versions_router, prefix="/api")
app.include_router(plc_export_router, prefix="/api")
app.include_router(plc_reverse_engineering_router, prefix="/api")
app.include_router(direct_plc_deploy_router, prefix="/api")
app.include_router(engineering_table_router, prefix="/api")
register_behavior_routes(app)
app.include_router(system_layer_router, prefix="/api")
app.include_router(system_layer_upgrade_router, prefix="/api")
app.include_router(tag_intelligence_router, prefix="/api")
app.include_router(views_api_router, prefix="/api")
app.include_router(production_api_router, prefix="/api")