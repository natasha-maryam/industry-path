export type InlineRemovedBlock = {
  anchorLineNumber: number;
  lines: string[];
};

export type InlineChangeSet = {
  changedLineNumbers: number[];
  removedBlocks: InlineRemovedBlock[];
};

type DiffChunk = {
  type: "equal" | "remove" | "add";
  lines: string[];
  startLineNumber: number;
};

function splitLines(value: string): string[] {
  return value.length > 0 ? value.split(/\r?\n/) : [];
}

function buildMiddleDiff(originalLines: string[], modifiedLines: string[], baseOriginalLine: number, baseModifiedLine: number): DiffChunk[] {
  const rows = originalLines.length;
  const columns = modifiedLines.length;
  const dp = Array.from({ length: rows + 1 }, () => new Array<number>(columns + 1).fill(0));

  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = columns - 1; column >= 0; column -= 1) {
      dp[row][column] = originalLines[row] === modifiedLines[column]
        ? dp[row + 1][column + 1] + 1
        : Math.max(dp[row + 1][column], dp[row][column + 1]);
    }
  }

  const chunks: DiffChunk[] = [];
  let row = 0;
  let column = 0;
  let originalLine = baseOriginalLine;
  let modifiedLine = baseModifiedLine;

  const pushChunk = (type: DiffChunk["type"], line: string, startLineNumber: number): void => {
    const previous = chunks[chunks.length - 1];
    if (previous && previous.type === type) {
      previous.lines.push(line);
      return;
    }
    chunks.push({ type, lines: [line], startLineNumber });
  };

  while (row < rows && column < columns) {
    if (originalLines[row] === modifiedLines[column]) {
      pushChunk("equal", originalLines[row], modifiedLine);
      row += 1;
      column += 1;
      originalLine += 1;
      modifiedLine += 1;
      continue;
    }

    if (dp[row + 1][column] >= dp[row][column + 1]) {
      pushChunk("remove", originalLines[row], originalLine);
      row += 1;
      originalLine += 1;
      continue;
    }

    pushChunk("add", modifiedLines[column], modifiedLine);
    column += 1;
    modifiedLine += 1;
  }

  while (row < rows) {
    pushChunk("remove", originalLines[row], originalLine);
    row += 1;
    originalLine += 1;
  }

  while (column < columns) {
    pushChunk("add", modifiedLines[column], modifiedLine);
    column += 1;
    modifiedLine += 1;
  }

  return chunks;
}

export function computeInlineChangeSet(originalContent: string, modifiedContent: string): InlineChangeSet {
  if (originalContent === modifiedContent) {
    return { changedLineNumbers: [], removedBlocks: [] };
  }

  const originalLines = splitLines(originalContent);
  const modifiedLines = splitLines(modifiedContent);

  let prefix = 0;
  while (
    prefix < originalLines.length &&
    prefix < modifiedLines.length &&
    originalLines[prefix] === modifiedLines[prefix]
  ) {
    prefix += 1;
  }

  let originalSuffix = originalLines.length - 1;
  let modifiedSuffix = modifiedLines.length - 1;
  while (
    originalSuffix >= prefix &&
    modifiedSuffix >= prefix &&
    originalLines[originalSuffix] === modifiedLines[modifiedSuffix]
  ) {
    originalSuffix -= 1;
    modifiedSuffix -= 1;
  }

  const changedLineNumbers = new Set<number>();
  const removedBlocks: InlineRemovedBlock[] = [];

  const middleOriginal = originalLines.slice(prefix, originalSuffix + 1);
  const middleModified = modifiedLines.slice(prefix, modifiedSuffix + 1);
  const chunks = buildMiddleDiff(middleOriginal, middleModified, prefix + 1, prefix + 1);

  for (let index = 0; index < chunks.length; index += 1) {
    const chunk = chunks[index];
    if (chunk.type === "add") {
      for (let offset = 0; offset < chunk.lines.length; offset += 1) {
        changedLineNumbers.add(chunk.startLineNumber + offset);
      }
      continue;
    }
    if (chunk.type !== "remove") {
      continue;
    }

    const nextChunk = chunks[index + 1];
    const previousChunk = chunks[index - 1];
    const anchorLineNumber = nextChunk?.type === "add"
      ? nextChunk.startLineNumber - 1
      : previousChunk?.type === "equal"
        ? previousChunk.startLineNumber + previousChunk.lines.length - 1
        : Math.max(0, chunk.startLineNumber - 1);

    removedBlocks.push({
      anchorLineNumber,
      lines: chunk.lines,
    });
  }

  return {
    changedLineNumbers: [...changedLineNumbers].sort((left, right) => left - right),
    removedBlocks,
  };
}
