import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, FileCode2 } from "lucide-react";
import { toast } from "react-hot-toast";
import type { GeneratedLogicFile, STDiagnosticMarker } from "./CodeExplorerPanel";
import {
  BULK_EDIT_ACTIONS,
  ST_TYPE_OPTIONS,
  applyBulkEditToLogic,
  extractIdentifierOptions,
  extractNumericTargets,
  extractTypeOptions,
  normalizeLogicPath,
  renameIdentifierInLogic,
  updateDeclarationTypeInLogic,
  updateNumericTargetInLogic,
  type TransformationResult,
  type BulkEditAction,
} from "../utils/controlLogicTransforms";
import {
  VALIDATION_ISSUE_LABELS,
  validateStructuredTextIssues,
  type StructuredTextValidationIssue,
} from "../utils/controlLogicValidation";
import type { LogicSnapshotSource } from "../utils/logicSnapshots";
import "../styles/control-logic-quick-edit-panel.css";

type ControlLogicQuickEditPanelProps = {
  files: GeneratedLogicFile[];
  selectedFilePath?: string | null;
  diagnosticsByFile?: Record<string, STDiagnosticMarker[]>;
  loading?: boolean;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  onUpdateSelectedFileContent?: (nextContent: string, options?: { source?: LogicSnapshotSource }) => void;
  onJumpToLocation?: (location: { file: string; line: number; column: number }) => void;
};

const PANEL_TITLE = "Quick Edit + Validate";

const toDisplayName = (path: string): string => {
  const parts = normalizeLogicPath(path).split("/").filter(Boolean);
  return parts[parts.length - 1] || "main.st";
};

export default function ControlLogicQuickEditPanel({
  files,
  selectedFilePath = null,
  diagnosticsByFile = {},
  loading = false,
  collapsed = false,
  onCollapsedChange,
  onUpdateSelectedFileContent,
  onJumpToLocation,
}: ControlLogicQuickEditPanelProps) {
  const [showValidationResults, setShowValidationResults] = useState<boolean>(false);
  const [renameFrom, setRenameFrom] = useState<string>("");
  const [renameTo, setRenameTo] = useState<string>("");
  const [typeTarget, setTypeTarget] = useState<string>("");
  const [nextType, setNextType] = useState<string>(ST_TYPE_OPTIONS[0] || "BOOL");
  const [numericTarget, setNumericTarget] = useState<string>("");
  const [numericValue, setNumericValue] = useState<string>("");
  const [deviceFrom, setDeviceFrom] = useState<string>("");
  const [deviceTo, setDeviceTo] = useState<string>("");
  const [signalFrom, setSignalFrom] = useState<string>("");
  const [signalTo, setSignalTo] = useState<string>("");
  const [bulkTarget, setBulkTarget] = useState<string>("");
  const [bulkAction, setBulkAction] = useState<BulkEditAction>("rename");
  const [bulkValue, setBulkValue] = useState<string>("");

  const normalizedDiagnosticsByFile = useMemo<Record<string, STDiagnosticMarker[]>>(() => {
    const output: Record<string, STDiagnosticMarker[]> = {};
    for (const [rawPath, markers] of Object.entries(diagnosticsByFile)) {
      const normalizedPath = normalizeLogicPath(rawPath);
      output[normalizedPath] = markers;

      const pathParts = normalizedPath.split("/");
      if (pathParts[0] === "control_logic") {
        const stripped = pathParts.slice(1).join("/");
        if (stripped) {
          output[stripped] = markers;
        }
      }
    }
    return output;
  }, [diagnosticsByFile]);

  const activeFile = useMemo<GeneratedLogicFile | null>(() => {
    if (!files.length) {
      return null;
    }

    const normalizedSelectedPath = selectedFilePath ? normalizeLogicPath(selectedFilePath) : "";
    return files.find((file) => normalizeLogicPath(file.path) === normalizedSelectedPath) ?? files[0] ?? null;
  }, [files, selectedFilePath]);

  const activeContent = activeFile?.content || "";
  const deferredActiveContent = useDeferredValue(activeContent);

  const identifierOptions = useMemo(() => extractIdentifierOptions(activeContent), [activeContent]);
  const numericTargets = useMemo(() => extractNumericTargets(activeContent), [activeContent]);
  const typeOptions = useMemo(() => extractTypeOptions(activeContent), [activeContent]);
  const validationResult = useMemo(() => validateStructuredTextIssues(deferredActiveContent), [deferredActiveContent]);
  const validationIssues = validationResult.issues;

  const activeFileDiagnostics = useMemo<STDiagnosticMarker[]>(() => {
    if (!activeFile) {
      return [];
    }
    return normalizedDiagnosticsByFile[normalizeLogicPath(activeFile.path)] ?? [];
  }, [activeFile, normalizedDiagnosticsByFile]);

  useEffect(() => {
    if (!identifierOptions.length) {
      setRenameFrom("");
      setTypeTarget("");
      setDeviceFrom("");
      setDeviceTo("");
      setSignalFrom("");
      setSignalTo("");
      setBulkTarget("");
      return;
    }

    setRenameFrom((current) => (current && identifierOptions.includes(current) ? current : identifierOptions[0] || ""));
    setTypeTarget((current) => (current && identifierOptions.includes(current) ? current : identifierOptions[0] || ""));
    setDeviceFrom((current) => (current && identifierOptions.includes(current) ? current : identifierOptions[0] || ""));
    setDeviceTo((current) => {
      if (current && identifierOptions.includes(current)) {
        return current;
      }
      return identifierOptions[1] || identifierOptions[0] || "";
    });
    setSignalFrom((current) => (current && identifierOptions.includes(current) ? current : identifierOptions[0] || ""));
    setSignalTo((current) => {
      if (current && identifierOptions.includes(current)) {
        return current;
      }
      return identifierOptions[1] || identifierOptions[0] || "";
    });
    setBulkTarget((current) => (current && identifierOptions.includes(current) ? current : identifierOptions[0] || ""));
  }, [identifierOptions]);

  useEffect(() => {
    if (!numericTargets.length) {
      setNumericTarget("");
      setNumericValue("");
      return;
    }

    setNumericTarget((current) => {
      const nextTarget = current && numericTargets.some((item) => item.name === current) ? current : numericTargets[0]?.name || "";
      return nextTarget;
    });
  }, [numericTargets]);

  useEffect(() => {
    if (!numericTarget) {
      return;
    }
    const selectedNumericTarget = numericTargets.find((item) => item.name === numericTarget);
    if (selectedNumericTarget) {
      setNumericValue(selectedNumericTarget.rawValue);
    }
  }, [numericTarget, numericTargets]);

  useEffect(() => {
    if (!typeOptions.length) {
      setNextType(ST_TYPE_OPTIONS[0] || "BOOL");
      return;
    }
    setNextType((current) => (current && typeOptions.includes(current) ? current : typeOptions[0] || ST_TYPE_OPTIONS[0] || "BOOL"));
  }, [typeOptions]);

  const errorCount = activeFileDiagnostics.filter((marker) => marker.severity === "error").length;
  const warningCount = activeFileDiagnostics.length - errorCount;
  const activeFileLabel = activeFile ? toDisplayName(activeFile.path) : "No file selected";
  const activeFilePath = activeFile ? normalizeLogicPath(activeFile.path) : "Waiting for an ST file";

  const selectedNumericTargetMeta = numericTargets.find((item) => item.name === numericTarget) ?? null;
  const canApply = Boolean(activeFile && onUpdateSelectedFileContent);

  const renamePreview = useMemo(() => renameIdentifierInLogic(activeContent, renameFrom, renameTo), [activeContent, renameFrom, renameTo]);
  const typePreview = useMemo(() => updateDeclarationTypeInLogic(activeContent, typeTarget, nextType), [activeContent, nextType, typeTarget]);
  const numericPreview = useMemo(() => updateNumericTargetInLogic(activeContent, numericTarget, numericValue), [activeContent, numericTarget, numericValue]);
  const deviceSwapPreview = useMemo(() => renameIdentifierInLogic(activeContent, deviceFrom, deviceTo), [activeContent, deviceFrom, deviceTo]);
  const signalRemapPreview = useMemo(() => renameIdentifierInLogic(activeContent, signalFrom, signalTo), [activeContent, signalFrom, signalTo]);
  const bulkPreview = useMemo(
    () => applyBulkEditToLogic(activeContent, { target: bulkTarget, action: bulkAction, value: bulkValue }),
    [activeContent, bulkAction, bulkTarget, bulkValue]
  );

  const handleValidationIssueClick = (issue: StructuredTextValidationIssue): void => {
    if (!activeFile || !onJumpToLocation) {
      return;
    }
    onJumpToLocation({
      file: activeFile.path,
      line: issue.line,
      column: issue.column,
    });
  };

  const applyUpdatedContent = (result: TransformationResult, successMessage: string): void => {
    if (!canApply || !activeFile || !onUpdateSelectedFileContent) {
      toast.error("No active logic file is available.", { className: "industrial-toast industrial-toast-error" });
      return;
    }

    if (result.content === activeFile.content) {
      toast.error("No matching edits were found in the active file.", { className: "industrial-toast industrial-toast-error" });
      return;
    }

    onUpdateSelectedFileContent(result.content, { source: "quick-edit" });
    if (result.changedLines.length > 0 && onJumpToLocation) {
      onJumpToLocation({
        file: activeFile.path,
        line: result.changedLines[0],
        column: 1,
      });
    }
    toast.success(successMessage, { className: "industrial-toast" });
  };

  const applyRename = (): void => {
    const result = renameIdentifierInLogic(activeContent, renameFrom, renameTo);
    if (!result.changed || result.error) {
      toast.error(result.error || "Rename could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `Tag updated across ${result.changeCount} instances.`);
  };

  const applyTypeChange = (): void => {
    const result = updateDeclarationTypeInLogic(activeContent, typeTarget, nextType);
    if (!result.changed || result.error) {
      toast.error(result.error || "Type update could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `Type updated on ${result.changeCount} declaration${result.changeCount === 1 ? "" : "s"}.`);
  };

  const applyNumericChange = (): void => {
    const result = updateNumericTargetInLogic(activeContent, numericTarget, numericValue);
    if (!result.changed || result.error) {
      toast.error(result.error || "Numeric update could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `Constant updated across ${result.changeCount} assignment${result.changeCount === 1 ? "" : "s"}.`);
  };

  const applyDeviceSwap = (): void => {
    const result = renameIdentifierInLogic(activeContent, deviceFrom, deviceTo);
    if (!result.changed || result.error) {
      toast.error(result.error || "Device swap could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `Device updated across ${result.changeCount} instances.`);
  };

  const applySignalRemap = (): void => {
    const result = renameIdentifierInLogic(activeContent, signalFrom, signalTo);
    if (!result.changed || result.error) {
      toast.error(result.error || "Signal remap could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `Signal remapped across ${result.changeCount} instances.`);
  };

  const applyBulkEdit = (): void => {
    const result = applyBulkEditToLogic(activeContent, {
      target: bulkTarget,
      action: bulkAction,
      value: bulkValue,
    });
    if (!result.changed || result.error) {
      toast.error(result.error || "Bulk edit could not be applied.", { className: "industrial-toast industrial-toast-error" });
      return;
    }
    applyUpdatedContent(result, `${BULK_EDIT_ACTIONS.find((item) => item.value === bulkAction)?.label || "Bulk edit"} applied across ${result.changeCount} change${result.changeCount === 1 ? "" : "s"}.`);
  };

  const renderPreview = (preview: TransformationResult, idleMessage: string) => {
    if (preview.error) {
      return <p className="control-logic-quick-edit-preview is-error">{preview.error}</p>;
    }
    if (!preview.changed) {
      return <p className="control-logic-quick-edit-preview">{idleMessage}</p>;
    }
    return (
      <p className="control-logic-quick-edit-preview is-ready">
        Pending: {preview.changeCount} change{preview.changeCount === 1 ? "" : "s"} across {preview.changedLines.length} line{preview.changedLines.length === 1 ? "" : "s"}.
      </p>
    );
  };

  return (
    <aside
      className={`control-logic-quick-edit-panel${collapsed ? " is-collapsed" : ""}`}
      aria-label={PANEL_TITLE}
    >
      <button
        className="control-logic-quick-edit-toggle"
        type="button"
        aria-expanded={!collapsed}
        aria-controls="control-logic-quick-edit-panel-body"
        onClick={() => {
          onCollapsedChange?.(!collapsed);
        }}
      >
        <span className="control-logic-quick-edit-toggle-icon" aria-hidden="true">
          {collapsed ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </span>
        <span className="control-logic-quick-edit-toggle-copy">
          <span className="control-logic-quick-edit-toggle-title">{PANEL_TITLE}</span>
          <span className="control-logic-quick-edit-toggle-meta">{activeFileLabel}</span>
        </span>
      </button>

      <div id="control-logic-quick-edit-panel-body" className="control-logic-quick-edit-card">
        <header className="control-logic-quick-edit-header">
          <div>
            <p className="control-logic-quick-edit-eyebrow">Control logic utility</p>
            <h3>{PANEL_TITLE}</h3>
          </div>
          <button
            className="control-logic-quick-edit-header-btn"
            type="button"
            aria-label="Collapse quick edit panel"
            onClick={() => {
              onCollapsedChange?.(true);
            }}
          >
            <ChevronRight size={16} />
          </button>
        </header>

        <div className="control-logic-quick-edit-body">
          <section className="control-logic-quick-edit-section control-logic-quick-edit-validation-shell">
            <button
              className="command-btn primary control-logic-quick-edit-validation-trigger"
              type="button"
              onClick={() => {
                setShowValidationResults((current) => !current);
              }}
              disabled={!activeFile}
              aria-expanded={showValidationResults}
            >
              Validate & Highlight Issues
            </button>
            {showValidationResults ? (
              <div className="control-logic-quick-edit-validation-results">
                <div className="control-logic-quick-edit-validation-summary">
                  <span>{validationIssues.length} issues</span>
                  <span>{validationResult.stats.declarations} declarations</span>
                  <span>{validationResult.stats.references} references</span>
                </div>
                {validationIssues.length > 0 ? (
                  <div className="control-logic-quick-edit-issue-list" role="list">
                    {validationIssues.map((issue) => (
                      <button
                        key={issue.id}
                        className="control-logic-quick-edit-issue-item"
                        type="button"
                        role="listitem"
                        onClick={() => handleValidationIssueClick(issue)}
                      >
                        <span className={`control-logic-quick-edit-issue-type type-${issue.type}`}>
                          {VALIDATION_ISSUE_LABELS[issue.type]}
                        </span>
                        <strong>{issue.name}</strong>
                        <span className="control-logic-quick-edit-issue-line">Line {issue.line}</span>
                        <code>{issue.snippet}</code>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="control-logic-quick-edit-validation-empty">
                    <CheckCircle2 size={15} />
                    <span>No validation issues detected in the current file.</span>
                  </div>
                )}
              </div>
            ) : null}
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <FileCode2 size={15} />
              <h4>Active file</h4>
            </div>
            <div className="control-logic-quick-edit-metric-grid">
              <div className="control-logic-quick-edit-stat">
                <span className="control-logic-quick-edit-stat-label">File</span>
                <strong>{activeFileLabel}</strong>
              </div>
            </div>
            <p className="control-logic-quick-edit-path">{activeFilePath}</p>
            <p className="control-logic-quick-edit-note">
              This panel is bound to the same ST file selection as the editor and updates immediately when the open file changes.
            </p>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              {errorCount > 0 || warningCount > 0 ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
              <h4>Validation snapshot</h4>
            </div>
            <div className="control-logic-quick-edit-metric-grid compact">
              <div className="control-logic-quick-edit-stat status-critical">
                <span className="control-logic-quick-edit-stat-label">Errors</span>
                <strong>{errorCount}</strong>
              </div>
              <div className="control-logic-quick-edit-stat status-warning">
                <span className="control-logic-quick-edit-stat-label">Warnings</span>
                <strong>{warningCount}</strong>
              </div>
              <div className="control-logic-quick-edit-stat">
                <span className="control-logic-quick-edit-stat-label">Workspace files</span>
                <strong>{files.length}</strong>
              </div>
            </div>
            <p className="control-logic-quick-edit-note">
              {loading
                ? "Validation context is refreshing with the latest generation run."
                : activeFile
                  ? "This shell is ready for file-scoped validation and quick-edit actions in the next step."
                  : "Generate logic to populate the workspace and activate file-scoped utilities."}
            </p>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>Global Tag Rename</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>Old tag</span>
                <input
                  className="modal-input"
                  list="control-logic-tag-options"
                  value={renameFrom}
                  onChange={(event) => setRenameFrom(event.target.value)}
                  placeholder="Pump_1"
                />
              </label>
              <label className="control-logic-quick-edit-field">
                <span>New tag</span>
                <input
                  className="modal-input"
                  value={renameTo}
                  onChange={(event) => setRenameTo(event.target.value)}
                  placeholder="Pump_2"
                />
              </label>
            </div>
            {renderPreview(renamePreview, "Choose a source and replacement tag to preview the rename scope.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applyRename}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>I/O Type Toggle</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>Selected tag</span>
                <select className="modal-input" value={typeTarget} onChange={(event) => setTypeTarget(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field">
                <span>Type</span>
                <select className="modal-input" value={nextType} onChange={(event) => setNextType(event.target.value)}>
                  {typeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {renderPreview(typePreview, "Select a declared tag and target type to preview the update.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applyTypeChange}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>Setpoint / Timer Editor</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>Constant</span>
                <select className="modal-input" value={numericTarget} onChange={(event) => setNumericTarget(event.target.value)}>
                  {numericTargets.map((option) => (
                    <option key={`${option.name}-${option.rawValue}`} value={option.name}>
                      {option.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field">
                <span>Value</span>
                <input
                  className="modal-input"
                  type="number"
                  step="any"
                  value={numericValue}
                  onChange={(event) => setNumericValue(event.target.value)}
                  placeholder="0"
                />
              </label>
            </div>
            <p className="control-logic-quick-edit-note">
              {selectedNumericTargetMeta
                ? `Current literal: ${selectedNumericTargetMeta.expression}`
                : "Select a numeric or timer-backed target from the active file."}
            </p>
            {renderPreview(numericPreview, "Select a numeric target and enter a replacement value to preview the edit.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applyNumericChange}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>Device Swap</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>From</span>
                <select className="modal-input" value={deviceFrom} onChange={(event) => setDeviceFrom(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field">
                <span>To</span>
                <select className="modal-input" value={deviceTo} onChange={(event) => setDeviceTo(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {renderPreview(deviceSwapPreview, "Select source and target devices to preview the swap.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applyDeviceSwap}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>Signal Remap</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>From</span>
                <select className="modal-input" value={signalFrom} onChange={(event) => setSignalFrom(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field">
                <span>To</span>
                <select className="modal-input" value={signalTo} onChange={(event) => setSignalTo(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {renderPreview(signalRemapPreview, "Select source and target signals to preview the remap.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applySignalRemap}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section">
            <div className="control-logic-quick-edit-section-header">
              <h4>Bulk Edit Mode</h4>
            </div>
            <div className="control-logic-quick-edit-form-grid compact">
              <label className="control-logic-quick-edit-field">
                <span>Target</span>
                <select className="modal-input" value={bulkTarget} onChange={(event) => setBulkTarget(event.target.value)}>
                  {identifierOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field">
                <span>Action</span>
                <select className="modal-input" value={bulkAction} onChange={(event) => setBulkAction(event.target.value as BulkEditAction)}>
                  {BULK_EDIT_ACTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="control-logic-quick-edit-field bulk-value-field">
                <span>{bulkAction === "type" ? "Type" : bulkAction === "value" ? "Numeric value" : "New value"}</span>
                {bulkAction === "type" ? (
                  <select className="modal-input" value={bulkValue} onChange={(event) => setBulkValue(event.target.value)}>
                    {typeOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="modal-input"
                    type={bulkAction === "value" ? "number" : "text"}
                    step={bulkAction === "value" ? "any" : undefined}
                    value={bulkValue}
                    onChange={(event) => setBulkValue(event.target.value)}
                    placeholder={bulkAction === "value" ? "42" : "Replacement value"}
                  />
                )}
              </label>
            </div>
            {renderPreview(bulkPreview, "Select a target, action, and replacement to preview the bulk edit.")}
            <button className="command-btn primary control-logic-quick-edit-apply" type="button" disabled={!canApply} onClick={applyBulkEdit}>
              Apply
            </button>
          </section>

          <section className="control-logic-quick-edit-section muted">
            <div className="control-logic-quick-edit-section-header">
              <ChevronLeft size={15} />
              <h4>Panel scope</h4>
            </div>
            <p className="control-logic-quick-edit-note">
              All edits apply only to the currently open logic file and write back into the underlying file model that drives the ST editor view.
            </p>
          </section>
        </div>
      </div>
      <datalist id="control-logic-tag-options">
        {identifierOptions.map((option) => (
          <option key={option} value={option} />
        ))}
      </datalist>
    </aside>
  );
}