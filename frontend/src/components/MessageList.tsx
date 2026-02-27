import React from "react";
import type { ChatMessage } from "../types";

export interface MessageListProps {
  messages: ChatMessage[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((m, idx) => {
        const isUser = m.role === "user";
        return (
          <div
            key={idx}
            className={"flex " + (isUser ? "justify-end" : "justify-start")}
          >
            <div
              className={
                "max-w-[85%] rounded-xl px-4 py-2.5 " +
                (isUser ? "bg-cyan-600/80" : "bg-slate-700")
              }
            >
              <div className="text-xs opacity-75 mb-1">
                {isUser ? "我" : "Agent"}
              </div>
              <div className="msg-content text-sm whitespace-pre-wrap break-words">
                {m.content}
              </div>
              {!isUser &&
                m.tool_calls &&
                Array.isArray(m.tool_calls) &&
                m.tool_calls.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-600">
                    <div className="text-xs text-cyan-400 mb-2">
                      调用的工具 ({m.tool_calls.length})
                    </div>
                    {m.tool_calls.map((tc, i) => (
                      <div
                        key={i}
                        className="text-xs rounded bg-slate-800/80 p-2 mb-2"
                      >
                        <div className="font-medium text-cyan-300 mb-1">
                          {i + 1}. {tc.tool || "tool"}
                        </div>
                        {tc.input &&
                          Object.keys(tc.input || {}).length > 0 && (
                            <div className="text-slate-400 mb-1">
                              入参:{" "}
                              {JSON.stringify(tc.input).slice(0, 500)}
                            </div>
                          )}
                        {tc.output != null &&
                          String(tc.output || "") !== "" && (
                            <div className="text-slate-300 whitespace-pre-wrap break-words">
                              结果:{" "}
                              {String(tc.output).length > 500
                                ? String(tc.output).slice(0, 500) + "…"
                                : String(tc.output)}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MessageList;

