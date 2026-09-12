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

  it('renders provenance card with truthful disclosures', () => {
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
      database: {
        engine: 'postgres',
        status: 'connected',
      },
    };

    render(<ProvenanceCard health={health} />);

    expect(screen.getByText(/Truthful Provenance & Safety Declarations/i)).toBeInTheDocument();
    expect(screen.getByText(/Kovai Vidya Mandir, Coimbatore, TN/i)).toBeInTheDocument();
    expect(screen.getByText(/₹0.00 \/ \$0.00/i)).toBeInTheDocument();
  });
});
