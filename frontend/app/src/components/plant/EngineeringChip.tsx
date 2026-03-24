import { Chip } from "./Chip";

type EngineeringChipProps = {
  label: string;
  onClick?: (value: string) => void;
};

export default function EngineeringChip({ label, onClick }: EngineeringChipProps) {
  return <Chip label={label} tone="neutral" onClick={onClick} />;
}
