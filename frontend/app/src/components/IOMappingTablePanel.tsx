import { useMemo, useState } from "react";
import { AlertTriangle, Search } from "lucide-react";
import type { IOMappingTableRow } from "../services/api";
import "../styles/io-mapping-table-panel.css";

const VALID_IO_TYPES = new Set(["AI", "AO", "DI", "DO"]);

export type IOMappingTablePanelProps = {
  rows: IOMappingTableRow[];
  loading?: boolean;
  failedMessage?: string | null;
  onRetry?: () => void;
  requiredPreviousStep?: string;
  pageSizeOptions?: number[];
  defaultPageSize?: number;
  maxChannel?: number;
};

type ValidationCode = "duplicate_tag" | "invalid_io_type" | "missing_signal" | "channel_overflow";

type RowWithValidation = IOMappingTableRow & {
  validations: ValidationCode[];
};

const VALIDATION_LABELS: Record<ValidationCode, string> = {
  duplicate_tag: "Duplicate Tag",
  invalid_io_type: "Invalid IO Type",
  missing_signal: "Missing Signal",
  channel_overflow: "Channel Overflow",
};

const normalizeToken = (value: string): string => value.toLowerCase().trim();

const safeText = (value: string | number): string => String(value ?? "").trim();

const statusClassForValidation = (code: ValidationCode): "warning" | "error" => {
  if (code === "duplicate_tag" || code === "channel_overflow") {
    return "error";
  }
  return "warning";
};

export default function IOMappingTablePanel({
  rows,
  loading = false,
  failedMessage = null,
  onRetry,
  requiredPreviousStep = "Logic Completion + Plant Graph",
  pageSizeOptions = [10, 20, 50],
  defaultPageSize = 10,
  maxChannel = 15,
}: IOMappingTablePanelProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [tagFilter, setTagFilter] = useState<string>("all");
  const [equipmentFilter, setEquipmentFilter] = useState<string>("all");
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);
  const [page, setPage] = useState<number>(1);

  const rowsWithValidation = useMemo<RowWithValidation[]>(() => {
    const tagCounts = new Map<string, number>();
    for (const row of rows) {
      const key = normalizeToken(row.tag);
      tagCounts.set(key, (tagCounts.get(key) ?? 0) + 1);
    }

    return rows.map((row) => {
      const validations: ValidationCode[] = [];
      const normalizedTag = normalizeToken(row.tag);
      const normalizedIoType = safeText(row.io_type).toUpperCase();
      const normalizedSignalType = normalizeToken(row.signal_type);

      if ((tagCounts.get(normalizedTag) ?? 0) > 1) {
        validations.push("duplicate_tag");
      }
      if (!VALID_IO_TYPES.has(normalizedIoType)) {
        validations.push("invalid_io_type");
      }
      if (!normalizedSignalType) {
        validations.push("missing_signal");
      }
      if (row.channel < 0 || row.channel > maxChannel) {
        validations.push("channel_overflow");
      }

      return {
        ...row,
        validations,
      };
    });
  }, [maxChannel, rows]);

  const tagOptions = useMemo<string[]>(() => {
    const options = rows.map((row) => row.tag).filter((value) => value.trim().length > 0);
    return [...new Set(options)].sort((left, right) => left.localeCompare(right));
  }, [rows]);

  const equipmentOptions = useMemo<string[]>(() => {
    const options = rows.map((row) => row.equipment_id).filter((value) => value.trim().length > 0);
    return [...new Set(options)].sort((left, right) => left.localeCompare(right));
  }, [rows]);

  const filteredRows = useMemo<RowWithValidation[]>(() => {
    const query = normalizeToken(searchQuery);

    return rowsWithValidation.filter((row) => {
      if (tagFilter !== "all" && row.tag !== tagFilter) {
        return false;
      }
      if (equipmentFilter !== "all" && row.equipment_id !== equipmentFilter) {
        return false;
      }

      if (!query) {
        return true;
      }

      const haystack = [
        row.tag,
        row.device_type,
        row.signal_type,
        row.io_type,
        row.plc_id,
        row.slot,
        row.channel,
        row.description,
        row.equipment_id,
      ]
        .map((value) => normalizeToken(String(value)))
        .join(" ");

      return haystack.includes(query);
    });
  }, [equipmentFilter, rowsWithValidation, searchQuery, tagFilter]);

  const totalPages = useMemo<number>(() => Math.max(1, Math.ceil(filteredRows.length / pageSize)), [filteredRows.length, pageSize]);

  const pageRows = useMemo<RowWithValidation[]>(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize, totalPages]);

  if (loading) {
    return <section className="io-mapping-table-panel io-mapping-state">Loading IO mappings...</section>;
  }

  if (failedMessage) {
    return (
      <section className="io-mapping-table-panel io-mapping-state error">
        <AlertTriangle size={15} />
        <span>{failedMessage}</span>
        <button className="io-mapping-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
          Retry
        </button>
      </section>
    );
  }

  if (rows.length === 0) {
    return <section className="io-mapping-table-panel io-mapping-state">No IO mappings available. Complete {requiredPreviousStep} first.</section>;
  }

  const warningCount = rowsWithValidation.reduce((count, row) => count + row.validations.length, 0);

  return (
    <section className="io-mapping-table-panel">
      {warningCount > 0 ? <div className="io-mapping-warning">Validation warnings found ({warningCount}). Review highlighted rows; workspace remains active.</div> : null}
      <header className="io-mapping-toolbar">
        <div className="io-mapping-search-wrap">
          <Search size={13} />
          <input
            value={searchQuery}
            onChange={(event) => {
              setSearchQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Search tags, equipment, PLC, description"
            type="search"
          />
        </div>

        <label>
          Tag
          <select
            value={tagFilter}
            onChange={(event) => {
              setTagFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="all">All</option>
            {tagOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label>
          Equipment
          <select
            value={equipmentFilter}
            onChange={(event) => {
              setEquipmentFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="all">All</option>
            {equipmentOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </header>

      <div className="io-mapping-table-wrap">
        <table className="io-mapping-table">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Device Type</th>
              <th>Signal Type</th>
              <th>IO Type</th>
              <th>PLC ID</th>
              <th>Slot</th>
              <th>Channel</th>
              <th>Description</th>
              <th>Equipment ID</th>
              <th>Validation</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, rowIndex) => (
              <tr key={`${row.tag}-${row.plc_id}-${row.slot}-${row.channel}-${rowIndex}`}>
                <td className="mono">{row.tag}</td>
                <td>{row.device_type}</td>
                <td>{row.signal_type || "—"}</td>
                <td className="mono">{row.io_type}</td>
                <td className="mono">{row.plc_id}</td>
                <td className="mono">{row.slot}</td>
                <td className="mono">{row.channel}</td>
                <td>{row.description || "—"}</td>
                <td className="mono">{row.equipment_id}</td>
                <td>
                  {row.validations.length > 0 ? (
                    <div className="io-mapping-badges">
                      {row.validations.map((validationCode) => (
                        <span key={`${row.tag}-${validationCode}`} className={`io-badge ${statusClassForValidation(validationCode)}`}>
                          {VALIDATION_LABELS[validationCode]}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="io-badge success">Valid</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="io-mapping-pagination">
        <div className="io-mapping-page-size">
          <label>
            Rows
            <select
              value={String(pageSize)}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
            >
              {pageSizeOptions.map((option) => (
                <option key={option} value={String(option)}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <span>
            Showing {filteredRows.length === 0 ? 0 : (Math.min(page, totalPages) - 1) * pageSize + 1}–
            {Math.min(Math.min(page, totalPages) * pageSize, filteredRows.length)} of {filteredRows.length}
          </span>
        </div>

        <div className="io-mapping-page-controls">
          <button
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            disabled={page <= 1}
            type="button"
          >
            Previous
          </button>
          <span>
            Page {Math.min(page, totalPages)} / {totalPages}
          </span>
          <button
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            disabled={page >= totalPages}
            type="button"
          >
            Next
          </button>
        </div>
      </footer>
    </section>
  );
}
