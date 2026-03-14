import type { Equipment } from "./types";

type RightDetailsTabProps = {
  selectedEquipment: Equipment;
};

export default function RightDetailsTab({ selectedEquipment }: RightDetailsTabProps) {
  return (
    <>
      <dl className="kv kv-technical">
        <dt>Equipment</dt>
        <dd>{selectedEquipment.id}</dd>
        <dt>Type</dt>
        <dd>{selectedEquipment.type}</dd>
        <dt>Status</dt>
        <dd>{selectedEquipment.status}</dd>
        <dt>Process Unit</dt>
        <dd>{selectedEquipment.processUnit ?? "N/A"}</dd>
        <dt>Control Role</dt>
        <dd>{selectedEquipment.controlRole ?? "N/A"}</dd>
        <dt>Signal Type</dt>
        <dd>{selectedEquipment.signalType ?? "N/A"}</dd>
        <dt>Instrument Role</dt>
        <dd>{selectedEquipment.instrumentRole ?? "N/A"}</dd>
        <dt>Power Rating</dt>
        <dd>{selectedEquipment.powerRating ?? "N/A"}</dd>
      </dl>

      <div className="panel-subtitle">Connections</div>
      <ul className="trace-chain">
        {(selectedEquipment.connections.length ? selectedEquipment.connections : ["No known process connections"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Control Path</div>
      <ul className="trace-chain">
        {(selectedEquipment.controlPath.length ? selectedEquipment.controlPath : ["No control path available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Controls</div>
      <ul className="trace-chain">
        {(selectedEquipment.controls.length ? selectedEquipment.controls : ["No control targets available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Measures</div>
      <ul className="trace-chain">
        {(selectedEquipment.measures.length ? selectedEquipment.measures : ["No measurement targets available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Inference Confidence</div>
      <ul className="trace-chain">
        {Object.entries(selectedEquipment.metadataConfidence).length ? (
          Object.entries(selectedEquipment.metadataConfidence)
            .sort((left, right) => right[1] - left[1])
            .slice(0, 5)
            .map(([key, value]) => <li key={key}>{`${key}: ${(value * 100).toFixed(0)}%`}</li>)
        ) : (
          <li>No confidence scores available</li>
        )}
      </ul>
    </>
  );
}
