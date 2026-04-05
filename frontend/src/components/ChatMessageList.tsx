"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id?: string;
  role: "user" | "assistant" | "tool";
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResponse?: string;
}

interface AgentStep {
  name: string;
  status: "running" | "done";
}

interface Props {
  messages: Message[];
  streaming?: string;
  agentSteps?: AgentStep[];
  onSuggestionClick?: (text: string) => void;
}

/* ── Icon components ─────────────────────────────────── */

function BotIcon() {
  return (
    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-md shadow-blue-500/25 ring-2 ring-white">
      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-2.47 3.71a2.25 2.25 0 01-1.874 1.003H9.344a2.25 2.25 0 01-1.874-1.003L5 14.5m14 0h-2.25M5 14.5H7.25m5-7.5v7.5" />
      </svg>
    </div>
  );
}

function UserIcon() {
  return (
    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center flex-shrink-0 shadow-sm ring-2 ring-white">
      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
      </svg>
    </div>
  );
}

/* ── Friendly tool name mapping ─────────────────────── */

const TOOL_LABELS: Record<string, string> = {
  transfer_to_agent: "Routing to specialist",
  track_shipment: "Looking up shipment",
  get_order_fees: "Querying fees",
  create_order: "Creating order",
  query_orders: "Searching orders",
  delete_order: "Deleting order",
  estimate_shipping_cost: "Estimating cost",
  query_price: "Comparing prices",
  query_channels: "Loading channels",
  query_destinations: "Searching destinations",
};

function friendlyName(toolName: string): string {
  return TOOL_LABELS[toolName] || toolName;
}

/* ── Compact step indicators ────────────────────────── */

function AgentStepList({ steps }: { steps: AgentStep[] }) {
  if (steps.length === 0) return null;
  return (
    <div className="msg-appear flex gap-3 items-start">
      <BotIcon />
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <div key={i} className="tool-card flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200/60 text-xs text-gray-600">
            {step.status === "running" ? (
              <svg className="w-3.5 h-3.5 text-blue-500 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            )}
            <span>{friendlyName(step.name)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Thinking indicator ─────────────────────────────── */

function ThinkingIndicator() {
  return (
    <div className="msg-appear flex gap-3 items-start">
      <BotIcon />
      <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white border border-gray-100 shadow-sm">
        <div className="flex items-center gap-1">
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </div>
      </div>
    </div>
  );
}

/* ── Empty State ────────────────────────────────────── */

function EmptyState({ onSuggestionClick }: { onSuggestionClick?: (text: string) => void }) {
  const suggestions = [
    { icon: "📦", text: "Track my shipment T6W20260401002" },
    { icon: "💰", text: "Get a shipping quote from Shanghai to US, 2.5kg" },
    { icon: "📋", text: "Show me my recent orders" },
    { icon: "🚢", text: "What shipping channels are available?" },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/25 mb-6">
        <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-gray-800 mb-1">Logistics AI Assistant</h2>
      <p className="text-sm text-gray-400 mb-8 text-center max-w-md">
        Your intelligent shipping partner. Ask about shipments, pricing, tracking, and more.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {suggestions.map((s, i) => (
          <div
            key={i}
            onClick={() => onSuggestionClick?.(s.text)}
            className="group flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200/80
                       bg-white hover:bg-blue-50/50 hover:border-blue-200 cursor-pointer
                       transition-all duration-200 shadow-sm hover:shadow-md"
          >
            <span className="text-lg">{s.icon}</span>
            <span className="text-sm text-gray-600 group-hover:text-gray-800 transition-colors">{s.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main Component ─────────────────────────────────── */

export default function ChatMessageList({ messages, streaming, agentSteps, onSuggestionClick }: Props) {
  const hasActiveSteps = agentSteps && agentSteps.length > 0;
  const isWaiting = !streaming && !hasActiveSteps &&
    messages.length > 0 && messages[messages.length - 1].role === "user";

  // Filter out tool messages from history (they are transient UI state now)
  const visibleMessages = messages.filter((m) => m.role !== "tool");

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
      {visibleMessages.length === 0 && !streaming && <EmptyState onSuggestionClick={onSuggestionClick} />}

      <div className="max-w-3xl mx-auto space-y-4">
        {visibleMessages.map((msg, i) => {
          const isUser = msg.role === "user";
          return (
            <div key={msg.id || i} className={"msg-appear flex gap-3 " + (isUser ? "flex-row-reverse" : "items-start")}>
              {isUser ? <UserIcon /> : <BotIcon />}
              <div
                className={
                  "max-w-[80%] px-4 py-3 text-sm leading-relaxed " +
                  (isUser
                    ? "bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20 rounded-2xl rounded-tr-sm"
                    : "bg-white border border-gray-100/80 shadow-sm text-gray-800 rounded-2xl rounded-tl-sm")
                }
              >
                {isUser ? (
                  <span className="whitespace-pre-wrap">{msg.content}</span>
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    className="prose prose-sm max-w-none prose-headings:mb-2 prose-headings:mt-3
                               prose-p:mb-2 prose-li:my-0.5 prose-img:rounded-xl"
                    components={{
                      table: ({ children, ...props }) => (
                        <div className="overflow-x-auto -mx-1">
                          <table {...props}>{children}</table>
                        </div>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          );
        })}

        {/* Compact agent step indicators (tool calls / sub-agent routing) */}
        {hasActiveSteps && <AgentStepList steps={agentSteps!} />}

        {/* Streaming response */}
        {streaming && (
          <div className="msg-appear flex gap-3 items-start">
            <BotIcon />
            <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-tl-sm bg-white border border-gray-100/80 shadow-sm text-sm leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm max-w-none">{streaming}</ReactMarkdown>
              <span className="streaming-cursor" />
            </div>
          </div>
        )}

        {/* Thinking dots — shown after user message before any response */}
        {isWaiting && <ThinkingIndicator />}
      </div>
    </div>
  );
}
