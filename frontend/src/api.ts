import type { AssistantResult, StreamEvent } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "";

interface StreamChatInput {
  message: string;
  conversationId: string | null;
  employeeId: string | null;
  onEvent: (event: StreamEvent) => void;
}

function parseEvent(block: string): StreamEvent | null {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }

  if (!dataLines.length) return null;
  return {
    event: eventName as StreamEvent["event"],
    data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
  };
}

export async function streamChat({
  message,
  conversationId,
  employeeId,
  onEvent,
}: StreamChatInput): Promise<AssistantResult> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      employee_id: employeeId,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${response.status}`);
  }
  if (!response.body) throw new Error("Streaming is not supported by this browser.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed: AssistantResult | null = null;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const parsed = parseEvent(block);
      if (!parsed) continue;
      onEvent(parsed);
      if (parsed.event === "complete") completed = parsed.data as unknown as AssistantResult;
      if (parsed.event === "error") {
        throw new Error(String(parsed.data.message ?? "Assistant execution failed."));
      }
    }
    if (done) break;
  }

  if (!completed) throw new Error("The assistant stream ended before returning an answer.");
  return completed;
}

