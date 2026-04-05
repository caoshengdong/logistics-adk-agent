"use client";
import { useRef, useState } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const msg = text.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-gray-100/80 bg-white/60 backdrop-blur-2xl px-4 py-4 md:px-8">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 bg-white border border-gray-200/80 rounded-2xl shadow-lg shadow-gray-200/30 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all duration-300">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => { setText(e.target.value); autoResize(); }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about shipments, pricing, tracking…"
            disabled={disabled}
            rows={1}
            className="flex-1 px-4 py-3.5 resize-none bg-transparent
                       outline-none text-sm leading-relaxed
                       disabled:opacity-50 placeholder:text-gray-400"
          />
          <div className="pr-2 pb-2">
            <button
              type="submit"
              disabled={disabled || !text.trim()}
              className="h-9 w-9 flex items-center justify-center rounded-xl transition-all duration-200
                         disabled:opacity-30 disabled:cursor-not-allowed
                         bg-gradient-to-r from-blue-600 to-indigo-600 text-white
                         hover:from-blue-500 hover:to-indigo-500 hover:shadow-md hover:shadow-blue-500/25
                         active:scale-95"
            >
              {disabled ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                </svg>
              )}
            </button>
          </div>
        </div>
        <p className="text-[10px] text-gray-400 mt-2 text-center">
          <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 text-[9px] font-mono">Enter</kbd> to send
          <span className="mx-1.5">·</span>
          <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 text-[9px] font-mono">Shift+Enter</kbd> new line
        </p>
      </form>
    </div>
  );
}
