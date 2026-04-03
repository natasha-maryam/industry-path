import { ArrowUp } from "lucide-react";
import type { KeyboardEvent } from "react";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSend: (value: string) => void | Promise<void>;
  placeholder: string;
  tooltip?: string;
  disabled?: boolean;
  isThinking?: boolean;
  helperText?: string;
};

export default function ChatInput({
  value,
  onChange,
  onSend,
  placeholder,
  tooltip,
  disabled = false,
  isThinking = false,
  helperText,
}: ChatInputProps) {
  const canSend = value.trim().length > 0 && !disabled && !isThinking;

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>): void => {
    if (event.key !== "Enter") {
      return;
    }

    event.preventDefault();
    if (canSend) {
      void onSend(value);
    }
  };

  return (
    <div className="plant-genie-input-shell">
      <div className="plant-genie-input-row">
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          title={tooltip}
          className="plant-genie-input"
          disabled={disabled}
        />
        <button
          type="button"
          className="plant-genie-send-button"
          aria-label="Send message"
          disabled={!canSend}
          onClick={() => {
            if (canSend) {
              void onSend(value);
            }
          }}
        >
          <ArrowUp size={16} />
        </button>
      </div>
      {helperText ? <div className="plant-genie-input-helper">{helperText}</div> : null}
    </div>
  );
}