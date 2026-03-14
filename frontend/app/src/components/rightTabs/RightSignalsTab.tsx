import type { Equipment } from "./types";

type RightSignalsTabProps = {
  selectedEquipment: Equipment;
};

export default function RightSignalsTab({ selectedEquipment }: RightSignalsTabProps) {
  return (
    <>
      <div className="panel-subtitle">Signal List</div>
      <ul className="trace-chain">
        {(selectedEquipment.signals.length ? selectedEquipment.signals : ["No explicit signals available"]).map((signal) => (
          <li key={signal}>{signal}</li>
        ))}
      </ul>
    </>
  );
}
