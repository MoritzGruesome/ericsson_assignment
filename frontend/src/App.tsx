import { FormEvent, useEffect, useRef, useState } from "react";
import { streamChat } from "./api";
import type { ChatMessage, Citation, ExecutionStep, StreamEvent } from "./types";

const EXAMPLES = [
  {
    label: "Policy lookup",
    text: "How many remote-working days are normally permitted during probation?",
  },
  {
    label: "Leave analysis",
    text: "I joined on 15 June and have taken four days off. How much annual leave is available to me today?",
    employeeId: "NS-1042",
  },
  {
    label: "Expense check",
    text: "A taxi home after a client dinner cost HKD 620 at 22:45. Is it reimbursable and who must approve it?",
  },
];

const AGENT_LABELS: Record<string, string> = {
  supervisor: "HR Supervisor",
  policy_rag_agent: "Policy RAG Agent",
  employee_case_analyst: "Case Analyst",
};

function Icon({ name }: { name: "leaf" | "send" | "book" | "person" | "shield" }) {
  const paths = {
    leaf: <path d="M19 3C12 3 6.5 6.7 5.2 12.2c-.6 2.7.5 5.1 2.7 6.3 2.2 1.1 4.9.6 6.6-1.3 2.9-3.1 3.3-8.8 4.5-14.2ZM5 21c2.1-5.3 5.8-9 11-12" />,
    send: <path d="m4 4 16 8-16 8 3-8-3-8Zm3 8h13" />,
    book: <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Zm16 0A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" />,
    person: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 9a7 7 0 0 0-14 0" />,
    shield: <path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Zm-3.5-10 2.2 2.2 4.8-5" />,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24">{paths[name]}</svg>;
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <details className="citation-card">
      <summary>
        <span className="citation-mark"><Icon name="book" /></span>
        <span>
          <strong>{citation.policy_id} §{citation.section_number}</strong>
          <small>{citation.section_title}</small>
        </span>
        <span className="chevron">⌄</span>
      </summary>
      <p>{citation.excerpt}</p>
      <code>{citation.source_path}</code>
    </details>
  );
}

function ExecutionHistory({ steps, live = false }: { steps: ExecutionStep[]; live?: boolean }) {
  const content = (
    <div className={`execution-steps${live ? " live" : ""}`}>
      {steps.map((step, index) => (
        <div className={`execution-step ${step.kind}`} key={`${step.kind}-${step.name}-${index}`}>
          <i />
          <span>{step.label}</span>
          {step.kind === "tool" && <code>{step.name}</code>}
        </div>
      ))}
    </div>
  );

  if (live) return content;
  return (
    <details className="execution-history">
      <summary>
        <span>Agent execution history</span>
        <small>{steps.length} {steps.length === 1 ? "step" : "steps"}</small>
        <span className="chevron">⌄</span>
      </summary>
      {content}
    </details>
  );
}

function formatAnswer(content: string) {
  return content.split("\n").map((line, index) => {
    if (line.startsWith("- ")) return <li key={index}>{line.slice(2)}</li>;
    if (!line.trim()) return <br key={index} />;
    return <p key={index}>{line.replace(/\*\*/g, "")}</p>;
  });
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ExecutionStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, progress]);

  const submit = async (event?: FormEvent, textOverride?: string, employeeOverride?: string) => {
    event?.preventDefault();
    const text = (textOverride ?? input).trim();
    if (!text || isLoading) return;

    const activeEmployee = employeeOverride ?? employeeId;
    if (employeeOverride) setEmployeeId(employeeOverride);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: text },
    ]);
    setInput("");
    setProgress([]);
    setError(null);
    setIsLoading(true);

    try {
      const result = await streamChat({
        message: text,
        conversationId,
        employeeId: activeEmployee || null,
        onEvent: (streamEvent: StreamEvent) => {
          if (streamEvent.event === "start") {
            setConversationId(String(streamEvent.data.conversation_id));
          }
          if (streamEvent.event === "progress") {
            const step = streamEvent.data as unknown as ExecutionStep;
            setProgress((current) => {
              const duplicate = current.some(
                (item) => item.kind === step.kind && item.name === step.name && item.label === step.label,
              );
              return duplicate ? current : [...current, step];
            });
          }
        },
      });
      setConversationId(result.conversation_id);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", content: result.answer, result },
      ]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
      setProgress([]);
    }
  };

  const reset = () => {
    setMessages([]);
    setConversationId(null);
    setProgress([]);
    setError(null);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><Icon name="leaf" /></span>
          <span><strong>PeopleGuide</strong><small>Northstar Systems</small></span>
        </div>

        <button className="new-chat" onClick={reset}>＋ New conversation</button>

        <div className="sidebar-section">
          <label htmlFor="employee">Demo employee</label>
          <select id="employee" value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}>
            <option value="">No employee selected</option>
            <option value="NS-1042">Mei Lin · NS-1042</option>
            <option value="NS-1077">Arjun Shah · NS-1077</option>
            <option value="NS-1115">Sofia Chan · NS-1115</option>
          </select>
          <p>Synthetic records only</p>
        </div>

        <div className="agent-key">
          <span>Specialist team</span>
          <div><i className="agent-dot supervisor" /> HR Supervisor</div>
          <div><i className="agent-dot policy" /> Policy RAG Agent</div>
          <div><i className="agent-dot case" /> Case Analyst</div>
        </div>

        <div className="privacy-note">
          <Icon name="shield" />
          <p><strong>Demo environment</strong><br />Do not enter real personal or medical information.</p>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="status-dot" /> Assistant online
          </div>
          <span className="environment">FICTIONAL POLICY DEMO</span>
        </header>

        <section className={`conversation ${messages.length ? "active" : "empty"}`}>
          {!messages.length && (
            <div className="welcome">
              <span className="welcome-icon"><Icon name="leaf" /></span>
              <p className="eyebrow">YOUR NORTHSTAR PEOPLE PARTNER</p>
              <h1>HR guidance,<br /><em>grounded in policy.</em></h1>
              <p className="intro">
                Ask about leave, benefits, expenses, or flexible work. Our specialist agents
                will find the relevant policy and apply it to your demo profile.
              </p>
              <div className="example-grid">
                {EXAMPLES.map((example) => (
                  <button
                    key={example.label}
                    onClick={() => void submit(undefined, example.text, example.employeeId)}
                  >
                    <span>{example.label}</span>
                    <p>{example.text}</p>
                    <b>↗</b>
                  </button>
                ))}
              </div>
            </div>
          )}

          {!!messages.length && (
            <div className="message-list">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="avatar">
                    {message.role === "user" ? <Icon name="person" /> : <Icon name="leaf" />}
                  </div>
                  <div className="message-body">
                    <div className="message-meta">
                      <strong>{message.role === "user" ? "You" : "PeopleGuide"}</strong>
                      {message.result && (
                        <span>{message.result.agents_used.map((agent) => AGENT_LABELS[agent] ?? agent).join(" · ")}</span>
                      )}
                    </div>
                    <div className="answer-content">{formatAnswer(message.content)}</div>
                    {message.result?.execution_history.length ? (
                      <ExecutionHistory steps={message.result.execution_history} />
                    ) : null}
                    {message.result?.assumptions.length ? (
                      <div className="assumptions"><strong>Assumptions</strong>{message.result.assumptions.join(" · ")}</div>
                    ) : null}
                    {message.result?.citations.length ? (
                      <div className="citations">
                        <span className="section-label">Policy sources</span>
                        {message.result.citations.map((citation) => (
                          <CitationCard key={`${citation.policy_id}-${citation.section_number}`} citation={citation} />
                        ))}
                      </div>
                    ) : null}
                  </div>
                </article>
              ))}

              {isLoading && (
                <article className="message assistant working">
                  <div className="avatar"><Icon name="leaf" /></div>
                  <div className="message-body">
                    <div className="message-meta"><strong>PeopleGuide</strong><span>Working with your specialist team</span></div>
                    {progress.length ? (
                      <ExecutionHistory steps={progress} live />
                    ) : (
                      <div className="progress-list"><div><i />Starting analysis</div></div>
                    )}
                  </div>
                </article>
              )}
              {error && <div className="error-banner"><strong>Couldn’t complete the request.</strong> {error}</div>}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <footer className="composer-wrap">
          <form className="composer" onSubmit={(event) => void submit(event)}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit();
                }
              }}
              placeholder="Ask a question about Northstar HR policies…"
              rows={1}
              disabled={isLoading}
              aria-label="Message PeopleGuide"
            />
            <button type="submit" disabled={!input.trim() || isLoading} aria-label="Send message">
              <Icon name="send" />
            </button>
          </form>
          <p>PeopleGuide provides policy guidance, not legal advice or employment decisions.</p>
        </footer>
      </main>
    </div>
  );
}

