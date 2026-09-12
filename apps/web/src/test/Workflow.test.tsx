import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Header } from '../components/Header';
import { ActionCard } from '../components/ActionCard';
import { NoticeCard } from '../components/NoticeCard';
import { ProvenanceCard } from '../components/ProvenanceCard';
import { AuditEventStream } from '../components/AuditEventStream';
import { SchoolAction, Notice, HealthResponse, AuditEvent } from '../types/schoolbag';
import * as clientModule from '../api/client';

describe('Schoolbag Frontend Core Workflow & Guardrails', () => {
  it('renders evaluator guide, zero spend declaration, and minimal identifier guarantee', () => {
    render(
      <Header
        workspace={{ id: 'ws_test_123', name: 'Test Family', created_at: '2026-09-14T09:00:00Z' }}
        health={{
          status: 'ok',
          app: 'Schoolbag',
          version: '0.1.0',
          milestone: 'M1',
          extractor: { mode: 'deterministic', status: 'operational', advisory_only: true },
          database: { engine: 'sqlite', status: 'connected' },
        }}
        noticeCount={3}
        selectedChild={null}
        onSelectChild={() => {}}
        onOpenIntake={() => {}}
        onRefresh={() => {}}
        isLoading={false}
      />
    );

    expect(screen.getByText(/Evaluator Quick-Start & Guardrail Checklist/i)).toBeInTheDocument();
    expect(screen.getByText(/Minimal Identifiers/i)).toBeInTheDocument();
    expect(screen.getByText(/Capacity:/i)).toHaveTextContent('3 / 50 notices');
  });

  it('renders action card with normalized deadline and human gate demonstration button', async () => {
    const mockAction: SchoolAction = {
      id: 'act_fee_101',
      notice_id: 'not_1',
      workspace_id: 'ws_test',
      action_type: 'fee_payment',
      title: 'Pay Annual Day Costume Fee',
      description: 'Submit costume fee to class teacher',
      category: 'fees',
      due_date: 'Friday 5 PM',
      normalized_due_date: '2026-09-18T17:00:00+05:30',
      amount: 350,
      currency: 'INR',
      status: 'draft',
      required_role: 'parent',
      approved_by: null,
      approved_at: null,
      approval_notes: null,
      version: 1,
      created_at: '2026-09-14T09:00:00Z',
      updated_at: '2026-09-14T09:00:00Z',
    };

    const updateSpy = vi.fn();
    render(<ActionCard action={mockAction} onActionUpdated={updateSpy} />);

    expect(screen.getByText('Pay Annual Day Costume Fee')).toBeInTheDocument();
    expect(screen.getByText(/₹350 INR/i)).toBeInTheDocument();
    expect(screen.getByText(/Simulate Assistant Approval \(Expect 403\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Parent Sign & Authorize/i)).toBeInTheDocument();
  });

  it('handles simulated assistant approval rejection with HTTP 403 error banner', async () => {
    const mockAction: SchoolAction = {
      id: 'act_consent_202',
      notice_id: 'not_1',
      workspace_id: 'ws_test',
      action_type: 'consent_slip',
      title: 'Sign Field Trip Consent Form',
      description: 'Parent consent required for Ooty botanical garden excursion',
      category: 'consent',
      due_date: 'Tomorrow 10 AM',
      normalized_due_date: '2026-09-15T10:00:00+05:30',
      amount: null,
      currency: null,
      status: 'draft',
      required_role: 'parent',
      approved_by: null,
      approved_at: null,
      approval_notes: null,
      version: 1,
      created_at: '2026-09-14T09:00:00Z',
      updated_at: '2026-09-14T09:00:00Z',
    };

    vi.spyOn(clientModule.api, 'approveAction').mockRejectedValueOnce(
      new clientModule.ApiError(
        'HUMAN_APPROVAL_REQUIRED',
        "Role 'assistant' cannot approve action requiring human parent authorization.",
        403
      )
    );

    render(<ActionCard action={mockAction} onActionUpdated={vi.fn()} />);

    const simButton = screen.getByText(/Simulate Assistant Approval/i);
    fireEvent.click(simButton);

    await waitFor(() => {
      expect(screen.getByText(/HTTP 403 - HUMAN_APPROVAL_REQUIRED/i)).toBeInTheDocument();
    });
  });

  it('renders notice card with synthetic metadata and child context', () => {
    const mockNotice: Notice = {
      id: 'not_123',
      workspace_id: 'ws_test',
      title: 'Science Project Materials Circular',
      raw_content: 'Please send chart papers and clay tomorrow for Science Fair exhibition.',
      source_type: 'circular',
      class_name: 'Class 5-B',
      child_alias: 'Kavya',
      fingerprint: 'fp_abc123',
      created_at: '2026-09-14T09:00:00Z',
    };

    render(<NoticeCard notice={mockNotice} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Science Project Materials Circular')).toBeInTheDocument();
    expect(screen.getByText('Kavya')).toBeInTheDocument();
    expect(screen.getByText('Class 5-B')).toBeInTheDocument();
  });

  it('renders audit event stream with security rejection event', () => {
    const mockEvents: AuditEvent[] = [
      {
        id: 'evt_1',
        workspace_id: 'ws_test',
        entity_type: 'action',
        entity_id: 'act_101',
        event_type: 'approval_rejected_human_gate',
        actor_type: 'assistant',
        actor_id: 'bot_ai',
        notes: 'Autonomous approval attempt blocked: parent role required.',
        timestamp: '2026-09-14T09:30:00Z',
      },
    ];

    render(<AuditEventStream events={mockEvents} />);

    expect(screen.getByText('approval_rejected_human_gate')).toBeInTheDocument();
    expect(screen.getByText(/Autonomous approval attempt blocked/i)).toBeInTheDocument();
  });

  it('renders provenance card with truthful disclosures and Strands agent seam', () => {
    const health: HealthResponse = {
      status: 'ok',
      app: 'Schoolbag',
      version: '0.1.0',
      milestone: 'M1',
      extractor: {
        mode: 'deterministic',
        status: 'operational',
        advisory_only: true,
      },
      strands: {
        engine: 'strands',
        status: 'operational',
        advisory_only: true,
      },
      database: {
        engine: 'postgres',
        status: 'connected',
      },
    };

    render(<ProvenanceCard health={health} />);

    expect(screen.getByText(/Truthful Provenance & Safety Declarations/i)).toBeInTheDocument();
    expect(screen.getByText(/Strands Agent Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/get_school_notice_context/i)).toBeInTheDocument();
    expect(screen.getByText(/Kovai Vidya Mandir, Coimbatore, TN/i)).toBeInTheDocument();
    expect(screen.getByText(/₹0.00 \/ \$0.00/i)).toBeInTheDocument();
  });

  it('triggers Strands AI analysis on notice card and renders advisory drafts with human gate notice', async () => {
    const mockNotice: Notice = {
      id: 'not_sports_99',
      notice_id: 'not_sports_99',
      workspace_id: 'ws_test',
      title: 'Annual Sports Day & Bus Transport Notice',
      raw_content: 'Annual Sports Meet on Friday. Transport fee is Rs 200. Parent consent mandatory.',
      source_type: 'circular',
      class_name: 'Class 8-A',
      child_alias: 'Arun',
      fingerprint: 'fp_sports_99',
      version: 1,
      created_at: '2026-09-14T09:00:00Z',
    };

    vi.spyOn(clientModule.api, 'analyzeNoticeStrands').mockResolvedValueOnce({
      notice_id: 'not_sports_99',
      source_version: 1,
      summary: 'Annual Sports Day requiring transport fee payment and signed parent consent.',
      is_urgent: true,
      advisory_notes: 'Both actions strictly require parental approval before execution.',
      suggested_actions: [
        {
          category: 'fees',
          title: 'Pay Sports Transport Fee',
          description: 'Submit Rs 200 for bus transport to sports ground',
          deadline_hint: 'Friday 9 AM',
          amount_inr: 200,
          approval_required: true,
        },
        {
          category: 'consent',
          title: 'Sign Sports Day Participation Form',
          description: 'Parent consent slip for student athletic events',
          deadline_hint: 'Thursday 4 PM',
          amount_inr: null,
          approval_required: true,
        },
      ],
      provenance: {
        engine: 'strands',
        model: 'openai/gpt-oss-20b',
        grounded_against_tool: true,
        tool_calls_observed: 1,
      },
    });

    render(<NoticeCard notice={mockNotice} isSelected={false} onSelect={vi.fn()} />);

    const analyzeBtn = screen.getByRole('button', { name: /Analyze with Strands AI/i });
    expect(analyzeBtn).toBeInTheDocument();

    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(screen.getByText(/Strands Advisory \(openai\/gpt-oss-20b\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Urgent Priority/i)).toBeInTheDocument();
      expect(screen.getByText('Pay Sports Transport Fee')).toBeInTheDocument();
      expect(screen.getByText(/₹200 INR/i)).toBeInTheDocument();
      expect(screen.getByText('Sign Sports Day Participation Form')).toBeInTheDocument();
      expect(screen.getAllByText(/Advisory Draft - Requires Human Parent Approval/i).length).toBe(2);
      expect(screen.getByText(/Bounded Tool:/i)).toHaveTextContent('get_school_notice_context');
    });
  });

  it('handles Strands AI rate limiting error 429 ASSISTANT_BUSY with warning banner', async () => {
    const mockNotice: Notice = {
      id: 'not_busy_12',
      workspace_id: 'ws_test',
      title: 'Exhibition Reminder',
      raw_content: 'Exhibition on Monday.',
      source_type: 'whatsapp',
      fingerprint: 'fp_busy',
      created_at: '2026-09-14T09:00:00Z',
    };

    vi.spyOn(clientModule.api, 'analyzeNoticeStrands').mockRejectedValueOnce(
      new clientModule.ApiError(
        'ASSISTANT_BUSY',
        'Model inference quota or concurrent active limit reached. Please wait 15 minutes.',
        429
      )
    );

    render(<NoticeCard notice={mockNotice} isSelected={false} onSelect={vi.fn()} />);

    const analyzeBtn = screen.getByRole('button', { name: /Analyze with Strands AI/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(screen.getByText(/HTTP 429 - ASSISTANT_BUSY/i)).toBeInTheDocument();
      expect(screen.getByText(/Model inference quota or concurrent active limit reached/i)).toBeInTheDocument();
    });
  });
});
