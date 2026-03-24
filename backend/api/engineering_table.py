from fastapi import APIRouter

from models.engineering_table import EngineeringTableRequest, EngineeringTableResponse
from services.engineering_table_parser import engineering_table_parser

router = APIRouter(prefix="/plant-model", tags=["engineering-table"])


@router.post("/engineering-table", response_model=EngineeringTableResponse)
def engineering_table(payload: EngineeringTableRequest) -> EngineeringTableResponse:
    return engineering_table_parser.build(payload)
