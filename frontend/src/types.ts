export interface Citation {
  policy_id: string;
  section_number: string;
  section_title: string;
  source_path: string;
  excerpt: string;
}

export interface AssistantResult {
  conversation_id: string;
  answer: string;
  citations: Citation[];
  assumptions: string[];
  escalation_required: boolean;
  escalation_reason: string | null;
  agents_used: string[];
  route: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  result?: AssistantResult;
}

export interface StreamEvent {
  event: "start" | "progress" | "complete" | "error";
  data: Record<string, unknown>;
}

