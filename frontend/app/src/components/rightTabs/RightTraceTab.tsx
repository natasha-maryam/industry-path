import RightWhyTracePanel from "./RightWhyTracePanel";

type RightTraceTabProps = {
  tracePath: string[];
  whyTraceTag?: string | null;
  onCloseWhyTrace?: () => void;
};

export default function RightTraceTab({ tracePath, whyTraceTag = null, onCloseWhyTrace }: RightTraceTabProps) {
  if (whyTraceTag) {
    return <RightWhyTracePanel tag={whyTraceTag} onClose={onCloseWhyTrace} />;
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
