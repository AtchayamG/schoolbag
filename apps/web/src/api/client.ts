import {
  AuditEvent,
  HealthResponse,
  Notice,
  NoticeAggregateResponse,
  NoticeCreatedResponse,
  ReminderDraft,
  SchoolAction,
  SchoolPreset,
  StrandsAdvisoryResponse,
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

function normalizeWorkspace(item: Workspace & { workspace_id?: string }): Workspace {
  return { ...item, id: item.workspace_id || item.id, name: item.name || 'Family workspace' };
}

// Normalization helpers ensuring both camel/snake case and legacy/backend shapes align seamlessly
function normalizeNotice(item: Record<string, unknown>): Notice {
  return {
    ...item,
    id: (item.id || item.notice_id || '') as string,
    notice_id: (item.notice_id || item.id || '') as string,
    workspace_id: (item.workspace_id || '') as string,
    title: (item.title || '') as string,
    raw_content: (item.raw_content || item.raw_body || '') as string,
    raw_body: (item.raw_body || item.raw_content || '') as string,
    source_type: (item.source_type || 'whatsapp') as any,
    class_name: item.class_name as string | null | undefined,
    child_alias: item.child_alias as string | null | undefined,
    received_at: item.received_at as string | null | undefined,
    normalized_due_at: item.normalized_due_at as string | null | undefined,
    raw_due_text: item.raw_due_text as string | null | undefined,
    fingerprint: (item.fingerprint || item.source_fingerprint || '') as string,
    source_fingerprint: (item.source_fingerprint || item.fingerprint || '') as string,
    version: typeof item.version === 'number' ? item.version : 1,
    created_at: (item.created_at || new Date().toISOString()) as string,
    updated_at: item.updated_at as string | undefined,
  };
}

function normalizeAction(item: Record<string, unknown>): SchoolAction {
  return {
    ...item,
    id: (item.id || item.action_id || '') as string,
    action_id: (item.action_id || item.id || '') as string,
    notice_id: (item.notice_id || '') as string,
    workspace_id: (item.workspace_id || '') as string,
    action_type: (item.action_type || 'fee_payment') as any,
    title: (item.title || '') as string,
    description: (item.description || '') as string,
    category: (item.category || item.action_type || 'general') as string,
    due_date: (item.due_date || item.raw_deadline || null) as string | null,
    raw_deadline: (item.raw_deadline || item.due_date || null) as string | null,
    normalized_due_date: (item.normalized_due_date || item.normalized_deadline || null) as string | null,
    normalized_deadline: (item.normalized_deadline || item.normalized_due_date || null) as string | null,
    amount: (item.amount ?? item.amount_inr ?? null) as number | null,
    amount_inr: (item.amount_inr ?? item.amount ?? null) as number | null,
    currency: (item.currency || 'INR') as string,
    status: (item.status === 'extracted' ? 'draft' : item.status || 'draft') as any,
    required_role: (item.required_role || (item.approval_required ? 'parent' : 'system')) as any,
    approved_by: item.approved_by as any,
    approved_at: item.approved_at as string | null | undefined,
    approval_notes: item.approval_notes as string | null | undefined,
    version: typeof item.version === 'number' ? item.version : 1,
    created_at: (item.created_at || new Date().toISOString()) as string,
    updated_at: (item.updated_at || new Date().toISOString()) as string,
  };
}

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
  getCurrentWorkspace: async (): Promise<Workspace> => normalizeWorkspace(await request<Workspace>('/api/workspaces/current')),
  createWorkspace: (name?: string): Promise<Workspace> =>
    request<Workspace>('/api/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }).then(normalizeWorkspace),

  // Presets
  getPresets: async (): Promise<SchoolPreset[]> => {
    const items = await request<(SchoolPreset & { preset_id?: string; raw_body?: string; raw_due_text?: string })[]>('/api/presets');
    return items.map(item => ({ ...item, id: item.preset_id || item.id, body: item.raw_body || item.body, due_date: item.raw_due_text || item.due_date }));
  },

  // Notices
  getNotices: async (childAlias?: string): Promise<Notice[]> => {
    const query = childAlias ? `?child_alias=${encodeURIComponent(childAlias)}` : '';
    const items = await request<Record<string, unknown>[]>(`/api/notices${query}`);
    return items.map(normalizeNotice);
  },

  createNotice: async (
    noticeData: {
      title: string;
      raw_content: string;
      raw_due_text?: string | null;
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
    const payload = {
      title: noticeData.title,
      raw_body: (noticeData as any).raw_body || noticeData.raw_content,
      source_type: noticeData.source_type,
      class_name: noticeData.class_name || 'Class 5-B',
      child_alias: noticeData.child_alias || 'Kavya',
      raw_due_text: (noticeData as any).raw_due_text || null,
      idempotency_key: noticeData.idempotency_key || null,
    };
    const resp = await request<{
      notice: Record<string, unknown>;
      actions: Record<string, unknown>[];
      is_deduplicated?: boolean;
      deduplicated?: boolean;
    }>('/api/notices', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return {
      notice: normalizeNotice(resp.notice),
      actions: (resp.actions || []).map(normalizeAction),
      deduplicated: resp.is_deduplicated ?? resp.deduplicated ?? false,
      is_deduplicated: resp.is_deduplicated ?? resp.deduplicated ?? false,
    };
  },

  getNoticeAggregate: async (id: string): Promise<NoticeAggregateResponse> => {
    const data = await request<{
      notice: Record<string, unknown>;
      actions: Record<string, unknown>[];
      reminders: ReminderDraft[];
      audit_events: AuditEvent[];
    }>(`/api/notices/${id}`);
    return {
      notice: normalizeNotice(data.notice),
      actions: (data.actions || []).map(normalizeAction),
      reminders: data.reminders || [],
      audit_events: data.audit_events || [],
    };
  },

  // Strands AI Advisory Loop
  analyzeNoticeStrands: (
    noticeId: string,
    expectedVersion: number = 1,
    idempotencyKey?: string,
  ): Promise<StrandsAdvisoryResponse> => {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return request<StrandsAdvisoryResponse>(`/api/notices/${noticeId}/analyze-strands`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        expected_version: expectedVersion,
        idempotency_key: idempotencyKey || null,
      }),
    });
  },

  // Actions
  getActions: async (noticeId?: string, status?: string): Promise<SchoolAction[]> => {
    const params = new URLSearchParams();
    if (noticeId) params.append('notice_id', noticeId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const items = await request<Record<string, unknown>[]>(`/api/actions${qs}`);
    return items.map(normalizeAction);
  },

  getAction: async (id: string): Promise<SchoolAction> => {
    const item = await request<Record<string, unknown>>(`/api/actions/${id}`);
    return normalizeAction(item);
  },

  updateActionDeadline: async (id: string, deadline: string, expectedVersion: number): Promise<SchoolAction> => {
    const item = await request<Record<string, unknown>>(`/api/actions/${id}/deadline`, {
      method: 'PATCH',
      body: JSON.stringify({ raw_deadline: deadline, expected_version: expectedVersion }),
    });
    return normalizeAction(item);
  },

  approveAction: async (
    id: string,
    role: string,
    expectedVersion: number,
    notes?: string,
  ): Promise<SchoolAction> => {
    const item = await request<Record<string, unknown>>(`/api/actions/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ actor_type: role, expected_version: expectedVersion, actor_name: notes || 'Parent' }),
    });
    return normalizeAction(item);
  },

  completeAction: async (
    id: string,
    expectedVersion: number,
    notes?: string,
  ): Promise<SchoolAction> => {
    const item = await request<Record<string, unknown>>(`/api/actions/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify({ expected_version: expectedVersion, actor_name: notes || 'Parent' }),
    });
    return normalizeAction(item);
  },

  // Reminders
  createReminder: (
    actionId: string,
    scheduledFor: string,
    channel: string = 'calendar',
    payload: Record<string, unknown> = {},
  ): Promise<ReminderDraft> =>
    request<ReminderDraft>(`/api/actions/${actionId}/reminders`, {
      method: 'POST',
      body: JSON.stringify({
        scheduled_for: scheduledFor,
        channel,
        message_body: (payload.notes as string) || 'School reminder',
        expected_action_version: 1,
      }),
    }),

  getReminders: (): Promise<ReminderDraft[]> => request<ReminderDraft[]>('/api/reminders'),

  // Audit
  getAuditEvents: (entityId?: string): Promise<AuditEvent[]> => {
    const query = entityId ? `?entity_id=${encodeURIComponent(entityId)}` : '';
    return request<AuditEvent[]>(`/api/audit${query}`);
  },
};
