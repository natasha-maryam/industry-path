export type StructuredTextValidationIssueType =
  | "undefined_tag"
  | "unused_variable"
  | "broken_reference"
  | "duplicate_tag"
  | "inconsistent_naming";

export type StructuredTextValidationIssue = {
  id: string;
  type: StructuredTextValidationIssueType;
  name: string;
  line: number;
  column: number;
  snippet: string;
};

type DeclarationRecord = {
  name: string;
  canonicalName: string;
  line: number;
  column: number;
  snippet: string;
};

type ReferenceRecord = {
  name: string;
  canonicalName: string;
  line: number;
  column: number;
  snippet: string;
};

type ValidationParseResult = {
  declarations: DeclarationRecord[];
  references: ReferenceRecord[];
};

export const VALIDATION_ISSUE_LABELS: Record<StructuredTextValidationIssueType, string> = {
  undefined_tag: "Undefined Tag",
  unused_variable: "Unused Variable",
  broken_reference: "Broken Reference",
  duplicate_tag: "Duplicate Tag",
  inconsistent_naming: "Inconsistent Naming",
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
  return line.trim().slice(0, 140) || "(empty line)";
}

function parseStructuredTextSymbols(content: string): ValidationParseResult {
  const sanitized = stripCommentsAndStringsPreserveLines(content);
  const originalLines = content.split(/\r?\n/);
  const sanitizedLines = sanitized.split(/\r?\n/);
  const declarations: DeclarationRecord[] = [];
  const references: ReferenceRecord[] = [];
  let inVarBlock = false;

  for (let index = 0; index < sanitizedLines.length; index += 1) {
    const sanitizedLine = sanitizedLines[index] || "";
    const originalLine = originalLines[index] || "";
    const trimmedUpper = sanitizedLine.trim().toUpperCase();
    const lineNumber = index + 1;

    if (/^VAR(?:_[A-Z]+)?\b/.test(trimmedUpper)) {
      inVarBlock = true;
      continue;
    }

    if (/^END_VAR\b/.test(trimmedUpper)) {
      inVarBlock = false;
      continue;
    }

    if (inVarBlock) {
      const declarationMatch = sanitizedLine.match(DECLARATION_LINE_PATTERN);
      if (!declarationMatch) {
        continue;
      }

      const declaredNames = declarationMatch[2]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

      for (const name of declaredNames) {
        const column = Math.max(1, originalLine.indexOf(name) + 1);
        declarations.push({
          name,
          canonicalName: canonicalizeName(name),
          line: lineNumber,
          column,
          snippet: buildSnippet(originalLine),
        });
      }

      const initializerIndex = sanitizedLine.indexOf(":=");
      if (initializerIndex >= 0) {
        const initializerSegment = sanitizedLine.slice(initializerIndex + 2);
        for (const match of initializerSegment.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) {
          const name = match[1];
          const upperName = name.toUpperCase();
          if (RESERVED_WORDS.has(upperName)) {
            continue;
          }
          references.push({
            name,
            canonicalName: canonicalizeName(name),
            line: lineNumber,
            column: initializerIndex + (match.index ?? 0) + 3,
            snippet: buildSnippet(originalLine),
          });
        }
      }
      continue;
    }

    for (const match of sanitizedLine.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) {
      const name = match[1];
      const upperName = name.toUpperCase();
      if (RESERVED_WORDS.has(upperName)) {
        continue;
      }
      references.push({
        name,
        canonicalName: canonicalizeName(name),
        line: lineNumber,
        column: (match.index ?? 0) + 1,
        snippet: buildSnippet(originalLine),
      });
    }
  }

  return { declarations, references };
}

function issueId(type: StructuredTextValidationIssueType, name: string, line: number, column: number): string {
  return `${type}:${name}:${line}:${column}`;
}

function toIssue(type: StructuredTextValidationIssueType, record: { name: string; line: number; column: number; snippet: string }): StructuredTextValidationIssue {
  return {
    id: issueId(type, record.name, record.line, record.column),
    type,
    name: record.name,
    line: record.line,
    column: record.column,
    snippet: record.snippet,
  };
}

function classifyUndeclaredReference(name: string): StructuredTextValidationIssueType {
  return /^[A-Z0-9_]+$/.test(name) || /_/.test(name) ? "undefined_tag" : "broken_reference";
}

export function validateStructuredTextIssues(content: string): {
  issues: StructuredTextValidationIssue[];
  stats: { declarations: number; references: number };
} {
  if (!content.trim()) {
    return { issues: [], stats: { declarations: 0, references: 0 } };
  }

  const parsed = parseStructuredTextSymbols(content);
  const issues: StructuredTextValidationIssue[] = [];
  const declarationsByExact = new Map<string, DeclarationRecord[]>();
  const declarationsByCanonical = new Map<string, DeclarationRecord[]>();
  const referencesByExact = new Map<string, ReferenceRecord[]>();

  for (const declaration of parsed.declarations) {
    const exactBucket = declarationsByExact.get(declaration.name) ?? [];
    exactBucket.push(declaration);
    declarationsByExact.set(declaration.name, exactBucket);

    const canonicalBucket = declarationsByCanonical.get(declaration.canonicalName) ?? [];
    canonicalBucket.push(declaration);
    declarationsByCanonical.set(declaration.canonicalName, canonicalBucket);
  }

  for (const reference of parsed.references) {
    const exactBucket = referencesByExact.get(reference.name) ?? [];
    exactBucket.push(reference);
    referencesByExact.set(reference.name, exactBucket);
  }

  for (const declarations of declarationsByExact.values()) {
    if (declarations.length > 1) {
      for (const declaration of declarations) {
        issues.push(toIssue("duplicate_tag", declaration));
      }
    }
  }

  for (const declarations of declarationsByCanonical.values()) {
    const distinctNames = [...new Set(declarations.map((item) => item.name))];
    if (distinctNames.length > 1) {
      for (const declaration of declarations) {
        issues.push(toIssue("inconsistent_naming", declaration));
      }
    }
  }

  for (const declaration of parsed.declarations) {
    const references = referencesByExact.get(declaration.name) ?? [];
    if (references.length === 0) {
      issues.push(toIssue("unused_variable", declaration));
    }
  }

  const declaredNames = new Set(parsed.declarations.map((item) => item.name));
  for (const reference of parsed.references) {
    if (!declaredNames.has(reference.name)) {
      issues.push(toIssue(classifyUndeclaredReference(reference.name), reference));
    }
  }

  const dedupedIssues = [...new Map(issues.map((issue) => [issue.id, issue])).values()].sort((left, right) => {
    if (left.line !== right.line) {
      return left.line - right.line;
    }
    return left.column - right.column;
  });

  return {
    issues: dedupedIssues,
    stats: {
      declarations: parsed.declarations.length,
      references: parsed.references.length,
    },
  };
}