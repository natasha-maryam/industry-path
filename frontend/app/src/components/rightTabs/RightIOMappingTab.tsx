import type { Equipment } from "./types";

type RightIOMappingTabProps = {
  selectedEquipment: Equipment;
};

const inferSignalType = (signal: string): string => {
  const token = signal.toUpperCase();
  if (token.includes("PV") || token.includes("LEVEL") || token.includes("FLOW") || token.includes("PRESS")) {
    return "Analog";
  }
  if (token.includes("CMD") || token.includes("RUN") || token.includes("TRIP") || token.includes("FAULT")) {
    return "Digital";
  }
  return "Unknown";
};

const inferIOType = (signal: string): string => {
  const token = signal.toUpperCase();
  if (token.includes("_PV") || token.includes("_AI") || token.includes("_MEAS")) {
    return "AI";
  }
  if (token.includes("_SP") || token.includes("_AO") || token.includes("_OUT")) {
    return "AO";
  }
  if (token.includes("_DI") || token.includes("_FB")) {
    return "DI";
  }
  if (token.includes("_DO") || token.includes("_CMD") || token.includes("RUN")) {
    return "DO";
  }
  return "N/A";
};

export default function RightIOMappingTab({ selectedEquipment }: RightIOMappingTabProps) {
  const rows = selectedEquipment.signals.map((signal, index) => ({
    signal,
    signalType: inferSignalType(signal),
    ioType: inferIOType(signal),
    address: `%I${index}`,
  }));

  return (
    <>
      <div className="panel-subtitle">IO Mapping Preview</div>
      {rows.length === 0 ? (
        <div className="monitor-frame">No signals available for mapping preview.</div>
      ) : (
        <div className="right-mini-table-wrap">
          <table className="right-mini-table">
            <thead>
              <tr>
                <th>Tag</th>
                <th>Signal Type</th>
                <th>IO Type</th>
                <th>Address</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.signal}>
                  <td className="value-mono">{row.signal}</td>
                  <td>{row.signalType}</td>
                  <td className="value-mono">{row.ioType}</td>
                  <td className="value-mono">{row.address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
