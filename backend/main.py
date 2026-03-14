from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.deploy import router as deploy_router
from api.routes.graph import router as graph_router
from api.routes.health import router as health_router
from api.routes.io_mapping import router as io_mapping_router
from api.routes.logic import router as logic_router
from api.routes.monitoring import router as monitoring_router
from api.routes.parse import router as parse_router
from api.routes.pipeline import router as pipeline_router
from api.routes.project_io_mapping import router as project_io_mapping_router
from api.routes.projects import router as projects_router
from api.routes.replay import router as replay_router
from api.routes.runtime_deploy import router as runtime_deploy_router
from api.routes.simulation import router as simulation_router
from api.routes.st_verify import router as st_verify_router
from api.routes.uploads import router as uploads_router
from db.postgres import postgres_client

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


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "CrossLayerX project-based backend running"}


@app.on_event("startup")
def startup() -> None:
    postgres_client.init_schema()


app.include_router(health_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(parse_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(replay_router, prefix="/api")
app.include_router(runtime_deploy_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(logic_router, prefix="/api")
app.include_router(io_mapping_router, prefix="/api")
app.include_router(project_io_mapping_router, prefix="/api")
app.include_router(deploy_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(st_verify_router, prefix="/api")