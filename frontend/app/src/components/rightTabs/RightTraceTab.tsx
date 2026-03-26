import RightWhyTracePanel from "./RightWhyTracePanel";

type RightTraceTabProps = {
  tracePath: string[];
  whyTraceTag?: string | null;
  onCloseWhyTrace?: () => void;
  onSelectTraceTag?: (tag: string) => void;
};

export default function RightTraceTab({ tracePath, whyTraceTag = null, onCloseWhyTrace, onSelectTraceTag }: RightTraceTabProps) {
  if (whyTraceTag) {
    return <RightWhyTracePanel tag={whyTraceTag} onClose={onCloseWhyTrace} onSelectTag={onSelectTraceTag} />;
  }

  return (
    <>
      <div className="panel-subtitle">Signal Path</div>
      <ol className="trace-chain trace-chain-ordered">
        {(tracePath.length ? tracePath : ["No active trace. Right-click a node to trace signal path."]).map((node) => (
          <li key={node}>{node}</li>
        ))}
      </ol>
    </>
  );
}
