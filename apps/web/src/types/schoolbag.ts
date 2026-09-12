export type SourceType = 'whatsapp' | 'email' | 'circular' | 'diary' | 'portal';

export type ActionType = 'fee_payment' | 'consent_slip' | 'material_bring' | 'exam_prep';

export type ActionStatus = 'draft' | 'approved' | 'completed' | 'dismissed';

export type ActorType = 'parent' | 'assistant' | 'system' | 'school';

export type ReminderChannel = 'in_app' | 'calendar' | 'email' | 'push';

export interface Notice {
  id: string;
  workspace_id: string;
  title: string;
  raw_content: string;
  source_type: SourceType;
  class_name?: string | null;
  child_alias?: string | null;
  received_at?: string | null;
  fingerprint: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface SchoolAction {
  id: string;
  notice_id: string;
  workspace_id: string;
  action_type: ActionType;
  title: string;
  description: string;
  category: string;
  due_date?: string | null;
  normalized_due_date?: string | null;
  amount?: number | null;
  currency?: string | null;
  status: ActionStatus;
  required_role: ActorType;
  approved_by?: ActorType | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ReminderDraft {
  id: string;
  action_id: string;
  workspace_id: string;
  scheduled_for: string;
  channel: ReminderChannel;
  payload?: Record<string, unknown>;
  is_dispatched: boolean;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  workspace_id: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  actor_type: ActorType;
  actor_id: string;
  notes?: string | null;
  payload?: Record<string, unknown>;
  timestamp: string;
}

export interface Workspace {
  id: string;
  name: string;
  created_at: string;
  notice_count?: number;
}

export interface NoticeCreatedResponse {
  notice: Notice;
  actions: SchoolAction[];
  deduplicated: boolean;
}

export interface NoticeAggregateResponse {
  notice: Notice;
  actions: SchoolAction[];
  reminders: ReminderDraft[];
  audit_events: AuditEvent[];
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  milestone: string;
  extractor: {
    mode: string;
    status: string;
    advisory_only: boolean;
  };
  database: {
    engine: 'sqlite' | 'postgres';
    status: string;
  };
}

export interface SchoolPreset {
  id: string;
  school_name: string;
  child_alias: string;
  class_name: string;
  title: string;
  body: string;
  source_type: SourceType;
  due_date?: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
