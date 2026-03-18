import type { PlantSignalRow } from "../services/api";

type PlantGraphTableProps = {
  rows: PlantSignalRow[];
  selectedTag: string;
  onSelectTag: (tag: string) => void;
  onTraceSignal: (row: PlantSignalRow) => void;
  onOpenControlLoop: (row: PlantSignalRow) => void;
  onOpenIOMapping: (row: PlantSignalRow) => void;
};

export default function PlantGraphTable({
  rows,
  selectedTag,
  onSelectTag,
  onTraceSignal,
  onOpenControlLoop,
  onOpenIOMapping,
}: PlantGraphTableProps) {
  const renderList = (items?: string[]): string => {
    if (!items || items.length === 0) {
      return "";
    }
    return items.join(", ");
  };

  if (rows.length === 0) {
    return <div className="plant-table-empty">No plant signals available. Run Parse to generate graph artifacts.</div>;
  }

  return (
    <div className="plant-table-wrap">
      <table className="plant-table" role="grid">
        <thead>
          <tr>
            <th>Tag</th>
            <th>Type</th>
            <th>Signal Type</th>
            <th>Process Unit</th>
            <th>Connected To</th>
            <th>Control Path</th>
            <th>Loop ID</th>
            <th>Confidence</th>
            <th>Source</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const active = selectedTag === row.tag;
            return (
              <tr
                key={row.tag}
                className={active ? "active" : ""}
                onClick={() => onSelectTag(row.tag)}
              >
                <td>{row.tag}</td>
                <td>{row.type || ""}</td>
                <td>{row.signal_type || ""}</td>
                <td>{row.process_unit || ""}</td>
                <td>{renderList(row.connected_to)}</td>
                <td>{renderList(row.control_path)}</td>
                <td>{renderList(row.loop_ids) || row.loop_id || ""}</td>
                <td>
                  {typeof row.confidence === "number" ? (
                    <span className="confidence-pill">{row.confidence.toFixed(2)}</span>
                  ) : (
                    ""
                  )}
                </td>
                <td>{row.source ? <span className={`source-badge source-${row.source.replace(/\+/g, "-").toLowerCase()}`}>{row.source}</span> : ""}</td>
                <td>
                  <div className="plant-table-actions" onClick={(event) => event.stopPropagation()}>
                    <button className="command-btn" type="button" onClick={() => onTraceSignal(row)}>Trace Signal</button>
                    <button className="command-btn" type="button" onClick={() => onOpenControlLoop(row)}>Open CL</button>
                    <button className="command-btn" type="button" onClick={() => onOpenIOMapping(row)}>Open IO Mapping</button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
