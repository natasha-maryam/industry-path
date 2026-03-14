import type { IOMappingIssue, IOMappingTableRow } from "../../services/api";

export type GroupedPreviewChannel = {
  tag: string;
  ioType: string;
  channel: number;
  slot: number;
  plcId: string;
  equipment?: string;
  deviceType?: string;
  hasWarning: boolean;
};

export type GroupedPreviewSlot = {
  slot: number;
  channels: GroupedPreviewChannel[];
};

export type GroupedPreviewPlc = {
  plcId: string;
  slots: GroupedPreviewSlot[];
};

export type MappingPreviewSummary = {
  totalSignals: number;
  ai: number;
  ao: number;
  di: number;
  doCount: number;
};

const ioTypeWeight: Record<string, number> = { AI: 1, AO: 2, DI: 3, DO: 4 };

export const buildIOMappingSummary = (rows: IOMappingTableRow[]): MappingPreviewSummary => {
  const summary: MappingPreviewSummary = { totalSignals: rows.length, ai: 0, ao: 0, di: 0, doCount: 0 };
  for (const row of rows) {
    const ioType = (row.io_type || "").toUpperCase();
    if (ioType === "AI") {
      summary.ai += 1;
    } else if (ioType === "AO") {
      summary.ao += 1;
    } else if (ioType === "DI") {
      summary.di += 1;
    } else if (ioType === "DO") {
      summary.doCount += 1;
    }
  }
  return summary;
};

export const groupMappingsByPlcAndSlot = (
  rows: IOMappingTableRow[],
  issues: IOMappingIssue[] = []
): GroupedPreviewPlc[] => {
  const warningTags = new Set(
    issues
      .filter((item) => item.severity === "warning" && item.tag)
      .map((item) => String(item.tag).toUpperCase())
  );

  const plcMap = new Map<string, Map<number, GroupedPreviewChannel[]>>();

  for (const row of rows) {
    const plcId = row.plc_id || "PLC1";
    const slot = Number(row.slot);
    const channelEntry: GroupedPreviewChannel = {
      tag: row.tag,
      ioType: row.io_type,
      channel: Number(row.channel),
      slot,
      plcId,
      equipment: row.equipment_id,
      deviceType: row.device_type,
      hasWarning: warningTags.has(String(row.tag).toUpperCase()),
    };

    if (!plcMap.has(plcId)) {
      plcMap.set(plcId, new Map<number, GroupedPreviewChannel[]>());
    }
    const slotMap = plcMap.get(plcId)!;
    if (!slotMap.has(slot)) {
      slotMap.set(slot, []);
    }
    slotMap.get(slot)!.push(channelEntry);
  }

  return [...plcMap.entries()]
    .map(([plcId, slotMap]) => ({
      plcId,
      slots: [...slotMap.entries()]
        .sort((left, right) => left[0] - right[0])
        .map(([slot, channels]) => ({
          slot,
          channels: channels.sort((left, right) => {
            if (left.channel !== right.channel) {
              return left.channel - right.channel;
            }
            const leftWeight = ioTypeWeight[(left.ioType || "").toUpperCase()] ?? 99;
            const rightWeight = ioTypeWeight[(right.ioType || "").toUpperCase()] ?? 99;
            if (leftWeight !== rightWeight) {
              return leftWeight - rightWeight;
            }
            return left.tag.localeCompare(right.tag);
          }),
        })),
    }))
    .sort((left, right) => left.plcId.localeCompare(right.plcId));
};
