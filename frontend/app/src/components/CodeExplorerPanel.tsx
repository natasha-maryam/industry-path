import { useEffect, useMemo, useRef, useState } from "react";
import * as monaco from "monaco-editor";
import { AlertTriangle, ChevronDown, ChevronRight, FileCode2, FileX, Folder, LoaderCircle } from "lucide-react";
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
  const editorMountRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const modelByPathRef = useRef<Map<string, monaco.editor.ITextModel>>(new Map());

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
      if (existing.getValue() !== content) {
        existing.setValue(content);
      }
      return existing;
    }

    const uri = monaco.Uri.parse(`inmemory://crosslayerx/${encodeURIComponent(normalized)}`);
    const model = monaco.editor.createModel(content, "plaintext", uri);
    modelByPathRef.current.set(normalized, model);
    return model;
  };

  useEffect(() => {
    if (!editorMountRef.current || loading || error || !hasFiles) {
      return;
    }

    const activeFile = selectedFile ?? resolvedFiles[0];
    const activeModel = getOrCreateModel(activeFile.path, activeFile.content || "");

    const filePathSet = new Set(resolvedFiles.map((file) => normalizePath(file.path)));
    for (const [filePath, model] of modelByPathRef.current.entries()) {
      if (!filePathSet.has(filePath)) {
        model.dispose();
        modelByPathRef.current.delete(filePath);
      }
    }

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
      });
      return;
    }

    editorRef.current.setModel(activeModel);
  }, [error, hasFiles, loading, resolvedFiles, selectedFile]);

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

    window.setTimeout(() => {
      if (!editorRef.current) {
        return;
      }
      editorRef.current.revealPositionInCenter({ lineNumber, column });
      editorRef.current.setPosition({ lineNumber, column });
      editorRef.current.focus();
      editorRef.current.setSelection({
        startLineNumber: lineNumber,
        startColumn: column,
        endLineNumber: lineNumber,
        endColumn: column + 1,
      });
    }, 0);
  }, [jumpToLocation, onSelectFile, resolvedFiles]);

  useEffect(() => {
    return () => {
      editorRef.current?.dispose();
      for (const model of modelByPathRef.current.values()) {
        model.dispose();
      }
      modelByPathRef.current.clear();
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
        <span>{resolvedFiles.length} files</span>
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

        <div className="code-explorer-editor-wrap">
          <div className="code-explorer-file-header">{selectedFile?.path || "No file selected"}</div>
          <div ref={editorMountRef} className="code-explorer-editor" />
        </div>
      </div>
    </section>
  );
}
