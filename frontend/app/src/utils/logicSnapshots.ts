import type { GeneratedLogicFile } from "../components/CodeExplorerPanel";

export type LogicSnapshotSource =
  | "generated"
  | "manual-edit"
  | "quick-edit"
  | "validation-fix"
  | "restore"
  | "restore-backup";

export type LogicSnapshot = {
  id: string;
  createdAt: string;
  source: LogicSnapshotSource;
  label: string;
  selectedFilePath: string | null;
  generatedLogic: string;
  files: GeneratedLogicFile[];
  signature: string;
};

export const MAX_LOGIC_SNAPSHOTS = 18;

function hashText(value: string): string {
  let hash = 5381;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 33) ^ value.charCodeAt(index);
  }
  return (hash >>> 0).toString(36);
}

export function cloneGeneratedLogicFiles(files: GeneratedLogicFile[]): GeneratedLogicFile[] {
  return files.map((file) => ({ ...file }));
}

export function buildLogicSnapshotSignature(files: GeneratedLogicFile[]): string {
  if (!files.length) {
    return "empty";
  }
  const serialized = files
    .map((file) => `${file.path}\n${file.content}`)
    .join("\n/*::snapshot-split::*/\n");
  return hashText(serialized);
}

export function describeLogicSnapshotSource(source: LogicSnapshotSource): string {
  switch (source) {
    case "generated":
      return "Generated logic";
    case "quick-edit":
      return "Quick edit";
    case "validation-fix":
      return "Validation fix";
    case "restore":
      return "Restored version";
    case "restore-backup":
      return "Pre-restore backup";
    case "manual-edit":
    default:
      return "Manual edit";
  }
}

export function buildLogicSnapshot(params: {
  files: GeneratedLogicFile[];
  generatedLogic: string;
  selectedFilePath: string | null;
  source: LogicSnapshotSource;
  createdAt?: string;
  label?: string;
}): LogicSnapshot {
  const createdAt = params.createdAt || new Date().toISOString();
  const signature = buildLogicSnapshotSignature(params.files);
  return {
    id: `${createdAt}-${signature}`,
    createdAt,
    source: params.source,
    label: params.label || describeLogicSnapshotSource(params.source),
    selectedFilePath: params.selectedFilePath,
    generatedLogic: params.generatedLogic,
    files: cloneGeneratedLogicFiles(params.files),
    signature,
  };
}

export function insertLogicSnapshot(history: LogicSnapshot[], snapshot: LogicSnapshot, maxSnapshots = MAX_LOGIC_SNAPSHOTS): LogicSnapshot[] {
  if (history[0]?.signature === snapshot.signature) {
    return history;
  }
  return [snapshot, ...history].slice(0, maxSnapshots);
}

export function formatRelativeSavedTime(timestamp: string, now = Date.now()): string {
  const value = new Date(timestamp).getTime();
  if (!Number.isFinite(value)) {
    return "just now";
  }
  const diffSeconds = Math.max(0, Math.floor((now - value) / 1000));
  if (diffSeconds < 5) {
    return "just now";
  }
  if (diffSeconds < 60) {
    return `${diffSeconds} sec ago`;
  }
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
}
