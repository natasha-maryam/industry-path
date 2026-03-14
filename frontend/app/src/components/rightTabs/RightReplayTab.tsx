type RightReplayTabProps = {
  replayPoint: number;
};

export default function RightReplayTab({ replayPoint }: RightReplayTabProps) {
  const replayTime = `12:${String(Math.floor(replayPoint / 2)).padStart(2, "0")}:34`;

  return (
    <dl className="kv kv-technical">
      <dt>Time</dt>
      <dd className="value-mono">{replayTime}</dd>
      <dt>Tank-101</dt>
      <dd className="value-mono">{`${replayPoint}% level`}</dd>
      <dt>Pump-101</dt>
      <dd>{replayPoint % 2 === 0 ? "RUNNING" : "IDLE"}</dd>
      <dt>Flow Rate</dt>
      <dd className="value-mono">{`${20 + Math.floor(replayPoint / 4)} m3/h`}</dd>
    </dl>
  );
}
