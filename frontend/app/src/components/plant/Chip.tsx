import { memo, useMemo, type ReactElement } from "react";

type ChipTone = "relation" | "source" | "neutral";

type ChipProps = {
  label: string;
  tone?: ChipTone;
  onClick?: (value: string) => void;
  compact?: boolean;
};

type ChipListProps = {
  values: string[];
  tone?: ChipTone;
  limit?: number;
  emptyLabel?: string;
  onChipClick?: (value: string) => void;
  compact?: boolean;
};

const toneClasses: Record<ChipTone, string> = {
  relation: "bg-indigo-100 text-indigo-700 hover:bg-indigo-200",
  source: "bg-gray-100 text-gray-700 hover:bg-gray-200",
  neutral: "bg-slate-100 text-slate-700 hover:bg-slate-200",
};

export const Chip = memo(function Chip({ label, tone = "neutral", onClick, compact = false }: ChipProps): ReactElement {
  const interactive = typeof onClick === "function";
  const sizeClasses = compact
    ? "max-w-full px-1.5 py-0.5 text-[8px] leading-tight whitespace-normal break-words text-left"
    : "max-w-[150px] px-2 py-0.5 text-xs truncate";
  const className = `inline-flex items-center rounded font-medium ${sizeClasses} ${toneClasses[tone]} ${interactive ? "cursor-pointer" : ""}`;

  if (interactive) {
    return (
      <button type="button" className={className} onClick={(event) => {
        event.stopPropagation();
        onClick(label);
      }} title={label}>
        {label}
      </button>
    );
  }

  return (
    <span className={className} title={label}>
      {label}
    </span>
  );
});

export const ChipList = memo(function ChipList({
  values,
  tone = "neutral",
  limit = 3,
  emptyLabel = "—",
  onChipClick,
  compact = false,
}: ChipListProps): ReactElement {
  const normalizedValues = useMemo(() => values.filter((item) => item && item.trim().length > 0), [values]);

  const visibleValues = useMemo(() => normalizedValues.slice(0, limit), [normalizedValues, limit]);

  if (normalizedValues.length === 0) {
    return <span className={`${compact ? "text-[8px]" : "text-sm"} text-slate-400`}>{emptyLabel}</span>;
  }

  const overflowCount = Math.max(0, normalizedValues.length - visibleValues.length);
  const allValuesTitle = normalizedValues.join(", ");

  return (
    <div className={`${compact ? "flex max-w-full flex-wrap items-start gap-1" : "flex max-w-[220px] items-center gap-1 overflow-hidden"}`} title={allValuesTitle}>
      {visibleValues.map((value) => (
        <Chip key={value} label={value} tone={tone} onClick={onChipClick} compact={compact} />
      ))}
      {overflowCount > 0 ? <span className={`${compact ? "text-[8px]" : "text-xs"} text-slate-500`}>+{overflowCount}</span> : null}
    </div>
  );
});
