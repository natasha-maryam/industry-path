import { describe, expect, it } from "vitest";
import { parseInlineTagIntelligence, parseStructuredTextIntelligence } from "./controlLogicIntelligence";
import { clearLogicTagIntelligenceSourceCache, getLogicTagIntelligenceSource } from "./logicTagIntelligenceSource";

describe("logicTagIntelligenceSource", () => {
  it("reuses cached analysis until content changes", () => {
    clearLogicTagIntelligenceSourceCache();
    const content = `VAR\n  PumpStart : BOOL;\nEND_VAR\n\nPumpStart := TRUE;`;

    const first = getLogicTagIntelligenceSource(content);
    const second = getLogicTagIntelligenceSource(content);
    const third = getLogicTagIntelligenceSource(`${content}\nPumpStart := FALSE;`);

    expect(second).toBe(first);
    expect(third).not.toBe(first);
  });

  it("exposes shared selectors for declarations and usages", () => {
    clearLogicTagIntelligenceSourceCache();
    const content = `VAR\n  PumpStart : BOOL;\nEND_VAR\n\nPumpStart := TRUE;\nIF pumpstart THEN\nEND_IF`;

    const source = getLogicTagIntelligenceSource(content);
    const tag = source.getTagByIdentifier("pumpstart");

    expect(tag?.tagName).toBe("PumpStart");
    expect(source.getDeclaration("PumpStart")).toEqual({
      line: 2,
      column: 3,
      snippet: "PumpStart : BOOL;",
      role: "definition",
    });
    expect(source.getAllUsages("PumpStart")).toHaveLength(2);
    expect(source.getReadWriteReferences("PumpStart")).toEqual({
      write: [{ line: 5, column: 1, snippet: "PumpStart := TRUE;", role: "write" }],
      read: [{ line: 6, column: 4, snippet: "IF pumpstart THEN", role: "read" }],
    });
    expect(source.getAllLineReferences("PumpStart")).toEqual([
      { line: 2, roles: ["definition"], primaryRole: "definition" },
      { line: 5, roles: ["write"], primaryRole: "write" },
      { line: 6, roles: ["read"], primaryRole: "read" },
    ]);
  });
});

describe("controlLogicIntelligence", () => {
  it("merges identifier casing and exposes inline tag intelligence sections", () => {
    const content = `VAR
  PumpStart : BOOL;
  FlowRate : REAL;
END_VAR

PumpStart := FlowRate > 1.0;
IF pumpstart THEN
  FlowRate := FlowRate + 1.0;
END_IF`;

    const parsed = parseStructuredTextIntelligence(content);
    const pumpStart = parsed.byName.PumpStart;

    expect(pumpStart).toBeDefined();
    expect(parsed.byName.pumpstart).toBe(pumpStart);
    expect(pumpStart.casingVariants).toEqual(["pumpstart", "PumpStart"]);
    expect(pumpStart.declarationLine).toBe(2);
    expect(pumpStart.writeCount).toBe(1);
    expect(pumpStart.readCount).toBe(1);
    expect(pumpStart.lineReferences).toEqual([2, 6, 7]);

    const inline = parseInlineTagIntelligence(content);
    const inlinePumpStart = inline.byName.pumpstart;

    expect(inlinePumpStart.tagName).toBe("PumpStart");
    expect(inlinePumpStart.dataType).toBe("BOOL");
    expect(inlinePumpStart.totalUsageCount).toBe(2);
    expect(inlinePumpStart.declarationLocation.line).toBe(2);
    expect(inlinePumpStart.usageContexts.written).toHaveLength(1);
    expect(inlinePumpStart.usageContexts.read).toHaveLength(1);
    expect(inlinePumpStart.allLineReferences).toEqual([
      { line: 2, roles: ["definition"], primaryRole: "definition" },
      { line: 6, roles: ["write"], primaryRole: "write" },
      { line: 7, roles: ["read"], primaryRole: "read" },
    ]);
  });

  it("tracks read and write references on the same line", () => {
    const content = `VAR
  FlowRate : REAL;
END_VAR

FlowRate := FlowRate + 1.0;`;

    const inline = parseInlineTagIntelligence(content);
    const flowRate = inline.byName.FlowRate;

    expect(flowRate.counts.writes).toBe(1);
    expect(flowRate.counts.reads).toBe(1);
    expect(flowRate.allLineReferences).toEqual([
      { line: 2, roles: ["definition"], primaryRole: "definition" },
      { line: 5, roles: ["write", "read"], primaryRole: "write" },
    ]);
  });
});