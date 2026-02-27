import React from "react";

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  disabled?: boolean;
  placeholder?: string;
}

const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder,
}) => {
  return (
    <div className="border-t border-slate-700 p-4 shrink-0">
      <form className="flex gap-2" onSubmit={onSubmit}>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="flex-1 rounded-lg bg-slate-700 border border-slate-600 px-4 py-3 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={disabled}
          className="rounded-lg bg-cyan-600 hover:bg-cyan-500 px-5 py-3 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {disabled ? "发送中…" : "发送"}
        </button>
      </form>
    </div>
  );
};

export default MessageInput;

