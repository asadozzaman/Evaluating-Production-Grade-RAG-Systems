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

export type DocumentIndexResult = {
  document_id: number;
  chunks_indexed: number;
  embedding_model: string;
  message: string;
};

export type TestQuestion = {
  id: number;
  project_id: number;
  question_text: string;
  question_type: string;
  expected_source: string | null;
  dataset_id: number | null;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

export type QuestionDataset = {
  id: number;
  project_id: number;
  dataset_name: string;
  dataset_version: string | null;
  imported_file_name: string | null;
  question_count: number;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

export type QuestionImportResult = {
  dataset: QuestionDataset;
  questions_imported: number;
  duplicate_questions: number;
  invalid_rows: number;
  errors: Array<{
    row_number: number;
    message: string;
  }>;
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
  dataset_id: number | null;
  batch_document_ids: string | null;
  auto_evaluate_enabled: boolean;
  batch_status: string | null;
  current_step: string | null;
  completed_steps: string | null;
  failed_step: string | null;
  batch_error_message: string | null;
  batch_started_at: string | null;
  batch_completed_at: string | null;
  retrieval_mode: "keyword" | "vector" | null;
  generator_model_name: string | null;
  embedding_model_name: string | null;
  judge_model_name: string | null;
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

export type EvaluationRecord = {
  id: number;
  evaluation_run_id: number;
  test_question_id: number;
  generated_answer_id: number;
  reviewer_user_id: number;
  evaluation_mode: "human" | "automated";
  judge_model_name: string | null;
  judge_reasoning: string | null;
  review_status: "pending_review" | "approved" | "needs_revision";
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  review_notes: string | null;
  score_change_reason: string | null;
  citation_quality_score: number;
  latency_cost_score: number;
  evidence_faithfulness_score: number;
  answer_relevance_score: number;
  retrieval_quality_score: number;
  overall_score: string;
  reviewer_notes: string | null;
  suggested_improvement: string | null;
  created_at: string;
  updated_at: string;
};

export type ReviewDashboardItem = {
  question_id: number;
  question_text: string;
  question_type: string;
  expected_source: string | null;
  answer_id: number;
  answer_text: string;
  model_name: string | null;
  evaluation_id: number | null;
  evaluation_mode: "human" | "automated" | null;
  review_status: "pending_review" | "approved" | "needs_revision";
  overall_score: string | null;
  citation_quality_score: number | null;
  latency_cost_score: number | null;
  evidence_faithfulness_score: number | null;
  answer_relevance_score: number | null;
  retrieval_quality_score: number | null;
  judge_model_name: string | null;
  judge_reasoning: string | null;
  reviewer_notes: string | null;
  suggested_improvement: string | null;
  review_notes: string | null;
  score_change_reason: string | null;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  retrieved_chunks: Array<{
    id: number;
    rank: number;
    source_document_id: number;
    section_reference: string | null;
    relevance_label: "high" | "medium" | "low" | "irrelevant" | null;
    chunk_text: string;
  }>;
};

export type RunReviewDashboard = {
  project_id: number;
  run_id: number;
  run_name: string;
  total_answers: number;
  pending_review_count: number;
  approved_count: number;
  needs_revision_count: number;
  review_completion_percent: string;
  ready_for_release: boolean;
  approved_average_overall_score: string | null;
  items: ReviewDashboardItem[];
};

export type JudgeCalibrationDimension = {
  field: string;
  label: string;
  paired_score_count: number;
  average_delta: string | null;
  exact_agreement_percent: string;
  within_one_agreement_percent: string;
  automated_higher_count: number;
  human_higher_count: number;
  equal_count: number;
  bias_direction: "aligned" | "automated_under_scores" | "automated_over_scores" | string;
};

export type JudgeCalibrationAnswer = {
  question_id: number;
  question_text: string;
  answer_id: number;
  automated_evaluation_id: number;
  human_evaluation_id: number;
  automated_overall_score: string;
  human_overall_score: string;
  overall_delta: string;
  dimension_deltas: DimensionScores;
  exact_matches: Record<string, boolean>;
  within_one_matches: Record<string, boolean>;
};

export type JudgeCalibrationReport = {
  project_id: number;
  run_id: number;
  run_name: string;
  paired_answer_count: number;
  automated_only_count: number;
  human_only_count: number;
  overall_exact_agreement_percent: string;
  overall_within_one_agreement_percent: string;
  average_overall_delta: string | null;
  dimension_calibration: JudgeCalibrationDimension[];
  answer_comparisons: JudgeCalibrationAnswer[];
};

export type ErrorCategory =
  | "retrieval_miss"
  | "citation_error"
  | "hallucination"
  | "incomplete_answer"
  | "irrelevant_answer"
  | "contradiction"
  | "latency_cost"
  | "format_error"
  | "policy_ambiguity"
  | "other";

export type ErrorSeverity = "low" | "medium" | "high" | "critical";

export type ErrorAnnotation = {
  id: number;
  evaluation_run_id: number;
  test_question_id: number;
  generated_answer_id: number;
  evaluation_record_id: number | null;
  created_by_user_id: number;
  category: ErrorCategory;
  severity: ErrorSeverity;
  source: "human" | "automated";
  notes: string | null;
  evidence_reference: string | null;
  created_at: string;
  updated_at: string;
};

export type ErrorTaxonomyBucket = {
  key: string;
  label: string;
  count: number;
  percent: string;
};

export type ErrorTaxonomyItem = {
  id: number;
  question_id: number;
  question_text: string;
  answer_id: number;
  answer_text: string;
  evaluation_record_id: number | null;
  category: ErrorCategory;
  category_label: string;
  severity: ErrorSeverity;
  source: "human" | "automated";
  notes: string | null;
  evidence_reference: string | null;
  created_by_user_id: number;
  created_at: string;
};

export type ErrorTaxonomyReport = {
  project_id: number;
  run_id: number;
  run_name: string;
  total_errors: number;
  affected_answers: number;
  category_counts: ErrorTaxonomyBucket[];
  severity_counts: ErrorTaxonomyBucket[];
  items: ErrorTaxonomyItem[];
};

export type AutoEvaluationResult = {
  run_id: number;
  evaluated_answers: number;
  skipped_answers: number;
  judge_model_name: string;
  message: string;
};

export type RagExecutionResult = {
  run_id: number;
  status: "completed" | "failed";
  model_name: string;
  processed_questions: number;
  retrieved_chunks_created: number;
  generated_answers_created: number;
  retrieval_mode: "keyword" | "vector";
  message: string;
};

export type BatchExperimentResult = {
  run: EvaluationRun;
  rag_execution: RagExecutionResult;
  auto_evaluation: AutoEvaluationResult | null;
  summary: RunSummary;
  message: string;
};

export type DimensionScores = {
  citation_quality_score: string | null;
  latency_cost_score: string | null;
  evidence_faithfulness_score: string | null;
  answer_relevance_score: string | null;
  retrieval_quality_score: string | null;
};

export type RetrievalQuestionMetric = {
  question_id: number;
  question_text: string;
  expected_source: string | null;
  expected_source_available: boolean;
  retrieved_chunk_count: number;
  relevant_chunk_count: number;
  expected_source_match: boolean | null;
  first_relevant_rank: number | null;
  precision_at_k: string | null;
  recall_at_k: string | null;
  reciprocal_rank: string | null;
  missing_evidence: boolean;
};

export type RetrievalMetrics = {
  project_id: number;
  run_id: number;
  evaluated_question_count: number;
  questions_with_expected_source: number;
  questions_with_retrieved_chunks: number;
  expected_source_hit_count: number;
  missing_evidence_count: number;
  hit_rate: string | null;
  precision_at_k: string | null;
  recall_at_k: string | null;
  mean_reciprocal_rank: string | null;
  chunk_coverage: string | null;
  question_metrics: RetrievalQuestionMetric[];
};

export type RunQuestionResult = {
  question_id: number;
  question_text: string;
  answer_id: number | null;
  answer_text: string | null;
  reviewed: boolean;
  overall_score: string | null;
  citation_quality_score: number | null;
  latency_cost_score: number | null;
  evidence_faithfulness_score: number | null;
  answer_relevance_score: number | null;
  retrieval_quality_score: number | null;
  evaluation_mode: "human" | "automated" | null;
  judge_model_name: string | null;
  review_status: "pending_review" | "approved" | "needs_revision" | null;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  expected_source_match: boolean | null;
  first_relevant_rank: number | null;
  retrieved_chunk_count: number;
  precision_at_k: string | null;
  recall_at_k: string | null;
  reciprocal_rank: string | null;
  missing_evidence: boolean;
};

export type RunSummary = {
  project_id: number;
  run_id: number;
  run_name: string;
  total_questions: number;
  generated_answers: number;
  reviewed_answers: number;
  review_completion_percent: string;
  average_overall_score: string | null;
  dimension_averages: DimensionScores;
  weakest_dimension: string | null;
  retrieval_metrics: RetrievalMetrics;
  question_results: RunQuestionResult[];
};

export type RunComparisonRun = {
  run_id: number;
  run_name: string;
  system_version: string | null;
  retrieval_mode: "keyword" | "vector" | null;
  generator_model_name: string | null;
  embedding_model_name: string | null;
  judge_model_name: string | null;
  generated_answers: number;
  reviewed_answers: number;
  average_overall_score: string | null;
  dimension_averages: DimensionScores;
  weakest_dimension: string | null;
};

export type RunComparisonDeltas = {
  overall_score_delta: string | null;
  citation_quality_delta: string | null;
  latency_cost_delta: string | null;
  evidence_faithfulness_delta: string | null;
  answer_relevance_delta: string | null;
  retrieval_quality_delta: string | null;
};

export type RunComparisonQuestionRunResult = {
  run_id: number;
  answer_id: number | null;
  answer_text: string | null;
  overall_score: string | null;
  reviewed: boolean;
  evaluation_mode: "human" | "automated" | null;
  judge_model_name: string | null;
};

export type RunComparisonQuestion = {
  question_id: number;
  question_text: string;
  best_run_id: number | null;
  run_results: RunComparisonQuestionRunResult[];
};

export type RunComparison = {
  project_id: number;
  baseline_run_id: number;
  compared_run_ids: number[];
  runs: RunComparisonRun[];
  metric_deltas: Record<string, RunComparisonDeltas>;
  question_results: RunComparisonQuestion[];
};

export type ExperimentLeaderboardRun = {
  rank: number;
  run_id: number;
  run_name: string;
  status: string;
  system_version: string | null;
  retrieval_mode: "keyword" | "vector" | null;
  generator_model_name: string | null;
  embedding_model_name: string | null;
  judge_model_name: string | null;
  generated_answers: number;
  reviewed_answers: number;
  review_completion_percent: string;
  average_overall_score: string | null;
  approved_average_overall_score: string | null;
  retrieval_hit_rate: string | null;
  retrieval_mrr: string | null;
  judge_exact_agreement_percent: string;
  judge_within_one_agreement_percent: string;
  judge_paired_answer_count: number;
  error_count: number;
  high_error_count: number;
  critical_error_count: number;
  leaderboard_score: string;
  quality_gate: string;
};

export type ExperimentLeaderboard = {
  project_id: number;
  project_name: string;
  total_runs: number;
  best_run_id: number | null;
  runs: ExperimentLeaderboardRun[];
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
