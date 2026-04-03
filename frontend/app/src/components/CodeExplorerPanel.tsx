import { useEffect, useMemo, useRef, useState } from "react";
import * as monaco from "monaco-editor";
import { AlertTriangle, ChevronDown, ChevronRight, FileCode2, FileX, Folder, LoaderCircle } from "lucide-react";
import { toast } from "react-hot-toast";
import type { InlineTagIntelligenceEntry, InlineTagIntelligenceLineReference, InlineTagIntelligenceReference } from "../utils/controlLogicIntelligence";
import { computeInlineChangeSet } from "../utils/logicInlineChanges";
import { ST_TYPE_OPTIONS } from "../utils/controlLogicTransforms";
import { getLogicTagIntelligenceSource } from "../utils/logicTagIntelligenceSource";
import TagIntelligenceDetailView from "./TagIntelligenceDetailView";
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

export type TagIntelligenceEditorCommand = {
  file: string;
  tagName: string;
  action: "focus-reference" | "jump-to-definition" | "highlight-all-usages" | "next-usage" | "previous-usage";
  line?: number;
  column?: number;
  nonce: number;
};

export type CodeExplorerPanelProps = {
  files?: GeneratedLogicFile[];
  changeBaselineFiles?: GeneratedLogicFile[];
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
  tagIntelligenceCommand?: TagIntelligenceEditorCommand | null;
  onRenameTagAction?: (params: { filePath: string; from: string; to: string; mode: "rename" | "remap" }) => boolean;
  onChangeTagTypeAction?: (params: { filePath: string; tagName: string; nextType: string }) => boolean;
  showChangeHighlights?: boolean;
  className?: string;
};

type FolderTree = {
  rootFiles: GeneratedLogicFile[];
  folders: Record<SupportedFolder, GeneratedLogicFile[]>;
};

type IntelligenceOverlayState = {
  matchedTagName: string;
  info: InlineTagIntelligenceEntry;
  anchor: InlineTagIntelligenceReference;
  top: number;
  left: number;
  activeUsageIndex: number;
};

type InlineSearchMatch = {
  lineNumber: number;
  startColumn: number;
  endColumn: number;
  preview: string;
};

type QuickActionMode = "menu" | "rename" | "remap" | "type";

type QuickActionState = {
  matchedTagName: string;
  info: InlineTagIntelligenceEntry;
  top: number;
  left: number;
  activeIndex: number;
  mode: QuickActionMode;
  inputValue: string;
  nextType: string;
};

const normalizePath = (path: string): string => path.replace(/^\/+/, "").replace(/\\/g, "/").trim();

const IDENTIFIER_TEXT_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;

function findInlineSearchMatches(content: string, query: string): InlineSearchMatch[] {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    return [];
  }

  const normalizedQuery = trimmedQuery.toLowerCase();
  const matches: InlineSearchMatch[] = [];
  const lines = content.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const sourceLine = lines[index] || "";
    const lowerLine = sourceLine.toLowerCase();
    let searchIndex = 0;

    while (searchIndex <= lowerLine.length - normalizedQuery.length) {
      const nextIndex = lowerLine.indexOf(normalizedQuery, searchIndex);
      if (nextIndex === -1) {
        break;
      }
      matches.push({
        lineNumber: index + 1,
        startColumn: nextIndex + 1,
        endColumn: nextIndex + trimmedQuery.length + 1,
        preview: sourceLine.trim() || sourceLine,
      });
      searchIndex = nextIndex + Math.max(1, trimmedQuery.length);
    }
  }

  return matches;
}

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
  changeBaselineFiles = [],
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
  tagIntelligenceCommand = null,
  onRenameTagAction,
  onChangeTagTypeAction,
  showChangeHighlights = true,
  className = "",
}: CodeExplorerPanelProps) {
  const editorWrapRef = useRef<HTMLDivElement | null>(null);
  const editorMountRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const jumpTimerRef = useRef<number | null>(null);
  const highlightTimerRef = useRef<number | null>(null);
  const hoverTimerRef = useRef<number | null>(null);
  const modelByPathRef = useRef<Map<string, monaco.editor.ITextModel>>(new Map());
  const highlightDecorationsRef = useRef<string[]>([]);
  const changeDecorationsRef = useRef<string[]>([]);
  const searchDecorationsRef = useRef<string[]>([]);
  const removedZoneIdsRef = useRef<string[]>([]);
  const pinnedPopoverRef = useRef<HTMLDivElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const quickActionButtonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const quickActionInputRef = useRef<HTMLInputElement | null>(null);
  const quickActionSelectRef = useRef<HTMLSelectElement | null>(null);

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
  const baselineFile = useMemo(() => {
    if (!selectedFile) {
      return null;
    }
    const normalizedSelectedPath = normalizePath(selectedFile.path);
    return changeBaselineFiles.find((file) => normalizePath(file.path) === normalizedSelectedPath) ?? null;
  }, [changeBaselineFiles, selectedFile]);
  const tagIntelligenceSource = useMemo(
    () => getLogicTagIntelligenceSource(selectedFile?.content || ""),
    [selectedFile?.content]
  );
  const inlineChangeSet = useMemo(() => {
    if (!showChangeHighlights || !selectedFile || !baselineFile) {
      return null;
    }
    return computeInlineChangeSet(baselineFile.content || "", selectedFile.content || "");
  }, [baselineFile, selectedFile, showChangeHighlights]);
  const [hoveredIdentifier, setHoveredIdentifier] = useState<IntelligenceOverlayState | null>(null);
  const [pinnedIdentifier, setPinnedIdentifier] = useState<IntelligenceOverlayState | null>(null);
  const [inlineSearchOpen, setInlineSearchOpen] = useState<boolean>(false);
  const [inlineSearchQuery, setInlineSearchQuery] = useState<string>("");
  const [searchActiveIndex, setSearchActiveIndex] = useState<number>(0);
  const [quickActionState, setQuickActionState] = useState<QuickActionState | null>(null);
  const usageDecorationsRef = useRef<string[]>([]);
  const inlineSearchMatches = useMemo(() => findInlineSearchMatches(selectedFile?.content || "", inlineSearchQuery), [inlineSearchQuery, selectedFile?.content]);

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

  const disposeEditors = (): void => {
    editorRef.current?.dispose();
    editorRef.current = null;
  };

  const getActiveEditorInstance = (): monaco.editor.IStandaloneCodeEditor | null => editorRef.current;

  const clearChangeHighlights = (): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      changeDecorationsRef.current = [];
      removedZoneIdsRef.current = [];
      return;
    }
    changeDecorationsRef.current = activeEditor.deltaDecorations(changeDecorationsRef.current, []);
    activeEditor.changeViewZones((accessor) => {
      for (const zoneId of removedZoneIdsRef.current) {
        accessor.removeZone(zoneId);
      }
    });
    removedZoneIdsRef.current = [];
  };

  const createRemovedBlockNode = (editor: monaco.editor.IStandaloneCodeEditor, lines: string[]): HTMLDivElement => {
    const block = document.createElement("div");
    block.className = "code-explorer-removed-zone";
    editor.applyFontInfo(block);

    for (const line of lines) {
      const row = document.createElement("div");
      row.className = "code-explorer-removed-zone-line";
      row.textContent = `- ${line || " "}`;
      block.appendChild(row);
    }

    return block;
  };

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

  const buildOverlayState = (
    editor: monaco.editor.IStandaloneCodeEditor,
    matchedTagName: string,
    info: InlineTagIntelligenceEntry,
    anchor: InlineTagIntelligenceReference,
    activeUsageIndex: number
  ): IntelligenceOverlayState | null => {
    const coordinates = getOverlayCoordinates(editor, new monaco.Position(anchor.line, anchor.column));
    if (!coordinates) {
      return null;
    }
    return {
      matchedTagName,
      info,
      anchor,
      ...coordinates,
      activeUsageIndex,
    };
  };

  const resolveIdentifierAtPosition = (
    editor: monaco.editor.IStandaloneCodeEditor,
    position: monaco.Position
  ): IntelligenceOverlayState | null => {
    const model = editor.getModel();
    if (!model) {
      return null;
    }
    const word = model.getWordAtPosition(position);
    if (!word?.word) {
      return null;
    }
    const info = tagIntelligenceSource.getTagByIdentifier(word.word);
    if (!info) {
      return null;
    }
    const usageOccurrences = tagIntelligenceSource.getAllUsages(word.word);
    const anchor = tagIntelligenceSource.getReferenceAtPosition(word.word, position.lineNumber, position.column, word.word);
    if (!anchor) {
      return null;
    }
    const activeUsageIndex = Math.max(
      0,
      usageOccurrences.findIndex(
        (occurrence) =>
          occurrence.line === position.lineNumber &&
          position.column >= occurrence.column &&
          position.column <= occurrence.column + Math.max(1, word.word.length - 1)
      )
    );
    return buildOverlayState(editor, word.word, info, anchor, activeUsageIndex >= 0 ? activeUsageIndex : 0);
  };

  const clearUsageHighlights = (): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      usageDecorationsRef.current = [];
      return;
    }
    usageDecorationsRef.current = activeEditor.deltaDecorations(usageDecorationsRef.current, []);
  };

  const clearSearchHighlights = (): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      searchDecorationsRef.current = [];
      return;
    }
    searchDecorationsRef.current = activeEditor.deltaDecorations(searchDecorationsRef.current, []);
  };

  const highlightAllUsages = (info: InlineTagIntelligenceEntry): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }
    usageDecorationsRef.current = activeEditor.deltaDecorations(
      usageDecorationsRef.current,
      info.usageContexts.all.map((occurrence) => ({
        range: new monaco.Range(occurrence.line, occurrence.column, occurrence.line, occurrence.column + info.tagName.length),
        options: {
          inlineClassName: occurrence.role === "write" ? "code-explorer-usage-highlight-write" : "code-explorer-usage-highlight-read",
        },
      }))
    );
  };

  const focusSearchMatch = (match: InlineSearchMatch): void => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }
    activeEditor.revealPositionInCenter({ lineNumber: match.lineNumber, column: match.startColumn });
    activeEditor.setPosition({ lineNumber: match.lineNumber, column: match.startColumn });
    activeEditor.focus();
    activeEditor.setSelection({
      startLineNumber: match.lineNumber,
      startColumn: match.startColumn,
      endLineNumber: match.lineNumber,
      endColumn: match.endColumn,
    });
  };

  const resolveTagAtSelection = (): QuickActionState | null => {
    const activeEditor = getActiveEditorInstance();
    const model = activeEditor?.getModel();
    if (!activeEditor || !model) {
      return null;
    }

    const selection = activeEditor.getSelection();
    const position = selection?.getPosition() ?? activeEditor.getPosition();
    if (!position) {
      return null;
    }

    const selectedText = selection && !selection.isEmpty() ? model.getValueInRange(selection).trim() : "";
    const identifier = IDENTIFIER_TEXT_PATTERN.test(selectedText)
      ? selectedText
      : model.getWordAtPosition(position)?.word ?? "";
    if (!identifier) {
      return null;
    }

    const info = tagIntelligenceSource.getTagByIdentifier(identifier);
    if (!info) {
      return null;
    }

    const reference = tagIntelligenceSource.getReferenceAtPosition(info.tagName, position.lineNumber, position.column, identifier)
      ?? info.declarationLocation.reference
      ?? info.usageContexts.all[0]
      ?? null;
    if (!reference) {
      return null;
    }

    const overlay = buildOverlayState(activeEditor, identifier, info, reference, 0);
    if (!overlay) {
      return null;
    }

    return {
      matchedTagName: identifier,
      info,
      top: overlay.top,
      left: overlay.left,
      activeIndex: 0,
      mode: "menu",
      inputValue: info.tagName,
      nextType: info.dataType || ST_TYPE_OPTIONS[0] || "BOOL",
    };
  };

  const openQuickActionMenu = (): void => {
    const quickAction = resolveTagAtSelection();
    if (!quickAction) {
      toast("Place the cursor on a tag to open quick actions.", { className: "industrial-toast" });
      return;
    }
    setPinnedIdentifier(null);
    setHoveredIdentifier(null);
    setInlineSearchOpen(false);
    clearUsageHighlights();
    setQuickActionState(quickAction);
  };

  const runQuickHighlightAction = (): void => {
    if (!quickActionState) {
      return;
    }
    highlightAllUsages(quickActionState.info);
    const reference = quickActionState.info.declarationLocation.reference ?? quickActionState.info.usageContexts.all[0] ?? null;
    if (reference) {
      updatePinnedFromReference(quickActionState.info, quickActionState.matchedTagName, reference);
    }
    setQuickActionState(null);
  };

  const applyQuickRenameOrRemap = (mode: "rename" | "remap"): void => {
    if (!quickActionState || !selectedFile || !onRenameTagAction) {
      return;
    }
    const didApply = onRenameTagAction({
      filePath: selectedFile.path,
      from: quickActionState.info.tagName,
      to: quickActionState.inputValue.trim(),
      mode,
    });
    if (didApply) {
      setQuickActionState(null);
    }
  };

  const applyQuickTypeChange = (): void => {
    if (!quickActionState || !selectedFile || !onChangeTagTypeAction) {
      return;
    }
    const didApply = onChangeTagTypeAction({
      filePath: selectedFile.path,
      tagName: quickActionState.info.tagName,
      nextType: quickActionState.nextType,
    });
    if (didApply) {
      setQuickActionState(null);
    }
  };

  const focusOccurrence = (info: InlineTagIntelligenceEntry, occurrence: InlineTagIntelligenceReference): void => {
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
      endColumn: occurrence.column + info.tagName.length,
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

  const focusLineReference = (info: InlineTagIntelligenceEntry, lineReference: InlineTagIntelligenceLineReference): InlineTagIntelligenceReference | null => {
    const definitionReference = tagIntelligenceSource.getDeclaration(info.tagName);
    const lineMatches = [
      ...(definitionReference && definitionReference.line === lineReference.line ? [definitionReference] : []),
      ...tagIntelligenceSource.getAllUsages(info.tagName).filter((occurrence) => occurrence.line === lineReference.line),
    ];
    const target = lineMatches[0] ?? null;
    if (target) {
      focusOccurrence(info, target);
    }
    return target;
  };

  const usageOccurrencesForPinned = pinnedIdentifier
    ? tagIntelligenceSource.getAllUsages(pinnedIdentifier.info.tagName)
    : [];

  const updatePinnedFromReference = (info: InlineTagIntelligenceEntry, matchedTagName: string, reference: InlineTagIntelligenceReference): void => {
    const nextUsageIndex = Math.max(
      0,
      tagIntelligenceSource.getAllUsages(info.tagName).findIndex((item) => item.line === reference.line && item.column === reference.column)
    );
    setPinnedIdentifier((current) => {
      const activeEditor = getActiveEditorInstance();
      if (!activeEditor) {
        return current;
      }
      return buildOverlayState(activeEditor, matchedTagName, info, reference, nextUsageIndex) ?? current;
    });
  };

  useEffect(() => {
    setHoveredIdentifier(null);
    setPinnedIdentifier(null);
    setQuickActionState(null);
    setInlineSearchOpen(false);
    setInlineSearchQuery("");
    setSearchActiveIndex(0);
    clearUsageHighlights();
    clearChangeHighlights();
    clearSearchHighlights();
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
        autoIndent: "full",
        folding: true,
        bracketPairColorization: { enabled: true },
      });
      return;
    }

    editorRef.current.setModel(activeModel);
  }, [error, hasFiles, loading, resolvedFiles, selectedFile]);

  useEffect(() => {
    const activeEditor = getActiveEditorInstance();
    const model = activeEditor?.getModel();
    if (!activeEditor || !model) {
      return;
    }

    if (!inlineChangeSet || (inlineChangeSet.changedLineNumbers.length === 0 && inlineChangeSet.removedBlocks.length === 0)) {
      clearChangeHighlights();
      return;
    }

    changeDecorationsRef.current = activeEditor.deltaDecorations(
      changeDecorationsRef.current,
      inlineChangeSet.changedLineNumbers
        .filter((lineNumber) => lineNumber >= 1 && lineNumber <= model.getLineCount())
        .map((lineNumber) => ({
          range: new monaco.Range(lineNumber, 1, lineNumber, 1),
          options: {
            isWholeLine: true,
            className: "code-explorer-change-line",
            linesDecorationsClassName: "code-explorer-change-glyph",
          },
        }))
    );

    activeEditor.changeViewZones((accessor) => {
      for (const zoneId of removedZoneIdsRef.current) {
        accessor.removeZone(zoneId);
      }

      removedZoneIdsRef.current = inlineChangeSet.removedBlocks.map((block) => {
        const safeAnchor = Math.max(0, Math.min(block.anchorLineNumber, model.getLineCount()));
        return accessor.addZone({
          afterLineNumber: safeAnchor,
          heightInLines: Math.max(1, block.lines.length),
          domNode: createRemovedBlockNode(activeEditor, block.lines),
        });
      });
    });

    return () => {
      clearChangeHighlights();
    };
  }, [inlineChangeSet, selectedFile?.path]);

  useEffect(() => {
    const activeEditor = getActiveEditorInstance();
    if (!activeEditor) {
      return;
    }

    if (!inlineSearchOpen || inlineSearchMatches.length === 0) {
      clearSearchHighlights();
      return;
    }

    searchDecorationsRef.current = activeEditor.deltaDecorations(
      searchDecorationsRef.current,
      inlineSearchMatches.map((match, index) => ({
        range: new monaco.Range(match.lineNumber, match.startColumn, match.lineNumber, match.endColumn),
        options: {
          inlineClassName: index === searchActiveIndex ? "code-explorer-search-match-active" : "code-explorer-search-match",
        },
      }))
    );
  }, [inlineSearchMatches, inlineSearchOpen, searchActiveIndex]);

  useEffect(() => {
    if (!inlineSearchOpen || inlineSearchMatches.length === 0) {
      return;
    }
    const clampedIndex = Math.min(searchActiveIndex, inlineSearchMatches.length - 1);
    if (clampedIndex !== searchActiveIndex) {
      setSearchActiveIndex(clampedIndex);
      return;
    }
    focusSearchMatch(inlineSearchMatches[clampedIndex]);
  }, [inlineSearchMatches, inlineSearchOpen, searchActiveIndex]);

  useEffect(() => {
    if (!quickActionState || quickActionState.mode !== "menu") {
      return;
    }
    window.requestAnimationFrame(() => {
      quickActionButtonRefs.current[quickActionState.activeIndex]?.focus();
    });
  }, [quickActionState]);

  useEffect(() => {
    if (!quickActionState || quickActionState.mode === "menu") {
      return;
    }
    window.requestAnimationFrame(() => {
      if (quickActionState.mode === "type") {
        quickActionSelectRef.current?.focus();
        return;
      }
      quickActionInputRef.current?.focus();
      quickActionInputRef.current?.select();
    });
  }, [quickActionState]);

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
      if (target && editorWrapRef.current?.contains(target) && (target as HTMLElement).closest(".code-explorer-quick-actions")) {
        return;
      }
      setQuickActionState(null);
      setPinnedIdentifier(null);
      clearUsageHighlights();
    };

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setInlineSearchOpen(false);
        setQuickActionState(null);
        setPinnedIdentifier(null);
        clearUsageHighlights();
        clearSearchHighlights();
      }
    };

    const updatePinnedPosition = (): void => {
      setPinnedIdentifier((current) => {
        if (!current) {
          return current;
        }
        const coordinates = getOverlayCoordinates(activeEditor, new monaco.Position(current.anchor.line, current.anchor.column));
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
        setHoveredIdentifier(nextOverlay);
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
      setPinnedIdentifier(nextOverlay);
      setHoveredIdentifier(null);
    });

    const scrollDisposable = activeEditor.onDidScrollChange(() => {
      updatePinnedPosition();
      setQuickActionState((current) => {
        if (!current) {
          return current;
        }
        const reference = current.info.declarationLocation.reference ?? current.info.usageContexts.all[0] ?? null;
        if (!reference) {
          return current;
        }
        const coordinates = getOverlayCoordinates(activeEditor, new monaco.Position(reference.line, reference.column));
        return coordinates ? { ...current, ...coordinates } : current;
      });
    });

    const selectionDisposable = activeEditor.onDidChangeCursorSelection(() => {
      setQuickActionState((current) => {
        if (!current) {
          return current;
        }
        const nextState = resolveTagAtSelection();
        if (!nextState || nextState.info.canonicalName !== current.info.canonicalName) {
          return current;
        }
        return { ...current, top: nextState.top, left: nextState.left };
      });
    });

    const handleShortcut = (event: KeyboardEvent): void => {
      const target = event.target as HTMLElement | null;
      const targetInsideEditor = Boolean(target && editorWrapRef.current?.contains(target));
      const editorHasFocus = activeEditor.hasTextFocus() || targetInsideEditor;
      if (!editorHasFocus) {
        return;
      }
      if (target && !activeEditor.hasTextFocus() && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key.toLowerCase() === "f") {
        event.preventDefault();
        setQuickActionState(null);
        setPinnedIdentifier(null);
        setInlineSearchOpen(true);
        window.requestAnimationFrame(() => {
          searchInputRef.current?.focus();
          searchInputRef.current?.select();
        });
        return;
      }
      if ((event.metaKey || event.ctrlKey) && !event.shiftKey && event.key === ".") {
        event.preventDefault();
        openQuickActionMenu();
      }
    };

    document.addEventListener("mousedown", handleOutsidePointer, true);
    document.addEventListener("keydown", handleEscape);
    document.addEventListener("keydown", handleShortcut, true);

    return () => {
      mouseMoveDisposable.dispose();
      mouseLeaveDisposable.dispose();
      mouseDownDisposable.dispose();
      scrollDisposable.dispose();
      selectionDisposable.dispose();
      document.removeEventListener("mousedown", handleOutsidePointer, true);
      document.removeEventListener("keydown", handleEscape);
      document.removeEventListener("keydown", handleShortcut, true);
    };
  }, [inlineSearchOpen, pinnedIdentifier, quickActionState, tagIntelligenceSource]);

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
      const activeEditor = editorRef.current;
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
      const activeEditor = editorRef.current;
      if (activeEditor) {
        highlightDecorationsRef.current = activeEditor.deltaDecorations(highlightDecorationsRef.current, []);
      }
    };
  }, [jumpToLocation, onSelectFile, resolvedFiles]);

  useEffect(() => {
    if (!tagIntelligenceCommand) {
      return;
    }

    const normalizedPath = normalizePath(tagIntelligenceCommand.file);
    const targetFile = resolvedFiles.find((file) => normalizePath(file.path) === normalizedPath);
    if (!targetFile) {
      return;
    }

    setSelectedPath(targetFile.path);
    onSelectFile?.(targetFile.path);

    const timer = window.setTimeout(() => {
      const activeEditor = getActiveEditorInstance();
      if (!activeEditor) {
        return;
      }
      const source = getLogicTagIntelligenceSource(targetFile.content || "");
      const info = source.getTagByIdentifier(tagIntelligenceCommand.tagName);
      if (!info) {
        return;
      }
      const declaration = source.getDeclaration(info.tagName);
      const usages = source.getAllUsages(info.tagName);
      const currentPinned = pinnedIdentifier && normalizePath(targetFile.path) === normalizePath(selectedPath) && pinnedIdentifier.info.canonicalName === info.canonicalName
        ? pinnedIdentifier
        : null;

      if (tagIntelligenceCommand.action === "highlight-all-usages") {
        highlightAllUsages(info);
        const anchor = declaration ?? usages[0];
        if (anchor) {
          const overlay = buildOverlayState(activeEditor, tagIntelligenceCommand.tagName, info, anchor, Math.max(0, usages.findIndex((item) => item.line === anchor.line && item.column === anchor.column)));
          if (overlay) {
            setPinnedIdentifier(overlay);
          }
        }
        return;
      }

      if (tagIntelligenceCommand.action === "jump-to-definition") {
        const target = declaration ?? usages[0];
        if (!target) {
          return;
        }
        focusOccurrence(info, target);
        const overlay = buildOverlayState(activeEditor, tagIntelligenceCommand.tagName, info, target, Math.max(0, usages.findIndex((item) => item.line === target.line && item.column === target.column)));
        if (overlay) {
          setPinnedIdentifier(overlay);
        }
        return;
      }

      if (tagIntelligenceCommand.action === "focus-reference") {
        const target = (declaration && declaration.line === tagIntelligenceCommand.line ? declaration : null)
          ?? usages.find(
            (item) =>
              item.line === tagIntelligenceCommand.line &&
              (tagIntelligenceCommand.column ? item.column === tagIntelligenceCommand.column : true)
          )
          ?? declaration
          ?? usages[0];
        if (!target) {
          return;
        }
        focusOccurrence(info, target);
        const overlay = buildOverlayState(activeEditor, tagIntelligenceCommand.tagName, info, target, Math.max(0, usages.findIndex((item) => item.line === target.line && item.column === target.column)));
        if (overlay) {
          setPinnedIdentifier(overlay);
        }
        return;
      }

      if (usages.length === 0) {
        return;
      }

      const currentIndex = currentPinned?.activeUsageIndex ?? 0;
      const nextIndex =
        tagIntelligenceCommand.action === "previous-usage"
          ? (currentIndex - 1 + usages.length) % usages.length
          : (currentIndex + 1) % usages.length;
      const target = usages[nextIndex];
      focusOccurrence(info, target);
      const overlay = buildOverlayState(activeEditor, tagIntelligenceCommand.tagName, info, target, nextIndex);
      if (overlay) {
        setPinnedIdentifier(overlay);
      }
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [onSelectFile, resolvedFiles, tagIntelligenceCommand]);

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
      clearSearchHighlights();
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
          {showChangeHighlights && baselineFile ? <span className="code-explorer-change-indicator">Showing changes</span> : null}
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
          {inlineSearchOpen ? (
            <div className="code-explorer-inline-search-shell">
              <input
                ref={searchInputRef}
                className="code-explorer-inline-search-input"
                type="text"
                value={inlineSearchQuery}
                onChange={(event) => {
                  setInlineSearchQuery(event.target.value);
                  setSearchActiveIndex(0);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    setInlineSearchOpen(false);
                    clearSearchHighlights();
                    window.requestAnimationFrame(() => {
                      getActiveEditorInstance()?.focus();
                    });
                    return;
                  }
                  if (event.key === "Enter") {
                    event.preventDefault();
                    if (inlineSearchMatches.length === 0) {
                      return;
                    }
                    setSearchActiveIndex((current) => {
                      const delta = event.shiftKey ? -1 : 1;
                      return (current + delta + inlineSearchMatches.length) % inlineSearchMatches.length;
                    });
                  }
                }}
                placeholder="Search current file"
                aria-label="Search current logic file"
              />
              <span className="code-explorer-inline-search-count">
                {inlineSearchMatches.length === 0
                  ? "No matches"
                  : `${Math.min(searchActiveIndex + 1, inlineSearchMatches.length)} of ${inlineSearchMatches.length}`}
              </span>
            </div>
          ) : null}
          <div ref={editorMountRef} className="code-explorer-editor" />
          {quickActionState ? (
            <div className="code-explorer-quick-actions" style={{ top: quickActionState.top, left: quickActionState.left }}>
              {quickActionState.mode === "menu" ? (
                <div className="code-explorer-quick-actions-grid" onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    setQuickActionState(null);
                    return;
                  }
                  if (event.key === "ArrowDown") {
                    event.preventDefault();
                    setQuickActionState((current) => current ? { ...current, activeIndex: (current.activeIndex + 1) % 4 } : current);
                    return;
                  }
                  if (event.key === "ArrowUp") {
                    event.preventDefault();
                    setQuickActionState((current) => current ? { ...current, activeIndex: (current.activeIndex - 1 + 4) % 4 } : current);
                  }
                }}>
                  {[
                    { label: "Rename", action: () => setQuickActionState((current) => current ? { ...current, mode: "rename", inputValue: current.info.tagName } : current) },
                    { label: "Remap", action: () => setQuickActionState((current) => current ? { ...current, mode: "remap", inputValue: current.info.tagName } : current) },
                    { label: "Change Type", action: () => setQuickActionState((current) => current ? { ...current, mode: "type", nextType: current.info.dataType || ST_TYPE_OPTIONS[0] || "BOOL" } : current) },
                    { label: "Highlight Usages", action: () => runQuickHighlightAction() },
                  ].map((item, index) => (
                    <button
                      key={item.label}
                      ref={(element) => {
                        quickActionButtonRefs.current[index] = element;
                      }}
                      className={`code-explorer-quick-action-btn ${quickActionState.activeIndex === index ? "is-active" : ""}`.trim()}
                      type="button"
                      onMouseEnter={() => setQuickActionState((current) => current ? { ...current, activeIndex: index } : current)}
                      onClick={item.action}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              ) : quickActionState.mode === "type" ? (
                <div className="code-explorer-quick-actions-form">
                  <strong>Change type for {quickActionState.info.tagName}</strong>
                  <select
                    ref={quickActionSelectRef}
                    className="code-explorer-quick-actions-select"
                    value={quickActionState.nextType}
                    onChange={(event) => setQuickActionState((current) => current ? { ...current, nextType: event.target.value } : current)}
                    onKeyDown={(event) => {
                      if (event.key === "Escape") {
                        event.preventDefault();
                        setQuickActionState((current) => current ? { ...current, mode: "menu" } : current);
                      }
                      if (event.key === "Enter") {
                        event.preventDefault();
                        applyQuickTypeChange();
                      }
                    }}
                  >
                    {ST_TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                  <div className="code-explorer-quick-actions-row">
                    <button className="code-explorer-quick-action-btn is-active" type="button" onClick={applyQuickTypeChange}>Apply</button>
                    <button className="code-explorer-quick-action-btn" type="button" onClick={() => setQuickActionState((current) => current ? { ...current, mode: "menu" } : current)}>Back</button>
                  </div>
                </div>
              ) : (
                <div className="code-explorer-quick-actions-form">
                  {(() => {
                    const renameMode = quickActionState.mode === "remap" ? "remap" : "rename";
                    return (
                      <>
                  <strong>{quickActionState.mode === "remap" ? `Remap ${quickActionState.info.tagName}` : `Rename ${quickActionState.info.tagName}`}</strong>
                  <input
                    ref={quickActionInputRef}
                    className="code-explorer-quick-actions-input"
                    type="text"
                    value={quickActionState.inputValue}
                    onChange={(event) => setQuickActionState((current) => current ? { ...current, inputValue: event.target.value } : current)}
                    onKeyDown={(event) => {
                      if (event.key === "Escape") {
                        event.preventDefault();
                        setQuickActionState((current) => current ? { ...current, mode: "menu" } : current);
                      }
                      if (event.key === "Enter") {
                        event.preventDefault();
                        applyQuickRenameOrRemap(renameMode);
                      }
                    }}
                  />
                  <div className="code-explorer-quick-actions-row">
                    <button className="code-explorer-quick-action-btn is-active" type="button" onClick={() => applyQuickRenameOrRemap(renameMode)}>Apply</button>
                    <button className="code-explorer-quick-action-btn" type="button" onClick={() => setQuickActionState((current) => current ? { ...current, mode: "menu" } : current)}>Back</button>
                  </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          ) : null}
          {hoveredIdentifier && !pinnedIdentifier ? (
            <div className="code-explorer-intel-tooltip" style={{ top: hoveredIdentifier.top, left: hoveredIdentifier.left }}>
              <strong>{hoveredIdentifier.matchedTagName}</strong>
              <span>
                {hoveredIdentifier.info.dataType || "Undeclared"} · {hoveredIdentifier.info.totalUsageCount} use{hoveredIdentifier.info.totalUsageCount === 1 ? "" : "s"}
              </span>
            </div>
          ) : null}
          {pinnedIdentifier ? (
            <div
              ref={pinnedPopoverRef}
              className="code-explorer-intel-popover"
              style={{ top: pinnedIdentifier.top, left: pinnedIdentifier.left }}
            >
              <TagIntelligenceDetailView
                matchedTagName={pinnedIdentifier.matchedTagName}
                info={pinnedIdentifier.info}
                activeUsageIndex={pinnedIdentifier.activeUsageIndex}
                usageOccurrences={usageOccurrencesForPinned}
                onFocusReference={(reference) => {
                  focusOccurrence(pinnedIdentifier.info, reference);
                  updatePinnedFromReference(pinnedIdentifier.info, pinnedIdentifier.matchedTagName, reference);
                }}
                onFocusLineReference={(lineReference) => {
                  const focused = focusLineReference(pinnedIdentifier.info, lineReference);
                  if (focused) {
                    updatePinnedFromReference(pinnedIdentifier.info, pinnedIdentifier.matchedTagName, focused);
                  }
                }}
                onJumpToDefinition={() => {
                  const definitionOccurrence = pinnedIdentifier.info.declarationLocation.reference ?? pinnedIdentifier.info.usageContexts.all[0];
                  if (definitionOccurrence) {
                    focusOccurrence(pinnedIdentifier.info, definitionOccurrence);
                    updatePinnedFromReference(pinnedIdentifier.info, pinnedIdentifier.matchedTagName, definitionOccurrence);
                  }
                }}
                onHighlightAllUsages={() => {
                  highlightAllUsages(pinnedIdentifier.info);
                }}
                onPreviousUsage={() => {
                  if (usageOccurrencesForPinned.length === 0) {
                    return;
                  }
                  const nextIndex = (pinnedIdentifier.activeUsageIndex - 1 + usageOccurrencesForPinned.length) % usageOccurrencesForPinned.length;
                  const target = usageOccurrencesForPinned[nextIndex];
                  focusOccurrence(pinnedIdentifier.info, target);
                  setPinnedIdentifier((current) => (current ? { ...current, anchor: target, activeUsageIndex: nextIndex } : current));
                }}
                onNextUsage={() => {
                  if (usageOccurrencesForPinned.length === 0) {
                    return;
                  }
                  const nextIndex = (pinnedIdentifier.activeUsageIndex + 1) % usageOccurrencesForPinned.length;
                  const target = usageOccurrencesForPinned[nextIndex];
                  focusOccurrence(pinnedIdentifier.info, target);
                  setPinnedIdentifier((current) => (current ? { ...current, anchor: target, activeUsageIndex: nextIndex } : current));
                }}
              />
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
