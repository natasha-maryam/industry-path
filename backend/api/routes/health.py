from fastapi import APIRouter

from db.influx import InfluxClient
from db.neo4j import Neo4jClient
from db.postgres import PostgresClient

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "services": {
            "postgres": PostgresClient().health(),
            "neo4j": Neo4jClient().health(),
            "influx": InfluxClient().health(),
        },
    }
