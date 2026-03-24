# Engineering Table Integration Notes

## Backend
- New endpoint: `POST /api/plant-model/engineering-table`
- Route file: `backend/api/engineering_table.py`
- Parser service: `backend/services/engineering_table_parser.py`
- Pydantic schemas: `backend/models/engineering_table.py`
- App registration: `backend/main.py`

Request body:
```json
{
  "project_id": "<uuid>",
  "file_ids": [],
  "include_inferred": true,
  "max_flow_depth": 4
}
```

## Frontend
- New component: `frontend/app/src/components/plant/EngineeringTable.tsx`
- Helper component: `frontend/app/src/components/plant/EngineeringChip.tsx`
- API client wiring: `frontend/app/src/services/api.ts`
- Mount point in workspace table view: `frontend/app/src/pages/Dashboard.tsx`

## Existing workspace mount
`Dashboard` already toggles `Graph View` and `Table View` in the graph workspace. The table branch now renders `EngineeringTable` and fetches data from the new endpoint.

## Row action callbacks
`EngineeringTable` supports compact row actions via callback props:
- `onTraceSignal(row)`
- `onOpenControlLoop(row)`
- `onOpenIOMapping(row)`

`Dashboard` wires these callbacks to existing app behavior (Trace tab, Control Loops tab, IO Mapping tab) without changing the workspace layout.

## Filters and warnings
- Table-level filters are composable: global search + type + source + minimum confidence + orphan-only + controlled-only.
- Row-level `warnings` are now part of the normalized row shape and are rendered in both table and details panel.
