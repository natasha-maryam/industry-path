import { AlertTriangle } from "lucide-react";
import type { IOMappingIssue, IOMappingTableRow } from "../../services/api";
import { buildIOMappingSummary, groupMappingsByPlcAndSlot } from "./ioMappingPreview";

type RightIOMappingTabProps = {
  selectedNodeId?: string;
  mappingRows: IOMappingTableRow[];
  mappingIssues?: IOMappingIssue[];
  selectedTag?: string | null;
  onSelectTag?: (tag: string) => void;
};

export default function RightIOMappingTab({
  selectedNodeId = "",
  mappingRows,
  mappingIssues = [],
  selectedTag = null,
  onSelectTag,
}: RightIOMappingTabProps) {
  const grouped = groupMappingsByPlcAndSlot(mappingRows, mappingIssues);
  const summary = buildIOMappingSummary(mappingRows);

  return (
    <>
      <div className="panel-subtitle">IO Mapping Preview</div>
      {selectedNodeId ? <div className="panel-subtitle">Selected node: {selectedNodeId}</div> : null}
      {mappingRows.length === 0 ? (
        <div className="monitor-frame">
          {selectedNodeId
            ? `No IO mappings found for selected node ${selectedNodeId}.`
            : "No signals available for mapping preview."}
        </div>
      ) : (
        <div className="right-io-preview">
          <div className="right-io-summary-grid">
            <span>Total: {summary.totalSignals}</span>
            <span>AI: {summary.ai}</span>
            <span>AO: {summary.ao}</span>
            <span>DI: {summary.di}</span>
            <span>DO: {summary.doCount}</span>
          </div>

          <div className="right-io-groups">
            {grouped.map((plc) => (
              <article key={plc.plcId} className="right-io-plc-group">
                <header className="right-io-plc-header">{plc.plcId}</header>
                <div className="right-io-slot-list">
                  {plc.slots.map((slotGroup) => (
                    <section key={`${plc.plcId}-slot-${slotGroup.slot}`} className="right-io-slot-group">
                      <h5>Slot {slotGroup.slot}</h5>
                      <ul>
                        {slotGroup.channels.map((item) => (
                          <li key={`${plc.plcId}-${slotGroup.slot}-${item.channel}-${item.tag}`}>
                            <button
                              type="button"
                              className={`right-io-item ${selectedTag && selectedTag.toUpperCase() === item.tag.toUpperCase() ? "selected" : ""}`}
                              onClick={() => onSelectTag?.(item.tag)}
                            >
                              <span className="value-mono">CH{item.channel}</span>
                              <span className="value-mono">{item.tag}</span>
                              <span className="right-io-type">{item.ioType}</span>
                              {item.deviceType ? <span className="right-io-device">{item.deviceType}</span> : null}
                              {item.hasWarning ? (
                                <span className="right-io-warning" title="Mapping warning">
                                  <AlertTriangle size={10} />
                                </span>
                              ) : null}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
