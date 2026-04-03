import {
  parseInlineTagIntelligence,
  type InlineTagIntelligenceEntry,
  type InlineTagIntelligenceLineReference,
  type InlineTagIntelligenceReference,
  type InlineTagIntelligenceResult,
} from "./controlLogicIntelligence";

export type LogicTagIntelligenceResolvedReference = {
  tag: InlineTagIntelligenceEntry;
  reference: InlineTagIntelligenceReference;
};

export type LogicTagIntelligenceSource = {
  content: string;
  version: string;
  parsed: InlineTagIntelligenceResult;
  entries: InlineTagIntelligenceEntry[];
  getTagByIdentifier: (identifier: string | null | undefined) => InlineTagIntelligenceEntry | null;
  getDeclaration: (identifier: string | null | undefined) => InlineTagIntelligenceReference | null;
  getAllUsages: (identifier: string | null | undefined) => InlineTagIntelligenceReference[];
  getReadWriteReferences: (identifier: string | null | undefined) => {
    read: InlineTagIntelligenceReference[];
    write: InlineTagIntelligenceReference[];
  };
  getAllLineReferences: (identifier: string | null | undefined) => InlineTagIntelligenceLineReference[];
  getCombinedReferences: (identifier: string | null | undefined) => InlineTagIntelligenceReference[];
  getReferenceAtPosition: (
    identifier: string | null | undefined,
    line: number,
    column: number,
    matchedIdentifier?: string | null
  ) => InlineTagIntelligenceReference | null;
  resolveAtPosition: (identifier: string | null | undefined, line: number, column: number) => LogicTagIntelligenceResolvedReference | null;
};

const EMPTY_REFERENCES: InlineTagIntelligenceReference[] = [];
const EMPTY_LINE_REFERENCES: InlineTagIntelligenceLineReference[] = [];
const EMPTY_READ_WRITE = {
  read: EMPTY_REFERENCES,
  write: EMPTY_REFERENCES,
} as const;

const MAX_CACHE_SIZE = 12;

function createCacheKey(content: string): string {
  return content;
}

function clampCache(): void {
  while (SOURCE_CACHE.size > MAX_CACHE_SIZE) {
    const oldestKey = SOURCE_CACHE.keys().next().value;
    if (!oldestKey) {
      return;
    }
    SOURCE_CACHE.delete(oldestKey);
  }
}

function canonicalizeIdentifier(identifier: string): string {
  return identifier.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function sortReferences<T extends { line: number; column: number }>(references: T[]): T[] {
  return [...references].sort((left, right) => (left.line === right.line ? left.column - right.column : left.line - right.line));
}

function withinReference(reference: InlineTagIntelligenceReference, line: number, column: number, matchedIdentifier?: string | null): boolean {
  const referenceLength = Math.max(1, (matchedIdentifier?.length ?? 0) || reference.snippet.length || 1);
  return reference.line === line && column >= reference.column && column <= reference.column + referenceLength - 1;
}

function buildSource(content: string): LogicTagIntelligenceSource {
  const parsed = parseInlineTagIntelligence(content);
  const entryIndex = new Map<string, InlineTagIntelligenceEntry>();
  const declarationIndex = new Map<string, InlineTagIntelligenceReference | null>();
  const usageIndex = new Map<string, InlineTagIntelligenceReference[]>();
  const readWriteIndex = new Map<string, { read: InlineTagIntelligenceReference[]; write: InlineTagIntelligenceReference[] }>();
  const combinedReferenceIndex = new Map<string, InlineTagIntelligenceReference[]>();
  const lineReferenceIndex = new Map<string, InlineTagIntelligenceLineReference[]>();

  for (const entry of parsed.entries) {
    const keys = new Set([entry.tagName, entry.canonicalName, ...entry.casingVariants]);
    const declaration = entry.declarationLocation.reference;
    const usages = entry.usageContexts.all;
    const combinedReferences = declaration ? sortReferences([declaration, ...usages]) : usages;
    const readWrite = {
      read: entry.usageContexts.read,
      write: entry.usageContexts.written,
    };

    for (const key of keys) {
      entryIndex.set(key, entry);
      entryIndex.set(canonicalizeIdentifier(key), entry);
      declarationIndex.set(key, declaration);
      declarationIndex.set(canonicalizeIdentifier(key), declaration);
      usageIndex.set(key, usages);
      usageIndex.set(canonicalizeIdentifier(key), usages);
      readWriteIndex.set(key, readWrite);
      readWriteIndex.set(canonicalizeIdentifier(key), readWrite);
      combinedReferenceIndex.set(key, combinedReferences);
      combinedReferenceIndex.set(canonicalizeIdentifier(key), combinedReferences);
      lineReferenceIndex.set(key, entry.allLineReferences);
      lineReferenceIndex.set(canonicalizeIdentifier(key), entry.allLineReferences);
    }
  }

  const getTagByIdentifier = (identifier: string | null | undefined): InlineTagIntelligenceEntry | null => {
    if (!identifier) {
      return null;
    }
    return entryIndex.get(identifier) ?? entryIndex.get(canonicalizeIdentifier(identifier)) ?? null;
  };

  const getDeclaration = (identifier: string | null | undefined): InlineTagIntelligenceReference | null => {
    if (!identifier) {
      return null;
    }
    return declarationIndex.get(identifier) ?? declarationIndex.get(canonicalizeIdentifier(identifier)) ?? null;
  };

  const getAllUsages = (identifier: string | null | undefined): InlineTagIntelligenceReference[] => {
    if (!identifier) {
      return EMPTY_REFERENCES;
    }
    return usageIndex.get(identifier) ?? usageIndex.get(canonicalizeIdentifier(identifier)) ?? EMPTY_REFERENCES;
  };

  const getReadWriteReferences = (identifier: string | null | undefined): { read: InlineTagIntelligenceReference[]; write: InlineTagIntelligenceReference[] } => {
    if (!identifier) {
      return EMPTY_READ_WRITE;
    }
    return readWriteIndex.get(identifier) ?? readWriteIndex.get(canonicalizeIdentifier(identifier)) ?? EMPTY_READ_WRITE;
  };

  const getAllLineReferences = (identifier: string | null | undefined): InlineTagIntelligenceLineReference[] => {
    if (!identifier) {
      return EMPTY_LINE_REFERENCES;
    }
    return lineReferenceIndex.get(identifier) ?? lineReferenceIndex.get(canonicalizeIdentifier(identifier)) ?? EMPTY_LINE_REFERENCES;
  };

  const getCombinedReferences = (identifier: string | null | undefined): InlineTagIntelligenceReference[] => {
    if (!identifier) {
      return EMPTY_REFERENCES;
    }
    return combinedReferenceIndex.get(identifier) ?? combinedReferenceIndex.get(canonicalizeIdentifier(identifier)) ?? EMPTY_REFERENCES;
  };

  const getReferenceAtPosition = (
    identifier: string | null | undefined,
    line: number,
    column: number,
    matchedIdentifier?: string | null
  ): InlineTagIntelligenceReference | null => {
    const references = getCombinedReferences(identifier);
    return references.find((reference) => withinReference(reference, line, column, matchedIdentifier)) ?? references[0] ?? null;
  };

  const resolveAtPosition = (identifier: string | null | undefined, line: number, column: number): LogicTagIntelligenceResolvedReference | null => {
    const tag = getTagByIdentifier(identifier);
    if (!tag) {
      return null;
    }
    const reference = getReferenceAtPosition(identifier, line, column, identifier);
    if (!reference) {
      return null;
    }
    return { tag, reference };
  };

  return {
    content,
    version: `${content.length}:${parsed.entries.length}`,
    parsed,
    entries: parsed.entries,
    getTagByIdentifier,
    getDeclaration,
    getAllUsages,
    getReadWriteReferences,
    getAllLineReferences,
    getCombinedReferences,
    getReferenceAtPosition,
    resolveAtPosition,
  };
}

const SOURCE_CACHE = new Map<string, LogicTagIntelligenceSource>();

export function getLogicTagIntelligenceSource(content: string): LogicTagIntelligenceSource {
  const normalizedContent = content || "";
  const cacheKey = createCacheKey(normalizedContent);
  const cached = SOURCE_CACHE.get(cacheKey);
  if (cached) {
    SOURCE_CACHE.delete(cacheKey);
    SOURCE_CACHE.set(cacheKey, cached);
    return cached;
  }

  const source = buildSource(normalizedContent);
  SOURCE_CACHE.set(cacheKey, source);
  clampCache();
  return source;
}

export function clearLogicTagIntelligenceSourceCache(): void {
  SOURCE_CACHE.clear();
}