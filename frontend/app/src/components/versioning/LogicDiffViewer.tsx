import { useEffect, useMemo, useRef, useState } from "react";
import * as monaco from "monaco-editor";
import type { VersionDiffResponse } from "../../types/versioning";

type LogicDiffViewerProps = {
  diff: VersionDiffResponse | null;
  loading?: boolean;
};

type ParsedDiff = {
  original: string;
  modified: string;
};

const parseUnifiedDiff = (input: string): ParsedDiff => {
  const original: string[] = [];
  const modified: string[] = [];
  const lines = input.split("\n");

  for (const line of lines) {
    if (line.startsWith("--- ") || line.startsWith("+++ ") || line.startsWith("@@ ")) {
      continue;
    }
    if (line.startsWith("+")) {
      modified.push(line.slice(1));
      continue;
    }
    if (line.startsWith("-")) {
      original.push(line.slice(1));
      continue;
    }
    original.push(line.startsWith(" ") ? line.slice(1) : line);
    modified.push(line.startsWith(" ") ? line.slice(1) : line);
  }

  return {
    original: original.join("\n"),
    modified: modified.join("\n"),
  };
};

export default function LogicDiffViewer({ diff, loading = false }: LogicDiffViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<monaco.editor.IStandaloneDiffEditor | null>(null);
  const originalModelRef = useRef<monaco.editor.ITextModel | null>(null);
  const modifiedModelRef = useRef<monaco.editor.ITextModel | null>(null);

  const files = useMemo(() => (diff ? Object.keys(diff.logic_diff || {}) : []), [diff]);
  const [selectedFile, setSelectedFile] = useState<string>(files[0] || "");

  useEffect(() => {
    if (!files.includes(selectedFile)) {
      setSelectedFile(files[0] || "");
    }
  }, [files, selectedFile]);

  useEffect(() => {
    if (!mountRef.current || !diff || !selectedFile) {
      return;
    }

    const raw = diff.logic_diff[selectedFile] || "";
    const parsed = parseUnifiedDiff(raw);

    if (!editorRef.current) {
      editorRef.current = monaco.editor.createDiffEditor(mountRef.current, {
        readOnly: true,
        automaticLayout: true,
        minimap: { enabled: false },
        renderSideBySide: true,
        lineNumbers: "on",
        fontSize: 12,
      });
    }

    originalModelRef.current?.dispose();
    modifiedModelRef.current?.dispose();
    originalModelRef.current = monaco.editor.createModel(parsed.original, "pascal");
    modifiedModelRef.current = monaco.editor.createModel(parsed.modified, "pascal");
    editorRef.current.setModel({
      original: originalModelRef.current,
      modified: modifiedModelRef.current,
    });

    return () => {
      originalModelRef.current?.dispose();
      modifiedModelRef.current?.dispose();
      originalModelRef.current = null;
      modifiedModelRef.current = null;
    };
  }, [diff, selectedFile]);

  useEffect(() => {
    return () => {
      editorRef.current?.dispose();
      editorRef.current = null;
      originalModelRef.current?.dispose();
      modifiedModelRef.current?.dispose();
    };
  }, []);

  if (loading) {
    return <div className="monitor-frame">Loading diff…</div>;
  }

  if (!diff) {
    return <div className="monitor-frame">Select two versions and run compare to view logic diff.</div>;
  }

  if (files.length === 0) {
    return <div className="monitor-frame">No logic file changes found. Metadata diff only.</div>;
  }

  return (
    <section className="logic-diff-viewer">
      <div className="logic-diff-toolbar">
        <strong>Logic Diff</strong>
        <select value={selectedFile} onChange={(event) => setSelectedFile(event.target.value)}>
          {files.map((file) => (
            <option key={file} value={file}>{file}</option>
          ))}
        </select>
      </div>
      <div className="logic-diff-surface" ref={mountRef} />
    </section>
  );
}
