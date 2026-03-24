import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ShieldCheck } from "lucide-react";

type AuthPanelProps = {
  onTokenChange?: (token: string) => void;
};

const maskToken = (token: string): string => {
  const trimmed = token.trim();
  if (!trimmed) {
    return "No token";
  }
  if (trimmed.length <= 12) {
    return `${trimmed.slice(0, 4)}…${trimmed.slice(-2)}`;
  }
  return `${trimmed.slice(0, 8)}…${trimmed.slice(-6)}`;
};

export default function AuthPanel({ onTokenChange }: AuthPanelProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [tokenInput, setTokenInput] = useState<string>("");

  const tokenLabel = useMemo(() => maskToken(tokenInput), [tokenInput]);

  return (
    <section className="rounded border border-slate-300 bg-white p-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <ShieldCheck size={14} className="text-slate-600" />
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Production Auth</h4>
        </div>
        <button type="button" className="command-btn" onClick={() => setIsExpanded((value) => !value)}>
          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
      </div>

      <p className="mt-1 text-[11px] text-slate-600">Token: {tokenLabel}</p>

      {isExpanded ? (
        <div className="mt-2 space-y-2 rounded border border-slate-200 bg-slate-50 p-2">
          <input
            type="password"
            value={tokenInput}
            onChange={(event) => setTokenInput(event.target.value)}
            placeholder="Paste JWT bearer token"
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="command-btn"
              onClick={() => {
                onTokenChange?.(tokenInput.trim());
              }}
            >
              Apply Token
            </button>
            <button
              type="button"
              className="command-btn"
              onClick={() => {
                setTokenInput("");
                onTokenChange?.("");
              }}
            >
              Clear
            </button>
          </div>
          <p className="text-[10px] text-slate-500">Stored in local component state only.</p>
        </div>
      ) : null}
    </section>
  );
}
