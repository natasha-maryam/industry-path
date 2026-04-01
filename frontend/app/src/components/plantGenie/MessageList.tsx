import { useEffect, useRef } from "react";

import MessageBubble, { type PlantGenieMessage } from "./MessageBubble";

type MessageListProps = {
  messages: PlantGenieMessage[];
  isThinking?: boolean;
};

export default function MessageList({ messages, isThinking = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isThinking, messages]);

  return (
    <div className="plant-genie-message-list" aria-live="polite">
      <div className="plant-genie-message-stack">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isThinking ? <MessageBubble message={{ id: "thinking", role: "assistant", content: "" }} isThinking /> : null}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}