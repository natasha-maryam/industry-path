import { useDeferredValue, useEffect, useId, useMemo, useRef, useState } from "react";
import { CheckCircle2, CornerDownLeft, Hash, PencilLine, Search, Tags } from "lucide-react";
import type { GeneratedLogicFile } from "./CodeExplorerPanel";
import type { InlineTagIntelligenceEntry } from "../utils/controlLogicIntelligence";
import { getLogicTagIntelligenceSource } from "../utils/logicTagIntelligenceSource";
import "../styles/logic-editor-command-palette.css";

type LogicEditorCommandPaletteProps = {
  isOpen: boolean;
  activeFile: GeneratedLogicFile | null;
  onClose: () => void;
  onJumpToLine: (lineNumber: number) => void;
  onJumpToDefinition: (tagName: string) => void;
  onHighlightUsages: (tagName: string) => void;
  onRenameTag: (from: string, to: string) => boolean;
  onValidateCurrentFile: () => void;
};

type CommandPaletteResult = {
  id: string;
  title: string;
  subtitle: string;
  kindLabel: string;
  icon: "line" | "tag" | "highlight" | "rename" | "validate";
  execute: () => void;
};

function parseRequestedLine(query: string): number | null {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    return null;
  }

  const directMatch = trimmedQuery.match(/^:?(\d+)$/);
  if (directMatch) {
    return Number.parseInt(directMatch[1] || "", 10);
  }

  const lineMatch = trimmedQuery.match(/^line\s+(\d+)$/i);
  if (lineMatch) {
    return Number.parseInt(lineMatch[1] || "", 10);
  }

  return null;
}

function getTargetLine(entry: InlineTagIntelligenceEntry): number | null {
  return entry.declarationLocation.line ?? entry.firstSeenLine ?? entry.allLineReferences[0]?.line ?? null;
}

export default function LogicEditorCommandPalette({
  isOpen,
  activeFile,
  onClose,
  onJumpToLine,
  onJumpToDefinition,
  onHighlightUsages,
  onRenameTag,
  onValidateCurrentFile,
}: LogicEditorCommandPaletteProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const renameInputRef = useRef<HTMLInputElement | null>(null);
  const listboxId = useId();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [renameTarget, setRenameTarget] = useState<InlineTagIntelligenceEntry | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const deferredQuery = useDeferredValue(query);

  const activeContent = activeFile?.content || "";
  const tagSource = useMemo(() => getLogicTagIntelligenceSource(activeContent), [activeContent]);
  const lineCount = useMemo(() => (activeContent ? activeContent.split(/\r?\n/).length : 0), [activeContent]);

  const results = useMemo<CommandPaletteResult[]>(() => {
    if (!activeFile || renameTarget) {
      return [];
    }

    const trimmedQuery = deferredQuery.trim().toLowerCase();
    const nextResults: CommandPaletteResult[] = [];

    if (!trimmedQuery || "validate current file".includes(trimmedQuery) || "validate".includes(trimmedQuery)) {
      nextResults.push({
        id: "validate-current-file",
        title: "Validate Current File",
        subtitle: activeFile.path,
        kindLabel: "Action",
        icon: "validate",
        execute: () => {
          onValidateCurrentFile();
          onClose();
        },
      });
    }

    const requestedLine = parseRequestedLine(deferredQuery);
    if (requestedLine && requestedLine >= 1 && requestedLine <= Math.max(1, lineCount)) {
      nextResults.push({
        id: `jump-line-${requestedLine}`,
        title: `Jump to line ${requestedLine}`,
        subtitle: activeFile.path,
        kindLabel: "Line",
        icon: "line",
        execute: () => {
          onJumpToLine(requestedLine);
          onClose();
        },
      });
    }

    const matchingEntries = tagSource.entries.filter((entry) => {
      if (!trimmedQuery) {
        return true;
      }
      const haystack = [
        entry.tagName,
        entry.dataType || "",
        entry.category,
        entry.allLineReferences.map((reference) => String(reference.line)).join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(trimmedQuery);
    });

    for (const entry of matchingEntries.slice(0, trimmedQuery ? 4 : 5)) {
      const targetLine = getTargetLine(entry);
      const locationLabel = targetLine ? `Line ${targetLine}` : "No local declaration";
      nextResults.push({
        id: `jump-tag-${entry.canonicalName}`,
        title: `Jump to ${entry.tagName}`,
        subtitle: `${locationLabel} · ${entry.totalUsageCount} use${entry.totalUsageCount === 1 ? "" : "s"}`,
        kindLabel: entry.dataType || "Tag",
        icon: "tag",
        execute: () => {
          onJumpToDefinition(entry.tagName);
          onClose();
        },
      });
      nextResults.push({
        id: `highlight-tag-${entry.canonicalName}`,
        title: `Highlight usages of ${entry.tagName}`,
        subtitle: `${entry.counts.writes} written · ${entry.counts.reads} read`,
        kindLabel: "Action",
        icon: "highlight",
        execute: () => {
          onHighlightUsages(entry.tagName);
          onClose();
        },
      });
      nextResults.push({
        id: `rename-tag-${entry.canonicalName}`,
        title: `Rename tag ${entry.tagName}`,
        subtitle: "Open inline rename",
        kindLabel: "Rename",
        icon: "rename",
        execute: () => {
          setRenameTarget(entry);
          setRenameValue(entry.tagName);
        },
      });
      if (nextResults.length >= 10) {
        break;
      }
    }

    return nextResults.slice(0, 10);
  }, [activeFile, deferredQuery, lineCount, onClose, onHighlightUsages, onJumpToDefinition, onJumpToLine, onValidateCurrentFile, renameTarget, tagSource.entries]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setQuery("");
    setActiveIndex(0);
    setRenameTarget(null);
    setRenameValue("");
    window.requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    });
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setActiveIndex((current) => Math.min(current, Math.max(0, results.length - 1)));
  }, [isOpen, results.length]);

  useEffect(() => {
    if (!renameTarget) {
      return;
    }
    window.requestAnimationFrame(() => {
      renameInputRef.current?.focus();
      renameInputRef.current?.select();
    });
  }, [renameTarget]);

  if (!isOpen || !activeFile) {
    return null;
  }

  const submitRename = (): void => {
    if (!renameTarget) {
      return;
    }
    const didRename = onRenameTag(renameTarget.tagName, renameValue.trim());
    if (didRename) {
      onClose();
      return;
    }
    window.requestAnimationFrame(() => {
      renameInputRef.current?.focus();
      renameInputRef.current?.select();
    });
  };

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>): void => {
    if (renameTarget) {
      if (event.key === "Escape") {
        event.preventDefault();
        setRenameTarget(null);
        setRenameValue("");
        window.requestAnimationFrame(() => {
          inputRef.current?.focus();
        });
      }
      if (event.key === "Enter") {
        event.preventDefault();
        submitRename();
      }
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (results.length > 0 ? (current + 1) % results.length : 0));
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => (results.length > 0 ? (current - 1 + results.length) % results.length : 0));
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      results[activeIndex]?.execute();
    }
  };

  const renderIcon = (icon: CommandPaletteResult["icon"]) => {
    switch (icon) {
      case "line":
        return <Hash size={15} />;
      case "highlight":
        return <Tags size={15} />;
      case "rename":
        return <PencilLine size={15} />;
      case "validate":
        return <CheckCircle2 size={15} />;
      case "tag":
      default:
        return <Search size={15} />;
    }
  };

  return (
    <div className="logic-editor-command-palette-backdrop" onMouseDown={onClose}>
      <div
        className="logic-editor-command-palette"
        role="dialog"
        aria-modal="true"
        aria-label="Logic editor command palette"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="logic-editor-command-palette-input-shell">
          <Search size={16} />
          <input
            ref={renameTarget ? renameInputRef : inputRef}
            className="logic-editor-command-palette-input"
            type="text"
            value={renameTarget ? renameValue : query}
            onChange={(event) => {
              if (renameTarget) {
                setRenameValue(event.target.value);
                return;
              }
              setQuery(event.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={onInputKeyDown}
            placeholder={renameTarget ? `Rename ${renameTarget.tagName} to...` : "Search tags, enter :42, or run actions"}
            aria-controls={renameTarget ? undefined : listboxId}
            aria-activedescendant={renameTarget ? undefined : results[activeIndex]?.id}
          />
          <span className="logic-editor-command-palette-file-pill">{activeFile.path}</span>
        </div>

        {renameTarget ? (
          <div className="logic-editor-command-palette-rename-panel">
            <div className="logic-editor-command-palette-rename-copy">
              <strong>Rename {renameTarget.tagName}</strong>
              <span>Updates the current logic file only.</span>
            </div>
            <div className="logic-editor-command-palette-footer-note">
              <CornerDownLeft size={13} />
              <span>Enter applies rename. Esc returns to results.</span>
            </div>
          </div>
        ) : results.length > 0 ? (
          <div className="logic-editor-command-palette-results" id={listboxId} role="listbox" aria-label="Command results">
            {results.map((result, index) => (
              <button
                key={result.id}
                id={result.id}
                className={`logic-editor-command-palette-result ${index === activeIndex ? "is-active" : ""}`.trim()}
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={result.execute}
              >
                <span className="logic-editor-command-palette-result-icon">{renderIcon(result.icon)}</span>
                <span className="logic-editor-command-palette-result-copy">
                  <strong>{result.title}</strong>
                  <span>{result.subtitle}</span>
                </span>
                <span className="logic-editor-command-palette-result-kind">{result.kindLabel}</span>
              </button>
            ))}
          </div>
        ) : (
          <div className="logic-editor-command-palette-empty">
            <strong>No matching commands</strong>
            <span>Try a tag name, `:line`, or `validate`.</span>
          </div>
        )}

        <div className="logic-editor-command-palette-footer-note">
          <CornerDownLeft size={13} />
          <span>Enter runs the selected command. Arrow keys move through results.</span>
        </div>
      </div>
    </div>
  );
}
