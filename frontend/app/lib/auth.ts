export type Role = {
  name: string;
  description: string;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: Role[];
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Project = {
  id: number;
  name: string;
  description: string | null;
  system_type: string;
  target_users: string;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

export type SourceDocument = {
  id: number;
  project_id: number;
  title: string;
  document_type: string;
  source_kind: "uri" | "file";
  source_uri: string | null;
  version: string | null;
  original_file_name: string | null;
  stored_file_name: string | null;
  content_type: string | null;
  file_size_bytes: number | null;
  storage_path: string | null;
  created_at: string;
  updated_at: string;
};

export type TestQuestion = {
  id: number;
  project_id: number;
  question_text: string;
  question_type: string;
  expected_source: string | null;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

export type EvaluationRun = {
  id: number;
  project_id: number;
  name: string;
  system_version: string | null;
  notes: string | null;
  status: "pending" | "running" | "completed" | "failed";
  last_error: string | null;
  processed_question_count: number;
  created_by_user_id: number;
  created_at: string;
};

export type RetrievedChunk = {
  id: number;
  evaluation_run_id: number;
  test_question_id: number;
  source_document_id: number;
  rank: number;
  chunk_text: string;
  section_reference: string | null;
  relevance_label: "high" | "medium" | "low" | "irrelevant" | null;
  retrieval_time_ms: number | null;
  created_at: string;
};

export type GeneratedAnswer = {
  id: number;
  evaluation_run_id: number;
  test_question_id: number;
  answer_text: string;
  model_name: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  generation_time_ms: number | null;
  estimated_cost: string | null;
  created_at: string;
};

export type RagExecutionResult = {
  run_id: number;
  status: "completed" | "failed";
  model_name: string;
  processed_questions: number;
  retrieved_chunks_created: number;
  generated_answers_created: number;
  message: string;
};

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const TOKEN_STORAGE_KEY = "clear-rag-token";

export async function authRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail ?? "Request failed");
  }

  return data as T;
}

export async function uploadRequest<T>(
  path: string,
  formData: FormData,
  token: string,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail ?? "Upload failed");
  }

  return data as T;
}
