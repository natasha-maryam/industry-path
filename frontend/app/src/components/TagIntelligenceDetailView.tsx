import type {
  InlineTagIntelligenceEntry,
  InlineTagIntelligenceLineReference,
  InlineTagIntelligenceReference,
} from "../utils/controlLogicIntelligence";
import "../styles/code-explorer-panel.css";

type TagIntelligenceDetailViewProps = {
  matchedTagName: string;
  info: InlineTagIntelligenceEntry;
  activeUsageIndex: number;
  usageOccurrences: InlineTagIntelligenceReference[];
  onFocusReference: (reference: InlineTagIntelligenceReference) => void;
  onFocusLineReference: (lineReference: InlineTagIntelligenceLineReference) => void;
  onJumpToDefinition: () => void;
  onHighlightAllUsages: () => void;
  onPreviousUsage: () => void;
  onNextUsage: () => void;
};

export default function TagIntelligenceDetailView({
  matchedTagName,
  info,
  activeUsageIndex,
  usageOccurrences,
  onFocusReference,
  onFocusLineReference,
  onJumpToDefinition,
  onHighlightAllUsages,
  onPreviousUsage,
  onNextUsage,
}: TagIntelligenceDetailViewProps) {
  return (
    <>
      <div className="code-explorer-intel-popover-header">
        <strong>{matchedTagName}</strong>
        <span>{info.category}</span>
      </div>
      <div className="code-explorer-intel-popover-section">
        <span>Definition</span>
        <div className="code-explorer-intel-definition-layout">
          <div className="code-explorer-intel-field code-explorer-intel-field-full">
            <span>Tag</span>
            <strong>{matchedTagName}</strong>
          </div>
          <div className="code-explorer-intel-meta-grid">
            <div className="code-explorer-intel-field">
              <span>Type</span>
              <strong>{info.dataType || "Undeclared"}</strong>
            </div>
            <div className="code-explorer-intel-field">
              <span>First seen</span>
              {info.firstSeenLine ? (
                <button
                  className="code-explorer-intel-line-chip"
                  type="button"
                  onClick={() => {
                    const target = info.allLineReferences.find((reference) => reference.line === info.firstSeenLine);
                    if (target) {
                      onFocusLineReference(target);
                    }
                  }}
                >
                  Line {info.firstSeenLine}
                </button>
              ) : (
                <strong>Unknown</strong>
              )}
            </div>
          </div>
          <div className="code-explorer-intel-field code-explorer-intel-field-full">
            <span>Defined</span>
            {info.declarationLocation.line ? (
              <button className="code-explorer-intel-line-chip" type="button" onClick={() => info.declarationLocation.reference && onFocusReference(info.declarationLocation.reference)}>
                Line {info.declarationLocation.line}
              </button>
            ) : (
              <strong>No local declaration</strong>
            )}
          </div>
          <div className="code-explorer-intel-field code-explorer-intel-field-full">
            <span>Declaration</span>
            <code>{info.declarationLocation.snippet || "Identifier is used in this file without a local declaration."}</code>
          </div>
        </div>
      </div>
      <div className="code-explorer-intel-popover-section">
        <span>Usage</span>
        <div className="code-explorer-intel-usage-summary">
          <strong>
            {info.totalUsageCount} total usage{info.totalUsageCount === 1 ? "" : "s"}
          </strong>
          <span>
            {info.counts.writes} written · {info.counts.reads} read · {info.totalOccurrenceCount} total references
          </span>
        </div>
        <div className="code-explorer-intel-line-reference-row">
          <span>All line references</span>
          <div className="code-explorer-intel-line-reference-list">
            {info.allLineReferences.length > 0 ? (
              info.allLineReferences.map((lineReference) => (
                <button
                  key={`line-ref-${lineReference.line}`}
                  className="code-explorer-intel-line-chip"
                  type="button"
                  onClick={() => onFocusLineReference(lineReference)}
                >
                  Line {lineReference.line}
                </button>
              ))
            ) : (
              <p className="code-explorer-intel-empty">No line references in this file.</p>
            )}
          </div>
        </div>
        <div className="code-explorer-intel-reference-list split">
          <div className="code-explorer-intel-usage-group">
            <span>Assigned / Written</span>
            {info.usageContexts.written.length > 0 ? (
              info.usageContexts.written.map((occurrence) => (
                <button
                  key={`write-${occurrence.line}-${occurrence.column}`}
                  className="code-explorer-intel-reference-item"
                  type="button"
                  onClick={() => onFocusReference(occurrence)}
                >
                  <span>Line {occurrence.line}</span>
                  <code>{occurrence.snippet}</code>
                </button>
              ))
            ) : (
              <p className="code-explorer-intel-empty">No write contexts in this file.</p>
            )}
          </div>
          <div className="code-explorer-intel-usage-group">
            <span>Read / Used</span>
            {info.usageContexts.read.length > 0 ? (
              info.usageContexts.read.map((occurrence) => (
                <button
                  key={`read-${occurrence.line}-${occurrence.column}`}
                  className="code-explorer-intel-reference-item"
                  type="button"
                  onClick={() => onFocusReference(occurrence)}
                >
                  <span>Line {occurrence.line}</span>
                  <code>{occurrence.snippet}</code>
                </button>
              ))
            ) : (
              <p className="code-explorer-intel-empty">No read contexts in this file.</p>
            )}
          </div>
        </div>
      </div>
      <div className="code-explorer-intel-popover-section">
        <span>Actions</span>
        <div className="code-explorer-intel-actions">
          <button className="code-explorer-intel-action-btn" type="button" onClick={onJumpToDefinition}>
            Jump to Definition
          </button>
          <button className="code-explorer-intel-action-btn" type="button" onClick={onHighlightAllUsages}>
            Highlight All Usages
          </button>
          <button className="code-explorer-intel-action-btn" type="button" disabled={usageOccurrences.length === 0} onClick={onPreviousUsage}>
            Previous Usage
          </button>
          <button className="code-explorer-intel-action-btn" type="button" disabled={usageOccurrences.length === 0} onClick={onNextUsage}>
            Next Usage
          </button>
        </div>
        {usageOccurrences.length > 0 ? (
          <strong>
            Usage {Math.min(activeUsageIndex + 1, usageOccurrences.length)} of {usageOccurrences.length}
          </strong>
        ) : null}
      </div>
      {info.casingVariants.length > 1 ? (
        <div className="code-explorer-intel-popover-section">
          <span>Casing variants</span>
          <strong>{info.casingVariants.join(", ")}</strong>
        </div>
      ) : null}
    </>
  );
}