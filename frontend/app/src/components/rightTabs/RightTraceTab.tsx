import RightWhyTracePanel from "./RightWhyTracePanel";
import type { SystemContext } from "../../intelligence/systemContext";

type RightTraceTabProps = {
  tracePath: string[];
  systemContext?: SystemContext | null;
  whyTraceTag?: string | null;
  onCloseWhyTrace?: () => void;
  onSelectTraceTag?: (tag: string) => void;
};

export default function RightTraceTab({ tracePath, systemContext = null, whyTraceTag = null, onCloseWhyTrace, onSelectTraceTag }: RightTraceTabProps) {
  if (whyTraceTag) {
    return <RightWhyTracePanel tag={whyTraceTag} onClose={onCloseWhyTrace} onSelectTag={onSelectTraceTag} />;
  }

  const resolvedTracePath =
    tracePath.length > 0
      ? tracePath
      : [
          ...(systemContext?.graph.upstream || []),
          ...(systemContext?.tag ? [systemContext.tag] : []),
          ...(systemContext?.graph.downstream || []),
        ];

  return (
    <>
      <div className="panel-subtitle">Signal Path</div>
      <ol className="trace-chain trace-chain-ordered">
        {(resolvedTracePath.length ? resolvedTracePath : ["No active trace. Right-click a node to trace signal path."]).map((node) => (
          <li key={node}>{node}</li>
        ))}
      </ol>

      <div className="panel-subtitle">Graph Relationships</div>
      <ul className="trace-chain">
        <li>Upstream: {(systemContext?.graph.upstream || []).join(", ") || "none"}</li>
        <li>Downstream: {(systemContext?.graph.downstream || []).join(", ") || "none"}</li>
        <li>Edges: {systemContext?.graph.edges.length || 0}</li>
      </ul>
    </>
  );
}
