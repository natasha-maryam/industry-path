import { useEffect, useMemo, useRef, useState } from "react";
import * as monaco from "monaco-editor";
import { AlertTriangle, ChevronDown, ChevronRight, FileCode2, FileX, Folder, LoaderCircle } from "lucide-react";
import { parseStructuredTextIntelligence, type StructuredTextIdentifierInfo } from "../utils/controlLogicIntelligence";
import "../styles/code-explorer-panel.css";

const SUPPORTED_FOLDERS = ["equipment", "control_loops", "sequences", "interlocks", "alarms", "utilities"] as const;

type SupportedFolder = (typeof SUPPORTED_FOLDERS)[number];

export type GeneratedLogicFile = {
  path: string;
  content: string;
};

export type STDiagnosticMarker = {
  line: number;
  column: number;
  severity: "error" | "warning";
  code: string;
  message: string;
};

export type STJumpLocation = {
  file: string;
  line: number;
  column: number;
  nonce?: number;
};

export type CodeExplorerPanelProps = {
  files?: GeneratedLogicFile[];
  bundledCode?: string;
  selectedFilePath?: string | null;
  onSelectFile?: (path: string) => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  requiredPreviousStep?: string;
  warningMessage?: string | null;
  diagnosticsByFile?: Record<string, STDiagnosticMarker[]>;
  jumpToLocation?: STJumpLocation | null;
  className?: string;
};

type FolderTree = {
  rootFiles: GeneratedLogicFile[];
  folders: Record<SupportedFolder, GeneratedLogicFile[]>;
};

type IntelligenceOverlayState = {
  info: StructuredTextIdentifierInfo;
  top: number;
  left: number;
  activeUsageIndex: number;
};

const normalizePath = (path: string): string => path.replace(/^\/+/, "").replace(/\\/g, "/").trim();

const parseBundledFiles = (bundledCode: string): GeneratedLogicFile[] => {
  if (!bundledCode.trim()) {
    return [];
  }

  const markerPattern = /\(\*\s*=====\s*FILE:\s*(.+?)\s*=====\s*\*\)/g;
  const matches = [...bundledCode.matchAll(markerPattern)];

  if (matches.length === 0) {
    return [{ path: "main.st", content: bundledCode }];
  }

  const parsedFiles: GeneratedLogicFile[] = [];

  for (let index = 0; index < matches.length; index += 1) {
    const current = matches[index];
    const next = matches[index + 1];
    const start = (current.index ?? 0) + current[0].length;
    const end = next?.index ?? bundledCode.length;
    const rawPath = current[1]?.trim() || `file_${index + 1}.st`;
    const filePath = normalizePath(rawPath);
    const content = bundledCode.slice(start, end).trim();

    parsedFiles.push({ path: filePath, content });
  }

  return parsedFiles;
};

const buildFolderTree = (files: GeneratedLogicFile[]): FolderTree => {
  const folders = SUPPORTED_FOLDERS.reduce(
    (accumulator, folder) => ({
      ...accumulator,
      [folder]: [],
    }),
    {} as Record<SupportedFolder, GeneratedLogicFile[]>
  );

  const rootFiles: GeneratedLogicFile[] = [];

  for (const file of files) {
    const normalizedPath = normalizePath(file.path);
    const parts = normalizedPath.split("/").filter(Boolean);
    const top = parts[0];

    if (!top || parts.length === 1) {
      rootFiles.push({ ...file, path: parts[0] || "main.st" });
      continue;
    }

    if ((SUPPORTED_FOLDERS as readonly string[]).includes(top)) {
      const folder = top as SupportedFolder;
      const relativePath = parts.slice(1).join("/") || `${folder}.st`;
      folders[folder] = [...folders[folder], { ...file, path: `${folder}/${relativePath}` }];
      continue;
    }

    rootFiles.push({ ...file, path: normalizedPath });
  }

  rootFiles.sort((left, right) => left.path.localeCompare(right.path));
  for (const folder of SUPPORTED_FOLDERS) {
    folders[folder].sort((left, right) => left.path.localeCompare(right.path));
  }

  return { rootFiles, folders };
};

export default function CodeExplorerPanel({
  files,
  bundledCode = "",
  selectedFilePath = null,
  onSelectFile,
  loading = false,
  error = null,
  onRetry,
  requiredPreviousStep = "ST Generation",
  warningMessage = null,
  diagnosticsByFile = {},
  jumpToLocation = null,
  className = "",
}: CodeExplorerPanelProps) {
  const editorWrapRef = useRef<HTMLDivElement | null>(null);
  const editorMountRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const diffEditorRef = useRef<monaco.editor.IStandaloneDiffEditor | null>(null);
  const jumpTimerRef = useRef<number | null>(null);
  const highlightTimerRef = useRef<number | null>(null);
  const hoverTimerRef = useRef<number | null>(null);
  const modelByPathRef = useRef<Map<string, monaco.editor.ITextModel>>(new Map());
  const originalModelByPathRef = useRef<Map<string, monaco.editor.ITextModel>>(new Map());
  const highlightDecorationsRef = useRef<string[]>([]);
  const pinnedPopoverRef = useRef<HTMLDivElement | null>(null);

  const resolvedFiles = useMemo<GeneratedLogicFile[]>(() => {
    const sourceFiles = files && files.length > 0 ? files : parseBundledFiles(bundledCode);
    const deduped = new Map<string, GeneratedLogicFile>();

    for (const sourceFile of sourceFiles) {
      const normalized = normalizePath(sourceFile.path || "main.st");
      if (!deduped.has(normalized)) {
        deduped.set(normalized, { path: normalized, content: sourceFile.content || "" });
      }
    }

    return [...deduped.values()];
  }, [bundledCode, files]);

  const folderTree = useMemo(() => buildFolderTree(resolvedFiles), [resolvedFiles]);
  const hasFiles = resolvedFiles.length > 0;

  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    root: true,
    equipment: true,
    control_loops: true,
  });
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [isDiffMode, setIsDiffMode] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedFilePath) {
      return;
    }
    setSelectedPath(selectedFilePath);
  }, [selectedFilePath]);

  useEffect(() => {
    if (!hasFiles) {
      setSelectedPath("");
      return;
    }

    const mainFile = resolvedFiles.find((file) => file.path.toLowerCase() === "main.st");
    setSelectedPath((current) => {
      const nextPath = current || selectedFilePath || mainFile?.path || resolvedFiles[0].path;
      if (nextPath && onSelectFile) {
        onSelectFile(nextPath);
      }
      return nextPath;
    });
  }, [hasFiles, onSelectFile, resolvedFiles, selectedFilePath]);

  const selectedFile = useMemo(() => {
    if (!selectedPath) {
      return null;
    }
    return resolvedFiles.find((file) => file.path === selectedPath) ?? null;
  }, [resolvedFiles, selectedPath]);
  const identifierIntelligence = useMemo(
    () => parseStructuredTextIntelligence(selectedFile?.content || ""),
    [selectedFile?.content]
  );
  const [hoveredIdentifier, setHoveredIdentifier] = useState<IntelligenceOverlayState | null>(null);
  const [pinnedIdentifier, setPinnedIdentifier] = useState<IntelligenceOverlayState | null>(null);
  const usageDecorationsRef = useRef<string[]>([]);

  const normalizedDiagnosticsByFile = useMemo<Record<string, STDiagnosticMarker[]>>(() => {
    const output: Record<string, STDiagnosticMarker[]> = {};
    for (const [rawPath, markers] of Object.entries(diagnosticsByFile)) {
      const normalizedPath = normalizePath(rawPath);
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

  const getOrCreateModel = (filePath: string, content: string): monaco.editor.ITextModel => {
    const normalized = normalizePath(filePath);
    const existing = modelByPathRef.current.get(normalized);
    if (existing) {
      if (existing.isDisposed()) {
        modelByPathRef.current.delete(normalized);
      } else {
        if (existing.getValue() !== content) {
          existing.setValue(content);
        }
        return existing;
      }
    }

    const uri = monaco.Uri.parse(`inmemory://crosslayerx/${encodeURIComponent(normalized)}`);
    const cached = monaco.editor.getModel(uri);
    if (cached && !cached.isDisposed()) {
      if (cached.getValue() !== content) {
        cached.setValue(content);
      }
      modelByPathRef.current.set(normalized, cached);
      return cached;
    }

    const model = monaco.editor.createModel(content, "pascal", uri);
    modelByPathRef.current.set(normalized, model);
    return model;
  };

  const getOrCreateOriginalModel = (filePath: string, content: string): monaco.editor.ITextModel => {
    const normalized = normalizePath(filePath);
    const existing = originalModelByPathRef.current.get(normalized);
    if (existing) {
      if (existing.isDisposed()) {
        originalModelByPathRef.current.delete(normalized);
      } else {
        return existing;
      }
    }

    const uri = monaco.Uri.parse(`inmemory://crosslayerx-original/${encodeURIComponent(normalized)}`);
    const cached = monaco.editor.getModel(uri);
    if (cached && !cached.isDisposed()) {
      originalModelByPathRef.current.set(normalized, cached);
      return cached;
    }

    const model = monaco.editor.createModel(content, "pascal", uri);
    originalModelByPathRef.current.set(normalized, model);
    return model;
  };

  const disposeEditors = (): void => {
    editorRef.current?.dispose();
    editorRef.current = null;
    diffEditorRef.current?.dispose();
    diffEditorRef.current = null;
  };

  const getActiveEditorInstance = (): monaco.editor.IStandaloneCodeEditor | null => editorRef.current ?? diffEditorRef.current?.getModifiedEditor() ?? null;

  const getOverlayCoordinates = (
    editor: monaco.editor.IStandaloneCodeEditor,
    position: monaco.Position
  ): { top: number; left: number } | null => {
    if (!editorMountRef.current) {
      return null;
    }
    const visiblePosition = editor.getScrolledVisiblePosition(position);
    if (!visiblePosition) {
      return null;
    }
    const top = editorMountRef.current.offsetTop + visiblePosition.top + visiblePosition.height + 8;
    const left = editorMountRef.current.offsetLeft + visiblePosition.left + 8;
    return { top, left };
  };

  const resolveIdentifierAtPosition = (
    editor: monaco.editor.IStandaloneCodeEditor,
    position: monaco.Position
  ): { info: StructuredTextIdentifierInfo; top: number; left: number; activeUsageIndex: number } | null => {
    const model = editor.getModel();
    if (!model) {
      return null;
    }
    const word = model.getWordAtPosition(position);
    if (!word?.word) {
      return null;
    }
    const info = identifierIntelligence.byName[word.word];
    if (!info) {
      return null;
    }
    const coordinates = getOverlayCoordinates(editor, position);
    if (!coordinates) {
      return null;
    }
    const usageOccurrences = [...info.writeOccurrences, ...info.readOccurrences].sort((left, right) =>
      left.line === right.line ? left.column - right.column : left.line - right.line
    );
    const activeUsageIndex = Math.max(
      0,
      usageOccurrences.findIndex((occurrence) => occurrence.line === position.lineNumber && occurrence.column === position.column)
    );
    return { info, ...coordinates, activeUsageIndex: activeUsageIndex >= 0 ? activeUsageIndex : 0 };
  };

  const clearUsageHighlights = (): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      usageDecorationsRef.current = [];
      return;
    }
    usageDecorationsRef.current = activeEditor.deltaDecorations(usageDecorationsRef.current, []);
  };

  const highlightAllUsages = (info: StructuredTextIdentifierInfo): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }
    usageDecorationsRef.current = activeEditor.deltaDecorations(
      usageDecorationsRef.current,
      info.occurrences.map((occurrence) => ({
        range: new monaco.Range(occurrence.line, occurrence.column, occurrence.line, occurrence.column + info.name.length),
        options: {
          inlineClassName: occurrence.role === "write" ? "code-explorer-usage-highlight-write" : "code-explorer-usage-highlight-read",
        },
      }))
    );
  };

  const focusOccurrence = (info: StructuredTextIdentifierInfo, occurrence: StructuredTextIdentifierInfo["occurrences"][number]): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }
    activeEditor.revealPositionInCenter({ lineNumber: occurrence.line, column: occurrence.column });
    activeEditor.setPosition({ lineNumber: occurrence.line, column: occurrence.column });
    activeEditor.focus();
    activeEditor.setSelection({
      startLineNumber: occurrence.line,
      startColumn: occurrence.column,
      endLineNumber: occurrence.line,
      endColumn: occurrence.column + info.name.length,
    });
    if (highlightTimerRef.current) {
      window.clearTimeout(highlightTimerRef.current);
    }
    highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, [
      {
        range: new monaco.Range(occurrence.line, 1, occurrence.line, 1),
        options: { isWholeLine: true, className: "code-explorer-line-highlight" },
      },
    ]);
    highlightTimerRef.current = window.setTimeout(() => {
      highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, []);
      highlightTimerRef.current = null;
    }, 1800);
  };

  const usageOccurrencesForPinned = pinnedIdentifier
    ? [...pinnedIdentifier.info.writeOccurrences, ...pinnedIdentifier.info.readOccurrences].sort((left, right) =>
        left.line === right.line ? left.column - right.column : left.line - right.line
      )
    : [];

  useEffect(() => {
    setHoveredIdentifier(null);
    setPinnedIdentifier(null);
    clearUsageHighlights();
    if (hoverTimerRef.current) {
      window.clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  }, [selectedFile?.path]);

  useEffect(() => {
    if (!editorMountRef.current || loading || error || !hasFiles) {
      disposeEditors();
      return;
    }

    const activeFile = selectedFile ?? resolvedFiles[0];
    const activeModel = getOrCreateModel(activeFile.path, activeFile.content || "");
    const originalModel = getOrCreateOriginalModel(activeFile.path, activeFile.content || "");

    const filePathSet = new Set(resolvedFiles.map((file) => normalizePath(file.path)));
    for (const [filePath, model] of modelByPathRef.current.entries()) {
      if (!filePathSet.has(filePath)) {
        model.dispose();
        modelByPathRef.current.delete(filePath);
      }
    }
    for (const [filePath, model] of originalModelByPathRef.current.entries()) {
      if (!filePathSet.has(filePath)) {
        model.dispose();
        originalModelByPathRef.current.delete(filePath);
      }
    }

    if (isDiffMode) {
      editorRef.current?.dispose();
      editorRef.current = null;

      if (!diffEditorRef.current) {
        diffEditorRef.current = monaco.editor.createDiffEditor(editorMountRef.current, {
          readOnly: true,
          automaticLayout: true,
          minimap: { enabled: false },
          renderSideBySide: true,
          originalEditable: false,
          lineNumbers: "on",
          fontSize: 12,
          scrollBeyondLastLine: false,
          wordWrap: "off",
          autoIndent: "full",
          folding: true,
          bracketPairColorization: { enabled: true },
        });
      }

      diffEditorRef.current.setModel({ original: originalModel, modified: activeModel });
      return;
    }

    diffEditorRef.current?.dispose();
    diffEditorRef.current = null;

    if (!editorRef.current) {
      editorRef.current = monaco.editor.create(editorMountRef.current, {
        model: activeModel,
        readOnly: true,
        automaticLayout: true,
        minimap: { enabled: false },
        lineNumbers: "on",
        fontSize: 12,
        scrollBeyondLastLine: false,
        wordWrap: "off",
        autoIndent: "full",
        folding: true,
        bracketPairColorization: { enabled: true },
      });
      return;
    }

    editorRef.current.setModel(activeModel);
  }, [error, hasFiles, isDiffMode, loading, resolvedFiles, selectedFile]);

  useEffect(() => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }

    const handleOutsidePointer = (event: MouseEvent): void => {
      const target = event.target as Node | null;
      if (target && pinnedPopoverRef.current?.contains(target)) {
        return;
      }
      setPinnedIdentifier(null);
      clearUsageHighlights();
    };

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setPinnedIdentifier(null);
        clearUsageHighlights();
      }
    };

    const updatePinnedPosition = (): void => {
      setPinnedIdentifier((current) => {
        if (!current) {
          return current;
        }
        const anchor = current.info.occurrences[0];
        if (!anchor) {
          return current;
        }
        const coordinates = getOverlayCoordinates(activeEditor, new monaco.Position(anchor.line, anchor.column));
        if (!coordinates) {
          return current;
        }
        return { ...current, ...coordinates };
      });
    };

    const mouseMoveDisposable = activeEditor.onMouseMove((event) => {
      if (pinnedIdentifier) {
        return;
      }
      if (!event.target.position || event.target.type !== monaco.editor.MouseTargetType.CONTENT_TEXT) {
        if (hoverTimerRef.current) {
          window.clearTimeout(hoverTimerRef.current);
          hoverTimerRef.current = null;
        }
        setHoveredIdentifier(null);
        return;
      }

      if (hoverTimerRef.current) {
        window.clearTimeout(hoverTimerRef.current);
      }

      const position = event.target.position;
      hoverTimerRef.current = window.setTimeout(() => {
        const nextOverlay = resolveIdentifierAtPosition(activeEditor, position);
        setHoveredIdentifier(nextOverlay ? { info: nextOverlay.info, top: nextOverlay.top, left: nextOverlay.left, activeUsageIndex: nextOverlay.activeUsageIndex } : null);
        hoverTimerRef.current = null;
      }, 90);
    });

    const mouseLeaveDisposable = activeEditor.onMouseLeave(() => {
      if (hoverTimerRef.current) {
        window.clearTimeout(hoverTimerRef.current);
        hoverTimerRef.current = null;
      }
      setHoveredIdentifier(null);
    });

    const mouseDownDisposable = activeEditor.onMouseDown((event) => {
      if (!event.target.position || event.target.type !== monaco.editor.MouseTargetType.CONTENT_TEXT) {
        setPinnedIdentifier(null);
        return;
      }
      const nextOverlay = resolveIdentifierAtPosition(activeEditor, event.target.position);
      if (!nextOverlay) {
        setPinnedIdentifier(null);
        clearUsageHighlights();
        return;
      }
      setPinnedIdentifier({ info: nextOverlay.info, top: nextOverlay.top, left: nextOverlay.left, activeUsageIndex: nextOverlay.activeUsageIndex });
      setHoveredIdentifier(null);
    });

    const scrollDisposable = activeEditor.onDidScrollChange(() => {
      updatePinnedPosition();
    });

    document.addEventListener("mousedown", handleOutsidePointer, true);
    document.addEventListener("keydown", handleEscape);

    return () => {
      mouseMoveDisposable.dispose();
      mouseLeaveDisposable.dispose();
      mouseDownDisposable.dispose();
      scrollDisposable.dispose();
      document.removeEventListener("mousedown", handleOutsidePointer, true);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [identifierIntelligence.byName, pinnedIdentifier]);

  useEffect(() => {
    for (const file of resolvedFiles) {
      const model = getOrCreateModel(file.path, file.content || "");
      const markers = (normalizedDiagnosticsByFile[normalizePath(file.path)] ?? []).map((item) => ({
        startLineNumber: Math.max(1, item.line || 1),
        startColumn: Math.max(1, item.column || 1),
        endLineNumber: Math.max(1, item.line || 1),
        endColumn: Math.max(1, (item.column || 1) + 1),
        message: item.message,
        code: item.code,
        severity: item.severity === "error" ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning,
      }));
      monaco.editor.setModelMarkers(model, "st-verifier", markers);
    }
  }, [normalizedDiagnosticsByFile, resolvedFiles]);

  useEffect(() => {
    if (!jumpToLocation) {
      return;
    }
    const normalizedPath = normalizePath(jumpToLocation.file);
    const directMatch = resolvedFiles.find((file) => normalizePath(file.path) === normalizedPath);
    const fallbackMatch = normalizedPath.startsWith("control_logic/")
      ? resolvedFiles.find((file) => normalizePath(file.path) === normalizedPath.replace(/^control_logic\//, ""))
      : null;
    const targetFile = directMatch ?? fallbackMatch;
    if (!targetFile) {
      return;
    }

    setSelectedPath(targetFile.path);
    onSelectFile?.(targetFile.path);

    const lineNumber = Math.max(1, jumpToLocation.line || 1);
    const column = Math.max(1, jumpToLocation.column || 1);

    if (jumpTimerRef.current) {
      window.clearTimeout(jumpTimerRef.current);
    }

    jumpTimerRef.current = window.setTimeout(() => {
      const activeEditor = editorRef.current ?? diffEditorRef.current?.getModifiedEditor();
      if (!activeEditor) {
        return;
      }
      activeEditor.revealPositionInCenter({ lineNumber, column });
      activeEditor.setPosition({ lineNumber, column });
      activeEditor.focus();
      activeEditor.setSelection({
        startLineNumber: lineNumber,
        startColumn: column,
        endLineNumber: lineNumber,
        endColumn: column + 1,
      });

      if (highlightTimerRef.current) {
        window.clearTimeout(highlightTimerRef.current);
        highlightTimerRef.current = null;
      }

      highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, [
        {
          range: new monaco.Range(lineNumber, 1, lineNumber, 1),
          options: {
            isWholeLine: true,
            className: "code-explorer-line-highlight",
          },
        },
      ]);

      highlightTimerRef.current = window.setTimeout(() => {
        highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, []);
        highlightTimerRef.current = null;
      }, 1800);
    }, 0);

    return () => {
      if (jumpTimerRef.current) {
        window.clearTimeout(jumpTimerRef.current);
        jumpTimerRef.current = null;
      }
      if (hoverTimerRef.current) {
        window.clearTimeout(hoverTimerRef.current);
        hoverTimerRef.current = null;
      }
      clearUsageHighlights();
      if (highlightTimerRef.current) {
        window.clearTimeout(highlightTimerRef.current);
        highlightTimerRef.current = null;
      }
      const activeEditor = editorRef.current ?? diffEditorRef.current?.getModifiedEditor();
      if (activeEditor) {
        highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, []);
      }
    };
  }, [jumpToLocation, onSelectFile, resolvedFiles]);

  useEffect(() => {
    return () => {
      if (jumpTimerRef.current) {
        window.clearTimeout(jumpTimerRef.current);
        jumpTimerRef.current = null;
      }
      if (highlightTimerRef.current) {
        window.clearTimeout(highlightTimerRef.current);
        highlightTimerRef.current = null;
      }
      disposeEditors();
      for (const model of modelByPathRef.current.values()) {
        model.dispose();
      }
      modelByPathRef.current.clear();
      for (const model of originalModelByPathRef.current.values()) {
        model.dispose();
      }
      originalModelByPathRef.current.clear();
    };
  }, []);

  const renderFileRow = (file: GeneratedLogicFile, displayPath: string) => {
    const active = selectedPath === file.path;

    return (
      <button
        key={file.path}
        className={`code-explorer-file-row ${active ? "active" : ""}`}
        onClick={() => {
          setSelectedPath(file.path);
          onSelectFile?.(file.path);
        }}
        type="button"
      >
        <FileCode2 size={12} />
        <span>{displayPath}</span>
      </button>
    );
  };

  if (loading) {
    return (
      <section className={`code-explorer-panel ${className}`.trim()}>
        <div className="code-explorer-state">
          <LoaderCircle size={16} className="code-explorer-spin" />
          <span>Loading generated logic files...</span>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className={`code-explorer-panel ${className}`.trim()}>
        <div className="code-explorer-state error">
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button className="code-explorer-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
            Retry
          </button>
        </div>
      </section>
    );
  }

  if (!hasFiles) {
    return (
      <section className={`code-explorer-panel ${className}`.trim()}>
        <div className="code-explorer-state">
          <FileX size={16} />
          <span>No generated ST files available. Complete {requiredPreviousStep} first.</span>
        </div>
      </section>
    );
  }

  return (
    <section className={`code-explorer-panel ${className}`.trim()}>
      <header className="code-explorer-header">
        <h3>Generated ST</h3>
        <div className="code-explorer-header-actions">
          <span>{resolvedFiles.length} files</span>
          <button className="code-explorer-mode-btn" type="button" onClick={() => setIsDiffMode((current) => !current)}>
            {isDiffMode ? "Standard" : "Diff"}
          </button>
        </div>
      </header>

      {warningMessage ? <div className="code-explorer-warning">{warningMessage}</div> : null}

      <div className="code-explorer-body">
        <aside className="code-explorer-tree" aria-label="Generated file tree">
          <button
            className="code-explorer-folder-row"
            onClick={() => setExpandedFolders((previous) => ({ ...previous, root: !previous.root }))}
            type="button"
          >
            {expandedFolders.root ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            <Folder size={12} />
            <span>root</span>
          </button>

          {expandedFolders.root ? (
            <div className="code-explorer-group">
              {folderTree.rootFiles.map((file) => renderFileRow(file, file.path))}

              {SUPPORTED_FOLDERS.map((folder) => {
                const filesInFolder = folderTree.folders[folder];
                const expanded = expandedFolders[folder] ?? false;

                return (
                  <div key={folder}>
                    <button
                      className="code-explorer-folder-row nested"
                      onClick={() =>
                        setExpandedFolders((previous) => ({
                          ...previous,
                          [folder]: !previous[folder],
                        }))
                      }
                      type="button"
                    >
                      {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      <Folder size={12} />
                      <span>{folder}</span>
                      <span className="code-explorer-count">{filesInFolder.length}</span>
                    </button>

                    {expanded ? (
                      <div className="code-explorer-group nested">
                        {filesInFolder.length > 0 ? (
                          filesInFolder.map((file) => renderFileRow(file, file.path.replace(`${folder}/`, "")))
                        ) : (
                          <div className="code-explorer-empty-folder">Empty</div>
                        )}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : null}
        </aside>

        <div className="code-explorer-editor-wrap" ref={editorWrapRef}>
          <div className="code-explorer-file-header">{selectedFile?.path || "No file selected"}</div>
          <div ref={editorMountRef} className="code-explorer-editor" />
          {hoveredIdentifier && !pinnedIdentifier ? (
            <div className="code-explorer-intel-tooltip" style={{ top: hoveredIdentifier.top, left: hoveredIdentifier.left }}>
              <strong>{hoveredIdentifier.info.name}</strong>
              <span>
                {hoveredIdentifier.info.declaredType || "Undeclared"} · {hoveredIdentifier.info.usageCount} use{hoveredIdentifier.info.usageCount === 1 ? "" : "s"}
              </span>
            </div>
          ) : null}
          {pinnedIdentifier ? (
            <div
              ref={pinnedPopoverRef}
              className="code-explorer-intel-popover"
              style={{ top: pinnedIdentifier.top, left: pinnedIdentifier.left }}
            >
              <div className="code-explorer-intel-popover-header">
                <strong>{pinnedIdentifier.info.name}</strong>
                <span>{pinnedIdentifier.info.category}</span>
              </div>
              <div className="code-explorer-intel-popover-grid">
                <div>
                  <span>Type</span>
                  <strong>{pinnedIdentifier.info.declaredType || "Undeclared"}</strong>
                </div>
                <div>
                  <span>Occurrences</span>
                  <strong>{pinnedIdentifier.info.occurrenceCount}</strong>
                </div>
                <div>
                  <span>Reads</span>
                  <strong>{pinnedIdentifier.info.readCount}</strong>
                </div>
                <div>
                  <span>Writes</span>
                  <strong>{pinnedIdentifier.info.writeCount}</strong>
                </div>
              </div>
              <div className="code-explorer-intel-popover-section">
                <span>Definition</span>
                <strong>
                  {pinnedIdentifier.info.declarationLine
                    ? `Line ${pinnedIdentifier.info.declarationLine}`
                    : pinnedIdentifier.info.firstSeenLine
                      ? `First seen on line ${pinnedIdentifier.info.firstSeenLine}`
                      : "No local declaration"}
                </strong>
                <code>{pinnedIdentifier.info.declarationSnippet || "Identifier is used in this file without a declaration."}</code>
              </div>
              <div className="code-explorer-intel-popover-section">
                <span>Usage</span>
                <div className="code-explorer-intel-usage-summary">
                  <strong>{pinnedIdentifier.info.usageCount} total usage{pinnedIdentifier.info.usageCount === 1 ? "" : "s"}</strong>
                  <span>All lines: {pinnedIdentifier.info.lineReferences.join(", ") || "None"}</span>
                </div>
                <div className="code-explorer-intel-reference-list split">
                  <div className="code-explorer-intel-usage-group">
                    <span>Assigned / Written</span>
                    {pinnedIdentifier.info.writeOccurrences.length > 0 ? (
                      pinnedIdentifier.info.writeOccurrences.map((occurrence) => (
                        <button
                          key={`write-${occurrence.line}-${occurrence.column}`}
                          className="code-explorer-intel-reference-item"
                          type="button"
                          onClick={() => {
                            focusOccurrence(pinnedIdentifier.info, occurrence);
                            setPinnedIdentifier((current) =>
                              current
                                ? {
                                    ...current,
                                    activeUsageIndex: usageOccurrencesForPinned.findIndex(
                                      (item) => item.line === occurrence.line && item.column === occurrence.column
                                    ),
                                  }
                                : current
                            );
                          }}
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
                    {pinnedIdentifier.info.readOccurrences.length > 0 ? (
                      pinnedIdentifier.info.readOccurrences.map((occurrence) => (
                        <button
                          key={`read-${occurrence.line}-${occurrence.column}`}
                          className="code-explorer-intel-reference-item"
                          type="button"
                          onClick={() => {
                            focusOccurrence(pinnedIdentifier.info, occurrence);
                            setPinnedIdentifier((current) =>
                              current
                                ? {
                                    ...current,
                                    activeUsageIndex: usageOccurrencesForPinned.findIndex(
                                      (item) => item.line === occurrence.line && item.column === occurrence.column
                                    ),
                                  }
                                : current
                            );
                          }}
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
                  <button
                    className="code-explorer-intel-action-btn"
                    type="button"
                    onClick={() => {
                      const definitionOccurrence = pinnedIdentifier.info.occurrences.find((item) => item.role === "declaration") ?? pinnedIdentifier.info.occurrences[0];
                      if (definitionOccurrence) {
                        focusOccurrence(pinnedIdentifier.info, definitionOccurrence);
                      }
                    }}
                  >
                    Jump to Definition
                  </button>
                  <button
                    className="code-explorer-intel-action-btn"
                    type="button"
                    onClick={() => {
                      highlightAllUsages(pinnedIdentifier.info);
                    }}
                  >
                    Highlight All Usages
                  </button>
                  <button
                    className="code-explorer-intel-action-btn"
                    type="button"
                    disabled={usageOccurrencesForPinned.length === 0}
                    onClick={() => {
                      if (usageOccurrencesForPinned.length === 0) {
                        return;
                      }
                      setPinnedIdentifier((current) => {
                        if (!current) {
                          return current;
                        }
                        const nextIndex = (current.activeUsageIndex - 1 + usageOccurrencesForPinned.length) % usageOccurrencesForPinned.length;
                        focusOccurrence(current.info, usageOccurrencesForPinned[nextIndex]);
                        return { ...current, activeUsageIndex: nextIndex };
                      });
                    }}
                  >
                    Previous Usage
                  </button>
                  <button
                    className="code-explorer-intel-action-btn"
                    type="button"
                    disabled={usageOccurrencesForPinned.length === 0}
                    onClick={() => {
                      if (usageOccurrencesForPinned.length === 0) {
                        return;
                      }
                      setPinnedIdentifier((current) => {
                        if (!current) {
                          return current;
                        }
                        const nextIndex = (current.activeUsageIndex + 1) % usageOccurrencesForPinned.length;
                        focusOccurrence(current.info, usageOccurrencesForPinned[nextIndex]);
                        return { ...current, activeUsageIndex: nextIndex };
                      });
                    }}
                  >
                    Next Usage
                  </button>
                </div>
              </div>
              {pinnedIdentifier.info.casingVariants.length > 1 ? (
                <div className="code-explorer-intel-popover-section">
                  <span>Casing variants</span>
                  <strong>{pinnedIdentifier.info.casingVariants.join(", ")}</strong>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
