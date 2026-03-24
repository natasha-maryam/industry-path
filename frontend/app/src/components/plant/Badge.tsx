import { memo, type ReactElement } from "react";

type BadgeProps = {
  label: string;
  className: string;
  title?: string;
};

const Pill = memo(function Pill({ label, className, title }: BadgeProps): ReactElement {
  return (
    <span className={`inline-flex max-w-[120px] items-center truncate rounded px-2 py-0.5 text-xs font-medium ${className}`} title={title || label}>
      {label}
    </span>
  );
});

const resolveTypeClass = (typeValue: string): string => {
  const value = typeValue.toLowerCase().trim();
  if (value === "instrument") {
    return "bg-blue-100 text-blue-700";
  }
  if (value === "actuator") {
    return "bg-orange-100 text-orange-700";
  }
  if (value === "equipment") {
    return "bg-gray-200 text-gray-800";
  }
  if (value === "control") {
    return "bg-purple-100 text-purple-700";
  }
  return "bg-gray-100 text-gray-600";
};

type TypeBadgeProps = {
  type: string;
};

export const TypeBadge = memo(function TypeBadge({ type }: TypeBadgeProps): ReactElement {
  return <Pill label={type || "unknown"} className={resolveTypeClass(type || "")} />;
});

type StatusBadgeProps = {
  status: "Connected" | "Controlled" | "Actuated" | "Orphan";
};

export const StatusBadge = memo(function StatusBadge({ status }: StatusBadgeProps): ReactElement {
  const classByStatus: Record<StatusBadgeProps["status"], string> = {
    Connected: "bg-green-100 text-green-700",
    Controlled: "bg-blue-100 text-blue-700",
    Actuated: "bg-orange-100 text-orange-700",
    Orphan: "bg-red-100 text-red-700",
  };
  return <Pill label={status} className={classByStatus[status]} />;
});

type ConfidenceBadgeProps = {
  value: number;
};

export const ConfidenceBadge = memo(function ConfidenceBadge({ value }: ConfidenceBadgeProps): ReactElement {
  let className = "bg-red-100 text-red-700";
  if (value >= 0.9) {
    className = "bg-green-100 text-green-700";
  } else if (value >= 0.7) {
    className = "bg-yellow-100 text-yellow-700";
  }
  return <Pill label={value.toFixed(3)} className={className} title={`Confidence ${value.toFixed(3)}`} />;
});

type WarningBadgeProps = {
  warning: string;
};

export const WarningBadge = memo(function WarningBadge({ warning }: WarningBadgeProps): ReactElement {
  const normalized = (warning || "").toLowerCase();
  let className = "bg-yellow-100 text-yellow-700";
  if (normalized.includes("no upstream") || normalized.includes("no downstream")) {
    className = "bg-red-100 text-red-700";
  } else if (normalized.includes("inferred")) {
    className = "bg-gray-100 text-gray-700";
  }
  return <Pill label={warning} className={className} />;
});
