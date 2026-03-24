import type { SavedEngineeringViewDiff } from "../services/api";

type DiffViewerProps = {
  diff: SavedEngineeringViewDiff | null;
  loading?: boolean;
  error?: string | null;
};

const toText = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
};

export default function DiffViewer({ diff, loading = false, error = null }: DiffViewerProps) {
  if (loading) {
    return <div className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600">Computing diff...</div>;
  }

  if (error) {
    return <div className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">{error}</div>;
  }

  if (!diff) {
    return <div className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-500">Select two snapshots to compare.</div>;
  }

  return (
    <div className="rounded border border-slate-200 bg-white p-2">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-700">
        <span className="rounded border border-slate-300 bg-slate-50 px-2 py-0.5">Added: {diff.summary.added}</span>
        <span className="rounded border border-slate-300 bg-slate-50 px-2 py-0.5">Removed: {diff.summary.removed}</span>
        <span className="rounded border border-slate-300 bg-slate-50 px-2 py-0.5">Changed: {diff.summary.changed}</span>
      </div>

      <div className="max-h-48 overflow-auto rounded border border-slate-200">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
            <tr>
              <th className="border-b border-slate-200 px-2 py-1">Tag</th>
              <th className="border-b border-slate-200 px-2 py-1">Status</th>
              <th className="border-b border-slate-200 px-2 py-1">Field</th>
              <th className="border-b border-slate-200 px-2 py-1">Before</th>
              <th className="border-b border-slate-200 px-2 py-1">After</th>
            </tr>
          </thead>
          <tbody>
            {diff.added.map((item) => (
              <tr key={`added-${item.tag}`}>
                <td className="border-b border-slate-100 px-2 py-1">{item.tag}</td>
                <td className="border-b border-slate-100 px-2 py-1 text-green-700">added</td>
                <td className="border-b border-slate-100 px-2 py-1">—</td>
                <td className="border-b border-slate-100 px-2 py-1">—</td>
                <td className="border-b border-slate-100 px-2 py-1">{toText(item.after)}</td>
              </tr>
            ))}
            {diff.removed.map((item) => (
              <tr key={`removed-${item.tag}`}>
                <td className="border-b border-slate-100 px-2 py-1">{item.tag}</td>
                <td className="border-b border-slate-100 px-2 py-1 text-red-700">removed</td>
                <td className="border-b border-slate-100 px-2 py-1">—</td>
                <td className="border-b border-slate-100 px-2 py-1">{toText(item.before)}</td>
                <td className="border-b border-slate-100 px-2 py-1">—</td>
              </tr>
            ))}
            {diff.changed.flatMap((item) =>
              item.fields.map((field, index) => (
                <tr key={`changed-${item.tag}-${field.field}-${index}`}>
                  <td className="border-b border-slate-100 px-2 py-1">{item.tag}</td>
                  <td className="border-b border-slate-100 px-2 py-1 text-amber-700">changed</td>
                  <td className="border-b border-slate-100 px-2 py-1">{field.field}</td>
                  <td className="border-b border-slate-100 px-2 py-1">{toText(field.before)}</td>
                  <td className="border-b border-slate-100 px-2 py-1">{toText(field.after)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
