import type { ControlLoopRecord } from "../../services/api";

type RightControlLoopsTabProps = {
  loops: ControlLoopRecord[];
  loading?: boolean;
  error?: string | null;
  selectedLoopTag?: string | null;
  onDetectLoops?: () => void;
  onSelectLoop: (loop: ControlLoopRecord) => void;
  onViewLoop: (loop: ControlLoopRecord) => void;
  onEditStrategy: (loop: ControlLoopRecord) => void;
  onGenerateLogic: (loop: ControlLoopRecord) => void;
  onTraceLoop: (loop: ControlLoopRecord) => void;
  onSimulate: (loop: ControlLoopRecord) => void;
};

export default function RightControlLoopsTab({
  loops,
  loading = false,
  error = null,
  selectedLoopTag = null,
  onDetectLoops,
  onSelectLoop,
  onViewLoop,
  onEditStrategy,
  onGenerateLogic,
  onTraceLoop,
  onSimulate,
}: RightControlLoopsTabProps) {
  return (
    <>
      <div className="panel-subtitle">Detected Control Loops</div>
      {loading ? (
        <div className="monitor-frame">Loading control loops...</div>
      ) : error ? (
        <div className="monitor-frame">
          <div>{error}</div>
          <button className="command-btn" type="button" onClick={onDetectLoops}>
            Detect Control Loops
          </button>
        </div>
      ) : loops.length === 0 ? (
        <div className="monitor-frame">
          <div>No control loops detected yet.</div>
          <button className="command-btn" type="button" onClick={onDetectLoops}>
            Detect Control Loops
          </button>
        </div>
      ) : (
        <div className="plant-table-wrap">
          <table className="plant-table" role="grid">
            <thead>
              <tr>
                <th>Loop ID</th>
                <th>Sensor</th>
                <th>Process</th>
                <th>Actuator</th>
                <th>Controller</th>
                <th>Loop Type</th>
                <th>Strategy</th>
                <th>Setpoint</th>
                <th>Output</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loops.map((loop) => (
                <tr
                  key={loop.id}
                  className={selectedLoopTag === loop.loop_tag ? "active" : ""}
                  onClick={() => onSelectLoop(loop)}
                >
                  <td>{loop.loop_tag}</td>
                  <td>{loop.sensor_tag}</td>
                  <td>{loop.process_unit || ""}</td>
                  <td>{loop.actuator_tag}</td>
                  <td>{loop.controller_tag || ""}</td>
                  <td>{loop.loop_type}</td>
                  <td>{loop.control_strategy}</td>
                  <td>{loop.setpoint_tag || ""}</td>
                  <td>{loop.output_tag || ""}</td>
                  <td>
                    <span className="confidence-pill">{Number(loop.confidence || 0).toFixed(2)}</span>
                  </td>
                  <td>{loop.status}</td>
                  <td>
                    <div className="plant-table-actions" onClick={(event) => event.stopPropagation()}>
                      <button className="command-btn" type="button" onClick={() => onViewLoop(loop)}>View Loop</button>
                      <button className="command-btn" type="button" onClick={() => onEditStrategy(loop)}>Edit Strategy</button>
                      <button className="command-btn" type="button" onClick={() => onGenerateLogic(loop)}>Generate Logic</button>
                      <button className="command-btn" type="button" onClick={() => onTraceLoop(loop)}>Trace Loop</button>
                      <button className="command-btn" type="button" onClick={() => onSimulate(loop)}>Simulate</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
