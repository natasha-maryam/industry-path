import type { Equipment } from "./types";

type RightSignalsTabProps = {
  selectedEquipment: Equipment;
  runtimeTelemetryTags?: Record<string, unknown>;
  forcedTags?: string[];
};

export default function RightSignalsTab({ selectedEquipment, runtimeTelemetryTags = {}, forcedTags = [] }: RightSignalsTabProps) {
  const forcedSet = new Set(forcedTags.map((tag) => tag.toUpperCase()));
  const selectedSignals = selectedEquipment.signals.length ? selectedEquipment.signals : [];

  const visibleSignals =
    selectedSignals.length > 0
      ? selectedSignals
      : Object.keys(runtimeTelemetryTags)
          .filter((key) => !key.startsWith("DIAGNOSTICS_") && !key.startsWith("FORCED_INPUT_"))
          .slice(0, 20);

  return (
    <>
      <div className="panel-subtitle">Signal List</div>
      <ul className="trace-chain">
        {visibleSignals.length > 0 ? (
          visibleSignals.map((signal) => {
            const liveValue = runtimeTelemetryTags[signal];
            const isForced = forcedSet.has(signal.toUpperCase());
            return <li key={signal}>{`${signal}: ${String(liveValue ?? "-")}${isForced ? " (forced)" : ""}`}</li>;
          })
        ) : (
          <li>No evaluated runtime signals available</li>
        )}
      </ul>
    </>
  );
}
