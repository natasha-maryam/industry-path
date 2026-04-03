export const ST_TYPE_OPTIONS = [
  "BOOL",
  "INT",
  "DINT",
  "REAL",
  "LREAL",
  "TIME",
  "TIMER",
  "TON",
  "TOF",
  "TP",
  "STRING",
] as const;

export type BulkEditAction = "rename" | "type" | "value";

export const BULK_EDIT_ACTIONS: Array<{ value: BulkEditAction; label: string }> = [
  { value: "rename", label: "Rename globally" },
  { value: "type", label: "Change declaration type" },
  { value: "value", label: "Set numeric constant" },
];

export type TransformationResult = {
  content: string;
  changed: boolean;
  changedLines: number[];
  changeCount: number;
  error?: string;
};

export type NumericTarget = {
  name: string;
  rawValue: string;
  expression: string;
};

const IDENTIFIER_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;
const DECLARATION_LINE_PATTERN = /^(\s*)([A-Za-z_][A-Za-z0-9_,\s]*)(\s*:\s*)([^;:=]+?)(\s*(?::=[^;]+)?;.*)$/;
const DECLARATION_WITH_INITIALIZER_PATTERN = /(\b[A-Za-z_][A-Za-z0-9_]*\b\s*:\s*[^;:=]+?\s*:=\s*)([^;]+)(?=;)/g;

export function normalizeLogicPath(path: string): string {
  return path.replace(/^\/+/, "").replace(/\\/g, "/").trim();
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function isValidIdentifier(value: string): boolean {
  return IDENTIFIER_PATTERN.test(value.trim());
}

function uniqueSortedLines(lines: number[]): number[] {
  return [...new Set(lines)].sort((left, right) => left - right);
}

function replaceWholeIdentifier(content: string, from: string, to: string): TransformationResult {
  if (!isValidIdentifier(from)) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Enter a valid existing identifier." };
  }
  if (!isValidIdentifier(to)) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Enter a valid replacement identifier." };
  }
  if (from === to) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "The replacement identifier must be different." };
  }

  const pattern = new RegExp(`(?<![A-Za-z0-9_])${escapeRegExp(from)}(?![A-Za-z0-9_])`, "g");
  const changedLines: number[] = [];
  let changeCount = 0;
  content.split(/\r?\n/).forEach((line, index) => {
    const matches = [...line.matchAll(pattern)];
    if (matches.length > 0) {
      changedLines.push(index + 1);
      changeCount += matches.length;
    }
  });
  const nextContent = content.replace(pattern, to);
  return {
    content: nextContent,
    changed: nextContent !== content,
    changedLines: uniqueSortedLines(changedLines),
    changeCount,
  };
}

function formatLiteralReplacement(expression: string, nextValue: string): string | null {
  const trimmedExpression = expression.trim();
  const trimmedValue = nextValue.trim();
  if (!trimmedValue) {
    return null;
  }

  if (/^-?\d+(?:\.\d+)?$/.test(trimmedExpression)) {
    return trimmedValue;
  }

  const timeLiteralMatch = trimmedExpression.match(/^([A-Za-z]+#)?(-?\d+(?:\.\d+)?)([a-zA-Z]+)$/);
  if (timeLiteralMatch) {
    return `${timeLiteralMatch[1] || ""}${trimmedValue}${timeLiteralMatch[3]}`;
  }

  return null;
}

function collectDeclarationIdentifiers(content: string): Array<{ name: string; type: string }> {
  return content
    .split(/\r?\n/)
    .flatMap((line) => {
      const match = line.match(DECLARATION_LINE_PATTERN);
      if (!match) {
        return [];
      }

      const names = match[2]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .filter((item) => isValidIdentifier(item));
      const typeName = match[4].trim().toUpperCase();
      return names.map((name) => ({ name, type: typeName }));
    });
}

export function extractIdentifierOptions(content: string): string[] {
  const declarationNames = collectDeclarationIdentifiers(content).map((item) => item.name);
  const assignmentNames = [...content.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b\s*:=/g)].map((match) => match[1]);
  return [...new Set([...declarationNames, ...assignmentNames])].sort((left, right) => left.localeCompare(right));
}

export function extractTypeOptions(content: string): string[] {
  const discovered = collectDeclarationIdentifiers(content).map((item) => item.type);
  return [...new Set([...ST_TYPE_OPTIONS, ...discovered])];
}

export function extractNumericTargets(content: string): NumericTarget[] {
  const targets = new Map<string, NumericTarget>();

  for (const match of content.matchAll(DECLARATION_WITH_INITIALIZER_PATTERN)) {
    const declarationPrefix = match[1] || "";
    const declarationMatch = declarationPrefix.match(/\b([A-Za-z_][A-Za-z0-9_]*)\b\s*:\s*[^;:=]+\s*:=\s*$/);
    const name = declarationMatch?.[1];
    const expression = (match[2] || "").trim();
    const rawValue = formatLiteralReplacement(expression, expression.match(/-?\d+(?:\.\d+)?/)?.[0] || "");

    if (name && rawValue) {
      targets.set(name, { name, rawValue: rawValue.match(/-?\d+(?:\.\d+)?/)?.[0] || rawValue, expression });
    }
  }

  for (const match of content.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\b\s*:=\s*([^,;\)\r\n]+)/g)) {
    const name = match[1] || "";
    const expression = (match[2] || "").trim();
    const rawValue = formatLiteralReplacement(expression, expression.match(/-?\d+(?:\.\d+)?/)?.[0] || "");

    if (name && rawValue) {
      targets.set(name, { name, rawValue: rawValue.match(/-?\d+(?:\.\d+)?/)?.[0] || rawValue, expression });
    }
  }

  return [...targets.values()].sort((left, right) => left.name.localeCompare(right.name));
}

export function renameIdentifierInLogic(content: string, oldName: string, newName: string): TransformationResult {
  return replaceWholeIdentifier(content, oldName.trim(), newName.trim());
}

export function updateDeclarationTypeInLogic(content: string, targetName: string, nextType: string): TransformationResult {
  const normalizedTarget = targetName.trim();
  const normalizedType = nextType.trim().toUpperCase();

  if (!isValidIdentifier(normalizedTarget)) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Select a valid tag to update." };
  }
  if (!normalizedType) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Select a valid type." };
  }

  let didChange = false;
  const changedLines: number[] = [];
  let changeCount = 0;
  const nextContent = content
    .split(/\r?\n/)
    .map((line, index) => {
      const match = line.match(DECLARATION_LINE_PATTERN);
      if (!match) {
        return line;
      }

      const names = match[2]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      if (!names.includes(normalizedTarget)) {
        return line;
      }

      const rebuilt = `${match[1]}${match[2]}${match[3]}${normalizedType}${match[5]}`;
      if (rebuilt !== line) {
        didChange = true;
        changedLines.push(index + 1);
        changeCount += 1;
      }
      return rebuilt;
    })
    .join("\n");

  return {
    content: nextContent,
    changed: didChange,
    changedLines: uniqueSortedLines(changedLines),
    changeCount,
    error: didChange ? undefined : "No declaration for the selected tag was found in the active file.",
  };
}

export function updateNumericTargetInLogic(content: string, targetName: string, nextValue: string): TransformationResult {
  const normalizedTarget = targetName.trim();
  const trimmedValue = nextValue.trim();

  if (!isValidIdentifier(normalizedTarget)) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Select a valid constant target." };
  }
  if (!/^[-+]?\d+(?:\.\d+)?$/.test(trimmedValue)) {
    return { content, changed: false, changedLines: [], changeCount: 0, error: "Enter a valid numeric value." };
  }

  let didChange = false;
  const changedLines: number[] = [];
  let changeCount = 0;
  const contentLines = content.split(/\r?\n/);
  contentLines.forEach((line, index) => {
    const declarationPattern = new RegExp(`\\b${escapeRegExp(normalizedTarget)}\\b\\s*:\\s*[^;:=]+?\\s*:=\\s*([^;]+)`);
    const assignmentPattern = new RegExp(`\\b${escapeRegExp(normalizedTarget)}\\b\\s*:=\\s*([^,;\\)\\r\\n]+)`);
    const declarationMatch = line.match(declarationPattern);
    const assignmentMatch = line.match(assignmentPattern);
    const declarationReplacement = declarationMatch ? formatLiteralReplacement(declarationMatch[1], trimmedValue) : null;
    const assignmentReplacement = assignmentMatch ? formatLiteralReplacement(assignmentMatch[1], trimmedValue) : null;
    const localChanges = Number(Boolean(declarationReplacement && declarationReplacement !== declarationMatch?.[1].trim())) + Number(Boolean(assignmentReplacement && assignmentReplacement !== assignmentMatch?.[1].trim()));
    if (localChanges > 0) {
      changedLines.push(index + 1);
      changeCount += localChanges;
    }
  });
  const declarationPattern = new RegExp(`(\\b${escapeRegExp(normalizedTarget)}\\b\\s*:\\s*[^;:=]+?\\s*:=\\s*)([^;]+)(?=;)`, "g");
  const assignmentPattern = new RegExp(`(\\b${escapeRegExp(normalizedTarget)}\\b\\s*:=\\s*)([^,;\\)\\r\\n]+)`, "g");

  const withDeclarations = content.replace(declarationPattern, (fullMatch, prefix: string, expression: string) => {
    const replacement = formatLiteralReplacement(expression, trimmedValue);
    if (!replacement || replacement === expression.trim()) {
      return fullMatch;
    }
    didChange = true;
    return `${prefix}${replacement}`;
  });

  const nextContent = withDeclarations.replace(assignmentPattern, (fullMatch, prefix: string, expression: string) => {
    const replacement = formatLiteralReplacement(expression, trimmedValue);
    if (!replacement || replacement === expression.trim()) {
      return fullMatch;
    }
    didChange = true;
    return `${prefix}${replacement}`;
  });

  return {
    content: nextContent,
    changed: didChange,
    changedLines: uniqueSortedLines(changedLines),
    changeCount,
    error: didChange ? undefined : "No numeric assignment or initializer for that target was found in the active file.",
  };
}

export function applyBulkEditToLogic(
  content: string,
  payload: { target: string; action: BulkEditAction; value: string }
): TransformationResult {
  if (payload.action === "rename") {
    return renameIdentifierInLogic(content, payload.target, payload.value);
  }
  if (payload.action === "type") {
    return updateDeclarationTypeInLogic(content, payload.target, payload.value);
  }
  return updateNumericTargetInLogic(content, payload.target, payload.value);
}