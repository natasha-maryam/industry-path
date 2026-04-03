from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from core.security import AuthContext, get_auth_context
from models.plant_genie import (
    PlantGenieAIBindingConnectResponse,
    PlantGenieAIBindingRequest,
    PlantGenieAIBindingResponse,
    PlantGenieAIConnectorCreateRequest,
    PlantGenieAIConnectorDeleteResponse,
    PlantGenieAIConnectorListResponse,
    PlantGenieAIConnectorResponse,
    PlantGenieAIConnectorTestResponse,
    PlantGenieAIConnectorUpdateRequest,
    PlantGeniePlantDataConnectorCreateRequest,
    PlantGeniePlantDataConnectorDeleteResponse,
    PlantGeniePlantDataConnectorListResponse,
    PlantGeniePlantDataOPCUABrowseRequest,
    PlantGeniePlantDataOPCUABrowseResponse,
    PlantGeniePlantDataConnectorResponse,
    PlantGeniePlantDataConnectorTestResponse,
    PlantGeniePlantDataHistorianBrowseRequest,
    PlantGeniePlantDataHistorianBrowseResponse,
    PlantGeniePlantDataHistorianBrowseItemResponse,
    PlantGeniePlantDataHistorianPreviewRequest,
    PlantGeniePlantDataHistorianPreviewResponse,
    PlantGeniePlantDataModbusPreviewRequest,
    PlantGeniePlantDataModbusPreviewResponse,
    PlantGeniePlantDataSQLColumnResponse,
    PlantGeniePlantDataSQLPreviewRequest,
    PlantGeniePlantDataSQLPreviewResponse,
    PlantGeniePlantDataSQLSchemaRequest,
    PlantGeniePlantDataSQLSchemaResponse,
    PlantGeniePlantDataSQLTableResponse,
    PlantGeniePlantDataConnectorUpdateRequest,
    PlantGenieQueryRequest,
    PlantGenieQueryResponse,
)
from services.plant_genie_ai_binding_service import plant_genie_ai_binding_service
from services.plant_genie_connector_service import (
    PlantGenieConnectorInvocationError,
    PlantGenieConnectorNotConfiguredError,
    plant_genie_connector_service,
)
from services.plant_genie_config import ensure_plant_genie_secret_storage_ready
from services.plant_genie_config_errors import SecretConfigurationError
from services.plant_genie_plant_data_runtime import plant_genie_plant_data_runtime
from services.plant_genie_plant_data_service import plant_genie_plant_data_connector_service


router = APIRouter(prefix="/plant-genie", tags=["plant-genie"])
logger = logging.getLogger(__name__)


@router.get("/connectors/ai", response_model=PlantGenieAIConnectorListResponse)
def list_ai_connectors(context: AuthContext = Depends(get_auth_context)) -> PlantGenieAIConnectorListResponse:
    connectors = plant_genie_connector_service.list_connectors(context.user_id)
    return PlantGenieAIConnectorListResponse(connectors=connectors)


@router.post("/connectors/ai", response_model=PlantGenieAIConnectorResponse)
def create_ai_connector(
    payload: PlantGenieAIConnectorCreateRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIConnectorResponse:
    try:
        ensure_plant_genie_secret_storage_ready(logger=logger, context="connector_create")
        return plant_genie_connector_service.create_connector(context.user_id, payload)
    except SecretConfigurationError as exc:
        logger.exception("Plant Genie AI connector secret storage misconfiguration during create for user=%s", context.user_id)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/connectors/ai/{connector_id}", response_model=PlantGenieAIConnectorResponse)
def update_ai_connector(
    connector_id: str,
    payload: PlantGenieAIConnectorUpdateRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIConnectorResponse:
    try:
        ensure_plant_genie_secret_storage_ready(logger=logger, context="connector_update")
        return plant_genie_connector_service.update_connector(context.user_id, connector_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connector not found") from exc
    except SecretConfigurationError as exc:
        logger.exception(
            "Plant Genie AI connector secret storage misconfiguration during update for user=%s connector=%s",
            context.user_id,
            connector_id,
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/connectors/ai/{connector_id}", response_model=PlantGenieAIConnectorDeleteResponse)
def delete_ai_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIConnectorDeleteResponse:
    try:
        plant_genie_connector_service.delete_connector(context.user_id, connector_id)
        return PlantGenieAIConnectorDeleteResponse(message="Connector deleted.")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connector not found") from exc


@router.post("/connectors/ai/{connector_id}/test", response_model=PlantGenieAIConnectorTestResponse)
def test_ai_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIConnectorTestResponse:
    try:
        connector, message = plant_genie_connector_service.test_connector(context.user_id, connector_id)
        return PlantGenieAIConnectorTestResponse(
            success=connector.health_status == "healthy",
            message=message,
            connector=connector,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connector not found") from exc
    except SecretConfigurationError as exc:
        logger.exception(
            "Plant Genie AI connector secret storage misconfiguration during test for user=%s connector=%s",
            context.user_id,
            connector_id,
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/connectors/ai/{connector_id}/activate", response_model=PlantGenieAIConnectorResponse)
def activate_ai_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIConnectorResponse:
    try:
        return plant_genie_connector_service.activate_connector(context.user_id, connector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connector not found") from exc


@router.get("/connectors/ai-binding", response_model=PlantGenieAIBindingResponse)
def get_ai_binding(
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIBindingResponse:
    return plant_genie_ai_binding_service.get_binding(context.user_id)


@router.put("/connectors/ai-binding", response_model=PlantGenieAIBindingConnectResponse)
def upsert_ai_binding(
    payload: PlantGenieAIBindingRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieAIBindingConnectResponse:
    try:
        binding = plant_genie_ai_binding_service.upsert_binding(context.user_id, payload)
        connector_name = binding.data_source_connector_name or "selected data source"
        return PlantGenieAIBindingConnectResponse(
            message=f"AI binding connected to {connector_name}.",
            binding=binding,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/connectors/plant-data", response_model=PlantGeniePlantDataConnectorListResponse)
def list_plant_data_connectors(context: AuthContext = Depends(get_auth_context)) -> PlantGeniePlantDataConnectorListResponse:
    connectors = plant_genie_plant_data_connector_service.list_connectors(context.user_id)
    return PlantGeniePlantDataConnectorListResponse(connectors=connectors)


@router.post("/connectors/plant-data", response_model=PlantGeniePlantDataConnectorResponse)
def create_plant_data_connector(
    payload: PlantGeniePlantDataConnectorCreateRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    try:
        created = plant_genie_plant_data_connector_service.create_connector(context.user_id, payload)
        if created.runtime.enabled:
            record = plant_genie_plant_data_connector_service.get_connector_record(context.user_id, created.id)
            plant_genie_plant_data_runtime.start_connector(record)
        return created
    except SecretConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/connectors/plant-data/{connector_id}", response_model=PlantGeniePlantDataConnectorResponse)
def update_plant_data_connector(
    connector_id: str,
    payload: PlantGeniePlantDataConnectorUpdateRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    try:
        updated = plant_genie_plant_data_connector_service.update_connector(context.user_id, connector_id, payload)
        if updated.runtime.enabled:
            record = plant_genie_plant_data_connector_service.get_connector_record(context.user_id, connector_id)
            plant_genie_plant_data_runtime.stop_connector(connector_id)
            plant_genie_plant_data_runtime.start_connector(record)
        return updated
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc
    except SecretConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/connectors/plant-data/{connector_id}", response_model=PlantGeniePlantDataConnectorDeleteResponse)
def delete_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorDeleteResponse:
    try:
        record = plant_genie_plant_data_connector_service.get_connector_record(context.user_id, connector_id)
        if record.enabled:
            plant_genie_plant_data_runtime.stop_connector(connector_id)
        plant_genie_plant_data_connector_service.delete_connector(context.user_id, connector_id)
        return PlantGeniePlantDataConnectorDeleteResponse(message="Plant data connector deleted.")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc


@router.post("/connectors/plant-data/{connector_id}/test", response_model=PlantGeniePlantDataConnectorTestResponse)
def test_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorTestResponse:
    try:
        record = plant_genie_plant_data_connector_service.get_connector_record(context.user_id, connector_id)
        healthy, message = plant_genie_plant_data_runtime.test_connector(record)
        connector = plant_genie_plant_data_connector_service.mark_test_result(
            context.user_id,
            connector_id,
            healthy=healthy,
            message=message,
        )
        return PlantGeniePlantDataConnectorTestResponse(success=healthy, message=message, connector=connector)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/connectors/plant-data/opcua/browse", response_model=PlantGeniePlantDataOPCUABrowseResponse)
def browse_plant_data_opcua(
    payload: PlantGeniePlantDataOPCUABrowseRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataOPCUABrowseResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.browse_opcua(payload.config, payload.secrets, payload.node_id)
        return PlantGeniePlantDataOPCUABrowseResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/sql/schema", response_model=PlantGeniePlantDataSQLSchemaResponse)
def plant_data_sql_schema(
    payload: PlantGeniePlantDataSQLSchemaRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataSQLSchemaResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.sql_schema(
            payload.config,
            payload.secrets,
            table_name=payload.table_name,
            table_schema=payload.table_schema,
        )
        return PlantGeniePlantDataSQLSchemaResponse(
            tables=[PlantGeniePlantDataSQLTableResponse(**table) for table in result.get("tables", [])],
            columns=[PlantGeniePlantDataSQLColumnResponse(**column) for column in result.get("columns", [])],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/sql/preview", response_model=PlantGeniePlantDataSQLPreviewResponse)
def preview_plant_data_sql(
    payload: PlantGeniePlantDataSQLPreviewRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataSQLPreviewResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.preview_sql(payload.config, payload.secrets, limit=payload.limit)
        return PlantGeniePlantDataSQLPreviewResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/modbus/preview", response_model=PlantGeniePlantDataModbusPreviewResponse)
def preview_plant_data_modbus(
    payload: PlantGeniePlantDataModbusPreviewRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataModbusPreviewResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.preview_modbus(payload.config, payload.secrets)
        return PlantGeniePlantDataModbusPreviewResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/historian/browse", response_model=PlantGeniePlantDataHistorianBrowseResponse)
def browse_plant_data_historian(
    payload: PlantGeniePlantDataHistorianBrowseRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataHistorianBrowseResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.browse_historian(payload.config, payload.secrets, query=payload.query, limit=payload.limit)
        return PlantGeniePlantDataHistorianBrowseResponse(
            items=[PlantGeniePlantDataHistorianBrowseItemResponse(**item) for item in result.get("items", [])]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/historian/preview", response_model=PlantGeniePlantDataHistorianPreviewResponse)
def preview_plant_data_historian(
    payload: PlantGeniePlantDataHistorianPreviewRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataHistorianPreviewResponse:
    _ = context
    try:
        result = plant_genie_plant_data_runtime.preview_historian(payload.config, payload.secrets)
        return PlantGeniePlantDataHistorianPreviewResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connectors/plant-data/{connector_id}/enable", response_model=PlantGeniePlantDataConnectorResponse)
def enable_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    try:
        response = plant_genie_plant_data_connector_service.set_enabled(context.user_id, connector_id, True)
        record = plant_genie_plant_data_connector_service.get_connector_record(context.user_id, connector_id)
        plant_genie_plant_data_runtime.start_connector(record)
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc


@router.post("/connectors/plant-data/{connector_id}/activate", response_model=PlantGeniePlantDataConnectorResponse)
def activate_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    return enable_plant_data_connector(connector_id, context)


@router.post("/connectors/plant-data/{connector_id}/disable", response_model=PlantGeniePlantDataConnectorResponse)
def disable_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    try:
        plant_genie_plant_data_runtime.stop_connector(connector_id)
        return plant_genie_plant_data_connector_service.set_enabled(context.user_id, connector_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant data connector not found") from exc


@router.post("/connectors/plant-data/{connector_id}/deactivate", response_model=PlantGeniePlantDataConnectorResponse)
def deactivate_plant_data_connector(
    connector_id: str,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGeniePlantDataConnectorResponse:
    return disable_plant_data_connector(connector_id, context)


@router.post("/query", response_model=PlantGenieQueryResponse)
def query_plant_genie(
    payload: PlantGenieQueryRequest,
    context: AuthContext = Depends(get_auth_context),
) -> PlantGenieQueryResponse:
    try:
        result = plant_genie_connector_service.query_active_connector(
            context.user_id,
            payload.prompt,
            payload.context.model_dump(),
        )
        return PlantGenieQueryResponse(**result)
    except PlantGenieConnectorNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PlantGenieConnectorInvocationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SecretConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc