const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export type AnalysisStatus = 'success' | 'error';
export type TaskStatus = 'pending' | 'started' | 'success' | 'failure';

export interface CriteriaScore {
  score: number;
  feedback: string;
  suggestions: string[];
}

export interface ResumeAnalysisResponse {
  status: AnalysisStatus;
  overall_score: number;
  summary: string;
  criteria: Record<string, CriteriaScore>;
  top_strengths: string[];
  top_improvements: string[];
  file_name?: string | null;
}

export interface AnalyzeTaskResponse {
  task_id: string;
  status: TaskStatus;
  cached: boolean;
  result: ResumeAnalysisResponse | null;
}

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  result: ResumeAnalysisResponse | null;
}

export interface HistoryItem {
  id_: number;
  file_name?: string | null;
  overall_score: number;
  summary: string;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = await response.json();
      if (payload.detail) {
        message = Array.isArray(payload.detail)
          ? payload.detail.map((item: { msg?: string }) => item.msg || 'Validation error').join(', ')
          : String(payload.detail);
      }
    } catch {
      // Keep the default error message when the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function analyzeResume(file: File, callbackUrl?: string): Promise<AnalyzeTaskResponse> {
  const formData = new FormData();
  formData.append('file', file);

  if (callbackUrl?.trim()) {
    formData.append('callback_url', callbackUrl.trim());
  }

  return request<AnalyzeTaskResponse>('/api/v1/resume/analyze', {
    method: 'POST',
    body: formData
  });
}

export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return request<TaskStatusResponse>(`/api/v1/resume/analyze/${taskId}/status`);
}

export async function getHistory(limit = 10, offset = 0): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/api/v1/resume/history?limit=${limit}&offset=${offset}`);
}

export function getExportUrl(id: number): string {
  return `${API_BASE_URL}/api/v1/resume/${id}/export`;
}
