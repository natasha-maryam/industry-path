type RightTraceTabProps = {
  tracePath: string[];
};

export default function RightTraceTab({ tracePath }: RightTraceTabProps) {
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
