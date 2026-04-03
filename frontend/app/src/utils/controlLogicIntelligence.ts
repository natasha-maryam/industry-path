export type StructuredTextIdentifierOccurrence = {
  line: number;
  column: number;
  snippet: string;
  role: "declaration" | "write" | "read";
};

export type StructuredTextIdentifierInfo = {
  name: string;
  canonicalName: string;
  category: "input" | "output" | "internal" | "timer" | "identifier";
  declaredType: string | null;
  declarationScope: string | null;
  declarationLine: number | null;
  declarationSnippet: string | null;
  firstSeenLine: number | null;
  isDeclared: boolean;
  occurrenceCount: number;
  usageCount: number;
  readCount: number;
  writeCount: number;
  declarationCount: number;
  lineReferences: number[];
  casingVariants: string[];
  occurrences: StructuredTextIdentifierOccurrence[];
  readOccurrences: StructuredTextIdentifierOccurrence[];
  writeOccurrences: StructuredTextIdentifierOccurrence[];
};

export type StructuredTextIntelligenceResult = {
  byName: Record<string, StructuredTextIdentifierInfo>;
  identifiers: StructuredTextIdentifierInfo[];
};

const RESERVED_WORDS = new Set([
  "AND",
  "ARRAY",
  "AT",
  "BOOL",
  "BY",
  "CASE",
  "CONST",
  "DINT",
  "DO",
  "ELSE",
  "ELSIF",
  "END_CASE",
  "END_FOR",
  "END_FUNCTION",
  "END_FUNCTION_BLOCK",
  "END_IF",
  "END_PROGRAM",
  "END_REPEAT",
  "END_STRUCT",
  "END_TYPE",
  "END_VAR",
  "END_WHILE",
  "EXIT",
  "FALSE",
  "FOR",
  "FUNCTION",
  "FUNCTION_BLOCK",
  "IF",
  "INT",
  "LREAL",
  "MOD",
  "NOT",
  "OF",
  "OR",
  "PROGRAM",
  "REAL",
  "REPEAT",
  "RETURN",
  "STRING",
  "STRUCT",
  "THEN",
  "TIME",
  "TO",
  "TON",
  "TOF",
  "TP",
  "TRUE",
  "TYPE",
  "UNTIL",
  "VAR",
  "VAR_GLOBAL",
  "VAR_INPUT",
  "VAR_IN_OUT",
  "VAR_OUTPUT",
  "VAR_TEMP",
  "WHILE",
  "XOR",
]);

const TIMER_TYPES = new Set(["TIME", "TIMER", "TON", "TOF", "TP"]);
const DECLARATION_LINE_PATTERN = /^(\s*)([A-Za-z_][A-Za-z0-9_,\s]*)(\s*:\s*)([^;:=]+)(\s*(?::=[^;]+)?;?.*)$/;

function canonicalizeName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function stripCommentsAndStringsPreserveLines(content: string): string {
  let output = "";
  let index = 0;
  let inBlockComment = false;
  let inLineComment = false;
  let inString = false;

  while (index < content.length) {
    const current = content[index];
    const next = content[index + 1] || "";

    if (inBlockComment) {
      if (current === "*" && next === ")") {
        output += "  ";
        inBlockComment = false;
        index += 2;
        continue;
      }
      output += current === "\n" ? "\n" : " ";
      index += 1;
      continue;
    }

    if (inLineComment) {
      if (current === "\n") {
        output += "\n";
        inLineComment = false;
      } else {
        output += " ";
      }
      index += 1;
      continue;
    }

    if (inString) {
      output += current === "\n" ? "\n" : " ";
      if (current === "'") {
        inString = false;
      }
      index += 1;
      continue;
    }

    if (current === "(" && next === "*") {
      output += "  ";
      inBlockComment = true;
      index += 2;
      continue;
    }

    if (current === "/" && next === "/") {
      output += "  ";
      inLineComment = true;
      index += 2;
      continue;
    }

    if (current === "'") {
      output += " ";
      inString = true;
      index += 1;
      continue;
    }

    output += current;
    index += 1;
  }

  return output;
}

function buildSnippet(line: string): string {
  return line.trim().slice(0, 160) || "(empty line)";
}

function uniqueSortedNumbers(values: number[]): number[] {
  return [...new Set(values)].sort((left, right) => left - right);
}

function inferCategory(scope: string | null, declaredType: string | null): StructuredTextIdentifierInfo["category"] {
  if (declaredType && TIMER_TYPES.has(declaredType.toUpperCase())) {
    return "timer";
  }
  if (scope === "VAR_INPUT") {
    return "input";
  }
  if (scope === "VAR_OUTPUT") {
    return "output";
  }
  if (scope) {
    return "internal";
  }
  return "identifier";
}

export function parseStructuredTextIntelligence(content: string): StructuredTextIntelligenceResult {
  if (!content.trim()) {
    return { byName: {}, identifiers: [] };
  }

  const sanitized = stripCommentsAndStringsPreserveLines(content);
  const originalLines = content.split(/\r?\n/);
  const sanitizedLines = sanitized.split(/\r?\n/);
  const byName = new Map<string, StructuredTextIdentifierInfo>();
  let currentVarScope: string | null = null;

  const ensureRecord = (name: string): StructuredTextIdentifierInfo => {
    const existing = byName.get(name);
    if (existing) {
      return existing;
    }
    const next: StructuredTextIdentifierInfo = {
      name,
      canonicalName: canonicalizeName(name),
      category: "identifier",
      declaredType: null,
      declarationScope: null,
      declarationLine: null,
      declarationSnippet: null,
      firstSeenLine: null,
      isDeclared: false,
      occurrenceCount: 0,
      usageCount: 0,
      readCount: 0,
      writeCount: 0,
      declarationCount: 0,
      lineReferences: [],
      casingVariants: [name],
      occurrences: [],
      readOccurrences: [],
      writeOccurrences: [],
    };
    byName.set(name, next);
    return next;
  };

  for (let index = 0; index < sanitizedLines.length; index += 1) {
    const sanitizedLine = sanitizedLines[index] || "";
    const originalLine = originalLines[index] || "";
    const trimmedUpper = sanitizedLine.trim().toUpperCase();
    const lineNumber = index + 1;

    if (/^VAR(?:_[A-Z]+)?\b/.test(trimmedUpper)) {
      currentVarScope = trimmedUpper.match(/^VAR(?:_[A-Z]+)?/)?.[0] || "VAR";
      continue;
    }

    if (/^END_VAR\b/.test(trimmedUpper)) {
      currentVarScope = null;
      continue;
    }

    if (currentVarScope) {
      const declarationMatch = sanitizedLine.match(DECLARATION_LINE_PATTERN);
      if (declarationMatch) {
        const declaredNames = declarationMatch[2]
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
        const declaredType = declarationMatch[4].trim().toUpperCase();

        for (const name of declaredNames) {
          const record = ensureRecord(name);
          record.isDeclared = true;
          record.declaredType = record.declaredType || declaredType;
          record.declarationScope = record.declarationScope || currentVarScope;
          record.declarationLine = record.declarationLine ?? lineNumber;
          record.declarationSnippet = record.declarationSnippet ?? buildSnippet(originalLine);
          record.firstSeenLine = record.firstSeenLine ?? lineNumber;
          record.declarationCount += 1;
          record.occurrenceCount += 1;
          record.lineReferences.push(lineNumber);
          record.category = inferCategory(record.declarationScope, record.declaredType);
          if (!record.casingVariants.includes(name)) {
            record.casingVariants.push(name);
          }
          record.occurrences.push({
            line: lineNumber,
            column: Math.max(1, originalLine.indexOf(name) + 1),
            snippet: buildSnippet(originalLine),
            role: "declaration",
          });
        }

        const initializerIndex = sanitizedLine.indexOf(":=");
        if (initializerIndex >= 0) {
          const initializerSegment = sanitizedLine.slice(initializerIndex + 2);
          for (const match of initializerSegment.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) {
            const name = match[1];
            if (RESERVED_WORDS.has(name.toUpperCase())) {
              continue;
            }
            const record = ensureRecord(name);
            record.firstSeenLine = record.firstSeenLine ?? lineNumber;
            record.usageCount += 1;
            record.readCount += 1;
            record.occurrenceCount += 1;
            record.lineReferences.push(lineNumber);
            if (!record.casingVariants.includes(name)) {
              record.casingVariants.push(name);
            }
            const occurrence = {
              line: lineNumber,
              column: initializerIndex + (match.index ?? 0) + 3,
              snippet: buildSnippet(originalLine),
              role: "read" as const,
            };
            record.occurrences.push(occurrence);
            record.readOccurrences.push(occurrence);
          }
        }
        continue;
      }
    }

    const writeMatch = sanitizedLine.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:=/);
    const writeIdentifier = writeMatch?.[1] || null;

    for (const match of sanitizedLine.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) {
      const name = match[1];
      if (RESERVED_WORDS.has(name.toUpperCase())) {
        continue;
      }
      const record = ensureRecord(name);
      record.firstSeenLine = record.firstSeenLine ?? lineNumber;
      record.occurrenceCount += 1;
      record.lineReferences.push(lineNumber);
      if (!record.casingVariants.includes(name)) {
        record.casingVariants.push(name);
      }
      const occurrence = {
        line: lineNumber,
        column: (match.index ?? 0) + 1,
        snippet: buildSnippet(originalLine),
        role: (writeIdentifier === name && (match.index ?? 0) === sanitizedLine.indexOf(name) ? "write" : "read") as "write" | "read",
      };
      if (occurrence.role === "write") {
        record.usageCount += 1;
        record.writeCount += 1;
        record.writeOccurrences.push(occurrence);
      } else {
        record.usageCount += 1;
        record.readCount += 1;
        record.readOccurrences.push(occurrence);
      }
      record.occurrences.push(occurrence);
    }
  }

  const identifiers = [...byName.values()]
    .map((item) => ({
      ...item,
      category: inferCategory(item.declarationScope, item.declaredType),
      lineReferences: uniqueSortedNumbers(item.lineReferences),
      casingVariants: [...item.casingVariants].sort((left, right) => left.localeCompare(right)),
      occurrences: [...item.occurrences].sort((left, right) => (left.line === right.line ? left.column - right.column : left.line - right.line)),
      readOccurrences: [...item.readOccurrences].sort((left, right) => (left.line === right.line ? left.column - right.column : left.line - right.line)),
      writeOccurrences: [...item.writeOccurrences].sort((left, right) => (left.line === right.line ? left.column - right.column : left.line - right.line)),
    }))
    .sort((left, right) => left.name.localeCompare(right.name));

  return {
    byName: Object.fromEntries(identifiers.map((item) => [item.name, item])),
    identifiers,
  };
}