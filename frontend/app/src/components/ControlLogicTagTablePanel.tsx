import { useDeferredValue, useMemo, useState } from "react";
import { FileCode2, Sparkles, X } from "lucide-react";
import type { GeneratedLogicFile, TagIntelligenceEditorCommand } from "./CodeExplorerPanel";
import { getLogicTagIntelligenceSource } from "../utils/logicTagIntelligenceSource";
import { normalizeLogicPath } from "../utils/controlLogicTransforms";
import type { InlineTagIntelligenceEntry, InlineTagIntelligenceLineReference, InlineTagIntelligenceReference } from "../utils/controlLogicIntelligence";
import TagIntelligenceDetailView from "./TagIntelligenceDetailView";
import "../styles/control-logic-quick-edit-panel.css";

type ControlLogicTagTablePanelProps = {
  files: GeneratedLogicFile[];
  selectedFilePath?: string | null;
  onDispatchEditorCommand?: (command: TagIntelligenceEditorCommand) => void;
};

function getActiveFile(files: GeneratedLogicFile[], selectedFilePath?: string | null): GeneratedLogicFile | null {
  if (!files.length) {
    return null;
  }
  const normalizedSelectedPath = selectedFilePath ? normalizeLogicPath(selectedFilePath) : "";
  return files.find((file) => normalizeLogicPath(file.path) === normalizedSelectedPath) ?? files[0] ?? null;
}

export default function ControlLogicTagTablePanel({
  files,
  selectedFilePath = null,
  onDispatchEditorCommand,
}: ControlLogicTagTablePanelProps) {
  const [searchInput, setSearchInput] = useState("");
  const [showShortcutHelp, setShowShortcutHelp] = useState(false);
  const [expandedTagName, setExpandedTagName] = useState<string | null>(null);
  const [activeUsageIndexByTag, setActiveUsageIndexByTag] = useState<Record<string, number>>({});
  const deferredSearchInput = useDeferredValue(searchInput);

  const activeFile = useMemo(() => getActiveFile(files, selectedFilePath), [files, selectedFilePath]);
  const activeContent = activeFile?.content || "";
  const tagIntelligenceSource = useMemo(() => getLogicTagIntelligenceSource(activeContent), [activeContent]);
  const visibleTagEntries = useMemo(() => {
    const searchText = deferredSearchInput.trim().toLowerCase();
    const entries = tagIntelligenceSource.entries;
    if (!searchText) {
      return entries;
    }
    return entries.filter((entry) => {
      const lineReferenceText = entry.allLineReferences.map((reference) => String(reference.line)).join(" ");
      return [entry.tagName, entry.dataType || "", lineReferenceText].join(" ").toLowerCase().includes(searchText);
    });
  }, [deferredSearchInput, tagIntelligenceSource]);

  const dispatchCommand = (entry: InlineTagIntelligenceEntry, action: TagIntelligenceEditorCommand["action"], reference?: InlineTagIntelligenceReference): void => {
    if (!activeFile || !onDispatchEditorCommand) {
      return;
    }
    onDispatchEditorCommand({
      file: activeFile.path,
      tagName: entry.tagName,
      action,
      line: reference?.line,
      column: reference?.column,
      nonce: Date.now(),
    });
  };

  const focusReference = (entry: InlineTagIntelligenceEntry, reference: InlineTagIntelligenceReference): void => {
    setActiveUsageIndexByTag((current) => ({
      ...current,
      [entry.canonicalName]: Math.max(
        0,
        entry.usageContexts.all.findIndex((item) => item.line === reference.line && item.column === reference.column)
      ),
    }));
    dispatchCommand(entry, "focus-reference", reference);
  };

  const focusLineReference = (entry: InlineTagIntelligenceEntry, lineReference: InlineTagIntelligenceLineReference): void => {
    const target =
      (entry.declarationLocation.reference && entry.declarationLocation.reference.line === lineReference.line ? entry.declarationLocation.reference : null) ??
      entry.usageContexts.all.find((reference) => reference.line === lineReference.line) ??
      null;
    if (!target) {
      return;
    }
    focusReference(entry, target);
  };

  return (
    <aside className="control-logic-tag-table-panel" aria-label="Tag Table">
      <header className="control-logic-tag-table-panel-header">
        <div className="control-logic-quick-edit-section-header">
          <FileCode2 size={15} />
          <h4>Tag Table</h4>
        </div>
        <span className="control-logic-tag-table-count">
          {visibleTagEntries.length} / {tagIntelligenceSource.entries.length}
        </span>
      </header>

      <div className="control-logic-tag-table-panel-body">
        <input
          className="modal-input control-logic-tag-table-search"
          type="text"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Search tag, type, or line..."
          aria-label="Filter tag table"
        />

        <button
          className="control-logic-tag-table-shortcuts-btn"
          type="button"
          onClick={() => setShowShortcutHelp(true)}
        >
          <Sparkles size={14} />
          <span>Keyboard Shortcuts</span>
        </button>

        <div className="control-logic-tag-table-list" role="list" aria-label="Detected tags in current logic file">
          {visibleTagEntries.length > 0 ? (
            visibleTagEntries.map((entry) => {
              const isExpanded = expandedTagName === entry.canonicalName;
              const activeUsageIndex = activeUsageIndexByTag[entry.canonicalName] ?? 0;
              return (
                <div key={entry.canonicalName} className="control-logic-tag-table-entry" role="listitem">
                  <div
                    className="control-logic-tag-table-row"
                    onClick={() => {
                      setExpandedTagName((current) => (current === entry.canonicalName ? null : entry.canonicalName));
                      setActiveUsageIndexByTag((current) => ({ ...current, [entry.canonicalName]: current[entry.canonicalName] ?? 0 }));
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setExpandedTagName((current) => (current === entry.canonicalName ? null : entry.canonicalName));
                        setActiveUsageIndexByTag((current) => ({ ...current, [entry.canonicalName]: current[entry.canonicalName] ?? 0 }));
                      }
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <span className="control-logic-tag-table-primary">{entry.tagName}</span>
                    <span className="control-logic-tag-table-detail">({entry.dataType || "Undeclared"})</span>
                    <span className="control-logic-tag-table-separator">|</span>
                    <span className="control-logic-tag-table-detail">
                      {entry.totalUsageCount} use{entry.totalUsageCount === 1 ? "" : "s"}
                    </span>
                    <span className="control-logic-tag-table-separator">|</span>
                    <span className="control-logic-tag-table-inline-lines">
                      (
                      {entry.allLineReferences.length > 0
                        ? entry.allLineReferences.map((reference, index) => (
                            <button
                              key={`${entry.canonicalName}-line-${reference.line}`}
                              className="control-logic-tag-table-inline-line-btn"
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                setExpandedTagName(entry.canonicalName);
                                focusLineReference(entry, reference);
                              }}
                            >
                              {reference.line}
                              {index < entry.allLineReferences.length - 1 ? ", " : ""}
                            </button>
                          ))
                        : "-"}
                      )
                    </span>
                  </div>
                  {isExpanded ? (
                    <div className="control-logic-tag-table-detail-shell">
                      <TagIntelligenceDetailView
                        matchedTagName={entry.tagName}
                        info={entry}
                        activeUsageIndex={activeUsageIndex}
                        usageOccurrences={entry.usageContexts.all}
                        onFocusReference={(reference) => focusReference(entry, reference)}
                        onFocusLineReference={(lineReference) => focusLineReference(entry, lineReference)}
                        onJumpToDefinition={() => {
                          const reference = entry.declarationLocation.reference ?? entry.usageContexts.all[0];
                          if (reference) {
                            setActiveUsageIndexByTag((current) => ({
                              ...current,
                              [entry.canonicalName]: Math.max(
                                0,
                                entry.usageContexts.all.findIndex((item) => item.line === reference.line && item.column === reference.column)
                              ),
                            }));
                          }
                          dispatchCommand(entry, "jump-to-definition", reference ?? undefined);
                        }}
                        onHighlightAllUsages={() => {
                          dispatchCommand(entry, "highlight-all-usages");
                        }}
                        onPreviousUsage={() => {
                          if (entry.usageContexts.all.length === 0) {
                            return;
                          }
                          const nextIndex = (activeUsageIndex - 1 + entry.usageContexts.all.length) % entry.usageContexts.all.length;
                          setActiveUsageIndexByTag((current) => ({ ...current, [entry.canonicalName]: nextIndex }));
                          dispatchCommand(entry, "previous-usage");
                        }}
                        onNextUsage={() => {
                          if (entry.usageContexts.all.length === 0) {
                            return;
                          }
                          const nextIndex = (activeUsageIndex + 1) % entry.usageContexts.all.length;
                          setActiveUsageIndexByTag((current) => ({ ...current, [entry.canonicalName]: nextIndex }));
                          dispatchCommand(entry, "next-usage");
                        }}
                      />
                    </div>
                  ) : null}
                </div>
              );
            })
          ) : (
            <div className="control-logic-tag-table-empty">No tags match the current filter.</div>
          )}
        </div>
      </div>

      {showShortcutHelp ? (
        <div className="modal-backdrop" onClick={() => setShowShortcutHelp(false)}>
          <div className="modal-card control-logic-shortcuts-modal" onClick={(event) => event.stopPropagation()}>
            <div className="control-logic-shortcuts-modal-header">
              <div>
                <p className="control-logic-shortcuts-modal-eyebrow">Keyboard-first logic editing</p>
                <h3>Keyboard Shortcuts</h3>
              </div>
              <button
                className="control-logic-shortcuts-modal-close"
                type="button"
                onClick={() => setShowShortcutHelp(false)}
                aria-label="Close keyboard shortcuts"
              >
                <X size={14} />
              </button>
            </div>

            <div className="control-logic-shortcuts-list">
              <div className="control-logic-shortcuts-item">
                <span className="control-logic-shortcuts-kbd">Cmd/Ctrl + K</span>
                <div>
                  <strong>Open Command Bar</strong>
                </div>
              </div>
              <div className="control-logic-shortcuts-item">
                <span className="control-logic-shortcuts-kbd">Cmd/Ctrl + Shift + F</span>
                <div>
                  <strong>Find &amp; Highlight</strong>
                </div>
              </div>
              <div className="control-logic-shortcuts-item">
                <span className="control-logic-shortcuts-kbd">Cmd/Ctrl + .</span>
                <div>
                  <strong>Quick Actions on Tag</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  );
}