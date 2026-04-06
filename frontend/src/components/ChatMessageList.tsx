"use client";
import { useEffect, useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { downloadArtifact } from "@/lib/api";
import type { ArtifactInfo } from "@/types";

interface Message {
  id?: string;
  role: "user" | "assistant" | "tool";
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResponse?: string;
  artifacts?: ArtifactInfo[];
}

interface AgentStep {
  name: string;
  status: "running" | "done";
}

interface Props {
  messages: Message[];
  streaming?: string;
  agentSteps?: AgentStep[];
  sending?: boolean;
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
  generate_quotation_pdf: "Generating PDF quotation",
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

/* ── Artifact helpers ─────────────────────────────────── */

/**
 * Pre-process markdown content: wrap bare artifact filenames in markdown
 * link syntax so the custom `a` renderer always catches them — regardless
 * of whether the LLM output them as a link or plain text.
 */
function linkifyArtifacts(content: string, artifacts: ArtifactInfo[]): string {
  if (artifacts.length === 0) return content;
  let result = content;
  for (const art of artifacts) {
    // Already wrapped in a markdown link → skip
    if (result.includes(`[${art.filename}](`)) continue;
    // Replace bare filename with markdown link
    result = result.split(art.filename).join(`[${art.filename}](${art.filename})`);
  }
  return result;
}

/** Extract plain text from a React children prop (string, number, array, or element). */
function extractText(node: React.ReactNode): string {
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (node && typeof node === "object" && "props" in node) {
    return extractText((node as React.ReactElement).props.children);
  }
  return "";
}

/** Find a matching artifact by filename, href, or `artifact:ID` pattern. */
function findArtifact(allArtifacts: ArtifactInfo[], href?: string, children?: React.ReactNode): ArtifactInfo | undefined {
  if (allArtifacts.length === 0) return undefined;
  const childText = extractText(children);

  // 1. Match by href === filename
  // 2. Match by link text === filename
  // 3. Match by artifact:ID href pattern
  const artifactIdMatch = href?.match(/^artifact:(.+)$/);
  return allArtifacts.find(
    (a) =>
      a.filename === href ||
      a.filename === childText ||
      (artifactIdMatch && a.artifact_id === artifactIdMatch[1]),
  );
}

/* ── Artifact download card ──────────────────────────── */

function ArtifactCard({ artifact }: { artifact: ArtifactInfo }) {
  const sizeKB = artifact.size ? (artifact.size / 1024).toFixed(1) : "?";
  const isPdf = artifact.content_type === "application/pdf";

  return (
    <div className="mt-2 flex items-center gap-3 px-3 py-2.5 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/60 max-w-xs">
      <div className="w-9 h-9 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
        {isPdf ? (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z" />
            <text x="7" y="18" fontSize="6" fontWeight="bold" fill="currentColor">PDF</text>
          </svg>
        ) : (
          <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-800 truncate">{artifact.filename}</p>
        <p className="text-[10px] text-gray-500">{sizeKB} KB</p>
      </div>
      <button
        onClick={() => downloadArtifact(artifact.artifact_id, artifact.filename)}
        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm hover:shadow-md active:scale-95"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        Download
      </button>
    </div>
  );
}

/* ── Main Component ─────────────────────────────────── */

export default function ChatMessageList({ messages, streaming, agentSteps, sending, onSuggestionClick }: Props) {
  const hasActiveSteps = agentSteps && agentSteps.length > 0;
  const isWaiting = !!sending && !streaming && !hasActiveSteps &&
    messages.length > 0 && messages[messages.length - 1].role === "user";

  // Filter out tool messages from history (they are transient UI state now)
  const visibleMessages = messages.filter((m) => m.role !== "tool");

  // Collect ALL artifacts across every message so any message can reference
  // any artifact (e.g. when user asks agent to "re-send the PDF").
  const allArtifacts = useMemo(() => {
    const arts: ArtifactInfo[] = [];
    for (const m of messages) {
      if (m.artifacts) arts.push(...m.artifacts);
    }
    return arts;
  }, [messages]);

  // Auto-scroll: ref at the bottom of the scrollable container
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming, agentSteps]);

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
                  <>
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
                        a: ({ href, children }) => {
                          // Match against ALL session artifacts (not just this message's)
                          const matchedArt = findArtifact(allArtifacts, href, children);
                          if (matchedArt) {
                            return (
                              <button
                                type="button"
                                onClick={() => downloadArtifact(matchedArt.artifact_id, matchedArt.filename)}
                                className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800
                                           font-medium underline underline-offset-2 decoration-blue-300
                                           hover:decoration-blue-500 transition-colors cursor-pointer"
                              >
                                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                                </svg>
                                {children}
                              </button>
                            );
                          }
                          // Real URL → open in new tab
                          if (href && /^https?:\/\//.test(href)) {
                            return (
                              <a href={href} target="_blank" rel="noopener noreferrer">
                                {children}
                              </a>
                            );
                          }
                          // Unknown relative link → render as inert text
                          return <span className="font-medium text-blue-600">{children}</span>;
                        },
                      }}
                    >
                      {linkifyArtifacts(msg.content, allArtifacts)}
                    </ReactMarkdown>
                    {msg.artifacts && msg.artifacts.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {msg.artifacts.map((art) => (
                          <ArtifactCard key={art.artifact_id} artifact={art} />
                        ))}
                      </div>
                    )}
                  </>
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
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-sm max-w-none"
                components={{
                  a: ({ href, children, ...props }) => {
                    if (href && /^https?:\/\//.test(href)) {
                      return <a {...props} href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
                    }
                    return <span className="font-medium text-blue-600">{children}</span>;
                  },
                }}
              >{streaming}</ReactMarkdown>
              <span className="streaming-cursor" />
            </div>
          </div>
        )}

        {/* Thinking dots — shown after user message before any response */}
        {isWaiting && <ThinkingIndicator />}

        {/* Scroll anchor — must be inside the overflow-y-auto container */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
