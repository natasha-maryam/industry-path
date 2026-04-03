import { describe, expect, it } from "vitest";
import { buildLogicSnapshot, formatRelativeSavedTime, insertLogicSnapshot } from "./logicSnapshots";

describe("logicSnapshots", () => {
  it("deduplicates consecutive identical snapshots", () => {
    const snapshot = buildLogicSnapshot({
      files: [{ path: "main.st", content: "A := TRUE;" }],
      generatedLogic: "A := TRUE;",
      selectedFilePath: "main.st",
      source: "quick-edit",
      createdAt: "2026-04-03T12:00:00.000Z",
    });

    const next = insertLogicSnapshot([snapshot], snapshot);

    expect(next).toHaveLength(1);
    expect(next[0]).toBe(snapshot);
  });

  it("prepends newer distinct snapshots", () => {
    const older = buildLogicSnapshot({
      files: [{ path: "main.st", content: "A := TRUE;" }],
      generatedLogic: "A := TRUE;",
      selectedFilePath: "main.st",
      source: "quick-edit",
      createdAt: "2026-04-03T12:00:00.000Z",
    });
    const newer = buildLogicSnapshot({
      files: [{ path: "main.st", content: "A := FALSE;" }],
      generatedLogic: "A := FALSE;",
      selectedFilePath: "main.st",
      source: "restore",
      createdAt: "2026-04-03T12:01:00.000Z",
    });

    const next = insertLogicSnapshot([older], newer);

    expect(next).toHaveLength(2);
    expect(next[0].signature).toBe(newer.signature);
    expect(next[1].signature).toBe(older.signature);
  });

  it("formats short relative save times", () => {
    expect(formatRelativeSavedTime("2026-04-03T12:00:55.000Z", new Date("2026-04-03T12:01:00.000Z").getTime())).toBe("5 sec ago");
    expect(formatRelativeSavedTime("2026-04-03T11:59:00.000Z", new Date("2026-04-03T12:01:00.000Z").getTime())).toBe("2 min ago");
  });
});
