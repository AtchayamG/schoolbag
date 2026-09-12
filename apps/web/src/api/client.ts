import {
  AuditEvent,
  HealthResponse,
  Notice,
  NoticeAggregateResponse,
  NoticeCreatedResponse,
  ReminderDraft,
  SchoolAction,
  SchoolPreset,
  Workspace,
} from '../types/schoolbag';

class ApiError extends Error {
  code: string;
  statusCode: number;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, statusCode: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export { ApiError };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    let errorData = {
      error: 'HTTP_ERROR',
      message: `Request failed with status ${response.status}`,
      details: undefined as Record<string, unknown> | undefined,
    };
    try {
      const json = await response.json();
      if (json.error || json.message) {
        errorData = {
          error: json.error || 'HTTP_ERROR',
          message: json.message || response.statusText,
          details: json.details,
        };
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiError(errorData.error, errorData.message, response.status, errorData.details);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Health & Readiness
  getHealth: (): Promise<HealthResponse> => request<HealthResponse>('/api/health'),

  // Workspace
  getCurrentWorkspace: (): Promise<Workspace> => request<Workspace>('/api/workspaces/current'),
  createWorkspace: (name?: string): Promise<Workspace> =>
    request<Workspace>('/api/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  // Presets
  getPresets: (): Promise<SchoolPreset[]> => request<SchoolPreset[]>('/api/presets'),

  // Notices
  getNotices: (childAlias?: string): Promise<Notice[]> => {
    const query = childAlias ? `?child_alias=${encodeURIComponent(childAlias)}` : '';
    return request<Notice[]>(`/api/notices${query}`);
  },

  createNotice: (
    noticeData: {
      title: string;
      raw_content: string;
      source_type: string;
      class_name?: string | null;
      child_alias?: string | null;
      received_at?: string | null;
      idempotency_key?: string | null;
    },
    idempotencyKeyHeader?: string,
  ): Promise<NoticeCreatedResponse> => {
    const headers: Record<string, string> = {};
    if (idempotencyKeyHeader) {
      headers['Idempotency-Key'] = idempotencyKeyHeader;
    }
    return request<NoticeCreatedResponse>('/api/notices', {
      method: 'POST',
      headers,
      body: JSON.stringify(noticeData),
    });
  },

  getNoticeAggregate: (id: string): Promise<NoticeAggregateResponse> =>
    request<NoticeAggregateResponse>(`/api/notices/${id}`),

  // Actions
  getActions: (noticeId?: string, status?: string): Promise<SchoolAction[]> => {
    const params = new URLSearchParams();
    if (noticeId) params.append('notice_id', noticeId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<SchoolAction[]>(`/api/actions${qs}`);
  },

  getAction: (id: string): Promise<SchoolAction> => request<SchoolAction>(`/api/actions/${id}`),

  updateActionDeadline: (id: string, deadline: string): Promise<SchoolAction> =>
    request<SchoolAction>(`/api/actions/${id}/deadline`, {
      method: 'PATCH',
      body: JSON.stringify({ deadline }),
    }),

  approveAction: (
    id: string,
    role: string,
    expectedVersion: number,
    notes?: string,
  ): Promise<SchoolAction> =>
    request<SchoolAction>(`/api/actions/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ role, expected_version: expectedVersion, notes }),
    }),

  completeAction: (
    id: string,
    expectedVersion: number,
    notes?: string,
  ): Promise<SchoolAction> =>
    request<SchoolAction>(`/api/actions/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify({ expected_version: expectedVersion, notes }),
    }),

  // Reminders
  createReminder: (
    actionId: string,
    scheduledFor: string,
    channel: string = 'in_app',
    payload: Record<string, unknown> = {},
  ): Promise<ReminderDraft> =>
    request<ReminderDraft>(`/api/actions/${actionId}/reminders`, {
      method: 'POST',
      body: JSON.stringify({ scheduled_for: scheduledFor, channel, payload }),
    }),

  getReminders: (): Promise<ReminderDraft[]> => request<ReminderDraft[]>('/api/reminders'),

  // Audit
  getAuditEvents: (entityId?: string): Promise<AuditEvent[]> => {
    const query = entityId ? `?entity_id=${encodeURIComponent(entityId)}` : '';
    return request<AuditEvent[]>(`/api/audit${query}`);
  },
};
