"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, removeToken } from "@/lib/auth";
import { chatStream, listSessions, getSessionMessages, deleteSession } from "@/lib/api";
import { useTypewriter } from "@/hooks/useTypewriter";
import ChatMessageList from "@/components/ChatMessageList";
import ChatInput from "@/components/ChatInput";
import type { ChatSession, ChatMessage } from "@/types";

/** Lightweight step indicator for tool / sub-agent activity */
interface AgentStep { name: string; status: "running" | "done"; }

/** Pending commit: waiting for typewriter to finish before committing to messages */
interface PendingCommit { text: string; newSessionId: string | undefined; }

export default function ChatPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pendingCommitRef = useRef<PendingCommit | null>(null);

  const { displayed: streamingText, pushText, reset: resetTypewriter, flush: flushTypewriter, isTyping } = useTypewriter(3);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    loadSessions();
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText, agentSteps]);

  // ── Commit pending message once typewriter finishes ──
  const commitPending = useCallback(() => {
    const pending = pendingCommitRef.current;
    if (!pending) return;
    pendingCommitRef.current = null;
    resetTypewriter();
    if (pending.text) {
      setMessages((prev) => [...prev, {
        id: "tmp-a-" + Date.now(),
        role: "assistant" as const,
        content: pending.text,
        created_at: new Date().toISOString(),
      }]);
    }
    if (pending.newSessionId && pending.newSessionId !== activeSessionId) {
      setActiveSessionId(pending.newSessionId);
    }
    loadSessions();
  }, [activeSessionId, resetTypewriter]);

  useEffect(() => {
    const pending = pendingCommitRef.current;
    if (!pending) return;
    // When the displayed text has caught up to the full text, commit
    if (streamingText === pending.text) {
      commitPending();
    }
  }, [streamingText, commitPending]);

  const loadSessions = async () => {
    try { const s = await listSessions(); setSessions(s); } catch {}
  };

  const loadMessages = async (sid: string) => {
    setActiveSessionId(sid);
    setAgentSteps([]);
    pendingCommitRef.current = null;
    resetTypewriter();
    try { const m = await getSessionMessages(sid); setMessages(m); } catch {}
  };

  const handleNewChat = () => {
    setActiveSessionId(undefined);
    setMessages([]);
    pendingCommitRef.current = null;
    resetTypewriter();
    setAgentSteps([]);
  };

  const handleDeleteSession = async (sid: string) => {
    await deleteSession(sid);
    if (activeSessionId === sid) handleNewChat();
    loadSessions();
  };

  const handleSend = async (text: string) => {
    if (sending) return;
    setSending(true);
    resetTypewriter();
    pendingCommitRef.current = null;
    setAgentSteps([]);
    const userMsg: ChatMessage = { id: "tmp-" + Date.now(), role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);

    let fullText = "";
    let newSessionId = activeSessionId;
    try {
      for await (const ev of chatStream(text, activeSessionId)) {
        if (ev.type === "text" && ev.content) {
          setAgentSteps([]);
          fullText += ev.content;
          pushText(fullText);
        } else if (ev.type === "text_reset") {
          fullText = "";
          resetTypewriter();
        } else if (ev.type === "tool_call" && ev.content) {
          try {
            const tc = JSON.parse(ev.content);
            setAgentSteps((prev) => [...prev, { name: tc.name, status: "running" }]);
          } catch {}
        } else if (ev.type === "tool_result" && ev.content) {
          try {
            const tr = JSON.parse(ev.content);
            setAgentSteps((prev) =>
              prev.map((s) => s.name === tr.name && s.status === "running" ? { ...s, status: "done" } : s)
            );
          } catch {}
        } else if (ev.type === "done") {
          newSessionId = ev.session_id || newSessionId;
        }
      }
    } catch {
      fullText = fullText || "Error: failed to get response.";
      pushText(fullText);
    } finally {
      setAgentSteps([]);
      setSending(false);

      if (fullText) {
        // Ensure the typewriter target is set (covers error path)
        pushText(fullText);
        // Schedule commit — the useEffect above will fire when
        // streamingText catches up to fullText
        pendingCommitRef.current = { text: fullText, newSessionId };
      } else {
        // No response text at all — just clean up
        resetTypewriter();
        if (newSessionId && newSessionId !== activeSessionId) {
          setActiveSessionId(newSessionId);
        }
        loadSessions();
      }
    }
  };

  const handleLogout = () => { removeToken(); router.push("/login"); };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/40">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <div className={`${sidebarCollapsed ? "w-0 overflow-hidden" : "w-72"} bg-gray-950 text-white flex flex-col shadow-2xl transition-all duration-300 flex-shrink-0`}>
        {/* Logo & New Chat */}
        <div className="px-4 py-4 border-b border-white/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-sm tracking-tight">Logistics AI</p>
              <p className="text-[10px] text-gray-500 font-medium">Intelligent Shipping Agent</p>
            </div>
          </div>
          <button onClick={handleNewChat}
            className="w-full py-2.5 border border-white/10 rounded-xl hover:bg-white/5 hover:border-white/20
                       text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2
                       active:scale-[0.98]">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-2 dark-scrollbar">
          {sessions.length === 0 && (
            <div className="text-center mt-12 px-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-3">
                <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                </svg>
              </div>
              <p className="text-xs text-gray-600">No conversations yet</p>
              <p className="text-[10px] text-gray-700 mt-1">Start a new chat to begin</p>
            </div>
          )}
          {sessions.map((s) => (
            <div key={s.id} onClick={() => loadMessages(s.id)}
              className={"group mx-2 px-3 py-2.5 rounded-xl cursor-pointer flex items-center gap-2.5 transition-all duration-150 mb-0.5 " +
                (activeSessionId === s.id ? "sidebar-active" : "text-gray-400 hover:bg-white/5 hover:text-gray-200")}>
              <svg className="w-4 h-4 flex-shrink-0 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>
              <span className="text-[13px] truncate flex-1">{s.title}</span>
              <button onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.id); }}
                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all p-1 rounded-lg hover:bg-red-500/10">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Bottom actions */}
        <div className="p-3 border-t border-white/5 space-y-0.5">
          <button onClick={() => router.push("/profile")}
            className="w-full px-3 py-2.5 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-all flex items-center gap-2.5">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </button>
          <button onClick={handleLogout}
            className="w-full px-3 py-2.5 text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all flex items-center gap-2.5">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
            Sign Out
          </button>
        </div>
      </div>

      {/* ── Main chat area ────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="h-14 flex items-center px-4 md:px-6 border-b border-gray-100/80 bg-white/50 backdrop-blur-xl flex-shrink-0">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors mr-3"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold text-gray-800 truncate">
              {activeSessionId
                ? sessions.find(s => s.id === activeSessionId)?.title || "Chat"
                : "New Conversation"}
            </h1>
          </div>
          {sending && (
            <div className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full">
              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Thinking…
            </div>
          )}
        </div>

        <ChatMessageList messages={messages} streaming={streamingText} agentSteps={agentSteps} onSuggestionClick={handleSend} />
        <div ref={bottomRef} />
        <ChatInput onSend={handleSend} disabled={sending} />
      </div>
    </div>
  );
}
