import { describe, expect, it } from "vitest";

import { computeInlineChangeSet } from "./logicInlineChanges";

describe("computeInlineChangeSet", () => {
  it("marks inserted and modified lines while preserving removed blocks", () => {
    const result = computeInlineChangeSet(
      [
        "PROGRAM Demo",
        "VAR",
        "    PumpStart : BOOL;",
        "END_VAR",
        "PumpStart := FALSE;",
      ].join("\n"),
      [
        "PROGRAM Demo",
        "VAR",
        "    PumpStart : BOOL;",
        "    PumpStop : BOOL;",
        "END_VAR",
        "PumpStart := TRUE;",
      ].join("\n"),
    );

    expect(result.changedLineNumbers).toEqual([4, 6]);
    expect(result.removedBlocks).toEqual([
      {
        anchorLineNumber: 5,
        lines: ["PumpStart := FALSE;"],
      },
    ]);
  });

  it("tracks deletions at the top of a file", () => {
    const result = computeInlineChangeSet(
      [
        "(* header *)",
        "PROGRAM Demo",
        "PumpStart := FALSE;",
      ].join("\n"),
      [
        "PROGRAM Demo",
        "PumpStart := FALSE;",
      ].join("\n"),
    );

    expect(result.changedLineNumbers).toEqual([]);
    expect(result.removedBlocks).toEqual([
      {
        anchorLineNumber: 0,
        lines: ["(* header *)"],
      },
    ]);
  });
});
