import UserAvatar from "../icons/UserAvatar";

export type PlantGenieMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
};

type MessageBubbleProps = {
  message: PlantGenieMessage;
  isThinking?: boolean;
};

export default function MessageBubble({ message, isThinking = false }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div className={`plant-genie-message-row ${isAssistant ? "is-assistant" : "is-user"}`}>
      <div className={`plant-genie-message-avatar ${isAssistant ? "is-assistant" : "is-user"}`} aria-hidden="true">
        {isAssistant ? <img className="plant-genie-message-avatar-image" src="/industrypath.jpeg" alt="" /> : <UserAvatar size={34} />}
      </div>

      <div className={`plant-genie-message-bubble-wrap ${isAssistant ? "is-assistant" : "is-user"}`}>
        <article className={`plant-genie-message-bubble ${isAssistant ? "aiBubble is-assistant" : "userBubble is-user"}`}>
          {isThinking ? (
            <div className="plant-genie-thinking" aria-label="Plant Genie is thinking">
              <span />
              <span />
              <span />
            </div>
          ) : (
            <div className="plant-genie-message-content">
              <p>{message.content}</p>
            </div>
          )}
        </article>
      </div>
    </div>
  );
}