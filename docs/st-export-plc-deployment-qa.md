# ST Export + PLC Deployment Integration QA Checklist

## 1) Export Readiness Validation
- [ ] Open **Export Logic** dialog with a valid project selected.
- [ ] Confirm readiness summary shows status for: plant model, loops, IO mapping, ST logic.
- [ ] Confirm blocking readiness errors disable **Generate Export**.
- [ ] Confirm warnings are visible but do not block export when allowed.
- [ ] Confirm unsupported target returns structured error.

## 2) Package Generation
- [ ] Select each target (`siemens`, `rockwell`, `codesys`, `beckhoff`, `openplc`, `generic_st`) and run export.
- [ ] Confirm export returns: export id, vendor, generated timestamp, artifact name.
- [ ] Confirm package preview lists metadata + source ST + vendor artifact entries.
- [ ] Confirm download succeeds and archive is non-empty.

## 3) Target Selection + Source Clarity
- [ ] Verify source selector supports **Live Current State** and **Saved Snapshot / Version**.
- [ ] For version mode, verify selected version tag is shown and used in export metadata.
- [ ] Confirm export source is explicit in UI and result summary.
- [ ] Confirm missing version selection blocks export in version mode.

## 4) Manifest + Traceability Correctness
- [ ] Extract downloaded package and verify `metadata/export_manifest.json` exists.
- [ ] Confirm manifest includes: `project_id`, `source_mode`, `source_version_id`, `export_target`, `export_timestamp`.
- [ ] Confirm manifest includes: `st_files`, `referenced_tags`, `mapped_io_channels`, `loops_represented`.
- [ ] Verify `metadata/st_block_traceability.json` maps blocks to source file, tags, and IO channel references.
- [ ] Verify `metadata/tag_mapping.json` and `metadata/io_mapping_summary.json` are present and populated.

## 5) Deployment Readiness + Handoff States
- [ ] With export ready, verify deployment panel state transitions to `ready_to_deploy`.
- [ ] Run **Prepare Handoff** and confirm logs include package handoff path.
- [ ] Run **Trigger Runtime Deploy** and confirm state resolves to `deployed` or `failed`.
- [ ] Confirm user-facing logs/errors are visible in dialog for each handoff run.

## 6) Error Handling Coverage
- [ ] Missing ST files -> readiness blocked with explicit error.
- [ ] Missing IO mapping -> readiness blocked with explicit error.
- [ ] Blocking mapping errors -> readiness blocked with explicit error.
- [ ] Missing required tags -> readiness blocked with explicit error.
- [ ] Empty export output or missing artifact -> structured failure surfaced.
- [ ] Backend timeout/failure -> dialog shows error toast and state `failed`.
- [ ] Invalid project/export context mismatch -> deployment handoff blocked with structured error.

## 7) Deployable vs Simulated Handoff Validation
- [ ] Confirm **Prepare Handoff** is always safe and does not start runtime.
- [ ] Confirm runtime deploy trigger executes existing runtime pipeline (`runtime_manager.deploy`) when requested.
- [ ] Confirm deployment state reflects actual runtime outcome, not silent success assumptions.
