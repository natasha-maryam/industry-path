import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Clock3, FileText, Folder, LoaderCircle, XCircle } from "lucide-react";
import type { PanelStatus, STGenerationPanelResponse } from "../services/api";
import "../styles/st-generation-panel.css";

type STGeneratedFile = {
  path: string;
  status?: PanelStatus;
  template_name?: string | null;
};

type RenderedTemplateSummary = {
  template_name: string;
  rendered_files: number;
};

export type STGenerationPanelData = STGenerationPanelResponse & {
  total_files_generated?: number;
  output_root?: string | null;
  generated_files?: STGeneratedFile[];
  rendered_templates?: RenderedTemplateSummary[];
};

type STGenerationPanelProps = {
  data: STGenerationPanelData | null;
  loading?: boolean;
  failedMessage?: string | null;
  requiredPreviousStep?: string;
  onRetry?: () => void;
};

type FolderGroup = {
  folder: string;
  files: STGeneratedFile[];
};

const SUPPORTED_FOLDERS = ["equipment", "control_loops", "sequences", "interlocks", "alarms", "utilities"] as const;

const statusIcon = (status: PanelStatus) => {
  if (status === "running") {
    return <LoaderCircle size={14} className="st-generation-icon-spin" />;
  }
  if (status === "success") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "failed") {
    return <XCircle size={14} />;
  }
  if (status === "warning") {
    return <AlertTriangle size={14} />;
  }
  return <Clock3 size={14} />;
};

const statusLabel = (status: PanelStatus): string => {
  if (status === "running") {
    return "Running";
  }
  if (status === "success") {
    return "Success";
  }
  if (status === "failed") {
    return "Failed";
  }
  if (status === "warning") {
    return "Warning";
  }
  return "Idle";
};

const parseGeneratedFilesFromCode = (code: string): STGeneratedFile[] => {
  const matches = code.match(/\(\*\s*=====\s*FILE:\s*([^*]+?)\s*=====\s*\*\)/g);
  if (!matches || matches.length === 0) {
    return [{ path: "main.st" }];
  }

  return matches
    .map((match) => {
      const pathMatch = match.match(/FILE:\s*([^*]+?)\s*=====/);
      return { path: pathMatch?.[1]?.trim() ?? "main.st" };
    })
    .filter((item, index, all) => all.findIndex((candidate) => candidate.path === item.path) === index);
};

const normalizeFilePath = (path: string): string => path.replace(/^\/+/, "").replace(/\\/g, "/").trim();

const toFolderName = (path: string): string => {
  const normalized = normalizeFilePath(path);
  if (!normalized.includes("/")) {
    return "root";
  }
  return normalized.split("/")[0] || "root";
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function STGenerationPanel({
  data,
  loading = false,
  failedMessage = null,
  requiredPreviousStep = "Logic Completion",
  onRetry,
}: STGenerationPanelProps) {
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    root: true,
    equipment: true,
    control_loops: true,
  });

  const generatedFiles = useMemo<STGeneratedFile[]>(() => {
    if (!data) {
      return [];
    }

    if (data.generated_files && data.generated_files.length > 0) {
      return data.generated_files.map((file) => ({ ...file, path: normalizeFilePath(file.path) }));
    }

    return parseGeneratedFilesFromCode(data.st_code ?? "").map((file) => ({ ...file, path: normalizeFilePath(file.path) }));
  }, [data]);

  const totalFiles = useMemo<number>(() => {
    if (!data) {
      return 0;
    }
    if (typeof data.total_files_generated === "number") {
      return data.total_files_generated;
    }
    return generatedFiles.length;
  }, [data, generatedFiles.length]);

  const folderGroups = useMemo<FolderGroup[]>(() => {
    const grouped = new Map<string, STGeneratedFile[]>();

    for (const folder of SUPPORTED_FOLDERS) {
      grouped.set(folder, []);
    }

    grouped.set("root", []);

    for (const file of generatedFiles) {
      const folder = toFolderName(file.path);
      const existing = grouped.get(folder) ?? [];
      grouped.set(folder, [...existing, file]);
    }

    return [...grouped.entries()].map(([folder, files]) => ({ folder, files }));
  }, [generatedFiles]);

  const templateSummary = useMemo<RenderedTemplateSummary[]>(() => {
    if (!data) {
      return [];
    }

    if (data.rendered_templates && data.rendered_templates.length > 0) {
      return data.rendered_templates;
    }

    const grouped = new Map<string, number>();
    for (const file of generatedFiles) {
      const template = file.template_name?.trim() || toFolderName(file.path);
      grouped.set(template, (grouped.get(template) ?? 0) + 1);
    }

    return [...grouped.entries()].map(([template_name, rendered_files]) => ({ template_name, rendered_files }));
  }, [data, generatedFiles]);

  if (loading) {
    return <section className="st-generation-panel st-generation-state">Generating ST files...</section>;
  }

  if (failedMessage) {
    return (
      <section className="st-generation-panel st-generation-state error">
        <span>{failedMessage}</span>
        <button className="st-generation-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
          Retry
        </button>
      </section>
    );
  }

  if (!data) {
    return <section className="st-generation-panel st-generation-state">No ST generation result available yet. Complete {requiredPreviousStep} first.</section>;
  }

  return (
    <section className="st-generation-panel">
      <header className="st-generation-header">
        <div className="st-generation-title-row">
          <h3>ST Generation Results</h3>
          <span className={`st-generation-status ${data.status}`}>{statusIcon(data.status)} {statusLabel(data.status)}</span>
        </div>
        <div className="st-generation-meta-grid">
          <span>Total Files: {totalFiles}</span>
          <span>Generated: {formatTimestamp(data.generated_at)}</span>
          <span>Output: {data.output_root || "main.st + folders"}</span>
          <span>Generator: {data.generator_version}</span>
        </div>
      </header>

      {data.status === "warning" || (data.warnings?.length ?? 0) > 0 ? (
        <div className="st-generation-warning">
          <strong>Warning:</strong> Generation completed with validation issues. Review warnings before verification.
        </div>
      ) : null}

      <div className="st-generation-content-grid">
        <article className="st-generation-card">
          <h4>Folder Structure Preview</h4>
          <ul className="st-generation-tree">
            <li>
              <button
                className="st-generation-tree-toggle"
                onClick={() =>
                  setExpandedFolders((prev) => ({
                    ...prev,
                    root: !prev.root,
                  }))
                }
                type="button"
              >
                {expandedFolders.root ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                <Folder size={12} />
                <span>root</span>
              </button>

              {expandedFolders.root ? (
                <ul>
                  {folderGroups.map((group) => (
                    <li key={group.folder}>
                      <button
                        className="st-generation-tree-toggle"
                        onClick={() =>
                          setExpandedFolders((prev) => ({
                            ...prev,
                            [group.folder]: !prev[group.folder],
                          }))
                        }
                        type="button"
                      >
                        {expandedFolders[group.folder] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                        <Folder size={12} />
                        <span>{group.folder}</span>
                        <span className="st-generation-file-count">{group.files.length}</span>
                      </button>

                      {expandedFolders[group.folder] && group.files.length > 0 ? (
                        <ul>
                          {group.files.map((file) => (
                            <li key={`${group.folder}-${file.path}`} className="st-generation-file-row">
                              <FileText size={11} />
                              <span>{group.folder === "root" ? file.path : file.path.replace(`${group.folder}/`, "")}</span>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          </ul>
        </article>

        <article className="st-generation-card">
          <h4>Rendered Templates</h4>
          {templateSummary.length > 0 ? (
            <ul className="st-generation-summary-list">
              {templateSummary.map((item) => (
                <li key={item.template_name}>
                  <span>{item.template_name}</span>
                  <strong>{item.rendered_files}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <div className="st-generation-empty">No rendered template summary available.</div>
          )}
        </article>
      </div>
    </section>
  );
}
