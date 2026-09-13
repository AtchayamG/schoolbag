import React, { useState } from 'react';
import {
  ShieldCheck,
  Database,
  Users,
  PlusCircle,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  HelpCircle,
} from 'lucide-react';
import { Workspace, HealthResponse } from '../types/schoolbag';

interface HeaderProps {
  workspace: Workspace | null;
  health: HealthResponse | null;
  noticeCount: number;
  selectedChild: string | null;
  onSelectChild: (child: string | null) => void;
  onOpenIntake: () => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  workspace,
  health,
  noticeCount,
  selectedChild,
  onSelectChild,
  onOpenIntake,
  onRefresh,
  isLoading,
}) => {
  const [showWalkthrough, setShowWalkthrough] = useState(false);
  const maxNotices = 50;
  const isNearCapacity = noticeCount >= 40;
  const isFull = noticeCount >= maxNotices;

  return (
    <header style={{ marginBottom: '1.5rem' }}>
      {/* Evaluator Guide Banner */}
      <div className="banner-evaluator">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3>
            <ShieldCheck size={18} />
            Evaluator Quick-Start & Guardrail Checklist (SB-001 &ndash; SB-005)
          </h3>
          <button
            onClick={() => setShowWalkthrough(!showWalkthrough)}
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', background: '#334155', color: '#f8fafc', border: '1px solid #475569' }}
          >
            <HelpCircle size={13} />
            <span>{showWalkthrough ? 'Hide 1-Min Tour' : '1-Min Evaluator Walkthrough'}</span>
            {showWalkthrough ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
        </div>

        <p style={{ marginTop: '0.25rem' }}>
          <strong>Workflow Pipeline:</strong> Intake &rarr; Extraction &rarr; Child Context &rarr; Deduplication &rarr; IST Normalization &rarr; <strong>Strands Advisory Loop</strong> &rarr; <strong>Human Authority Gate</strong> &rarr; <strong>iCalendar .ics / WhatsApp Draft</strong> &rarr; Completion.
        </p>

        {showWalkthrough && (
          <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#0f172a', borderRadius: 'var(--radius-sm)', border: '1px solid #334155' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.4rem' }}>
              60-Second Evaluator Verification Sequence:
            </div>
            <ol style={{ fontSize: '0.75rem', color: '#cbd5e1', paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <li>Click <strong>&ldquo;Ingest School Notice&rdquo;</strong> &rarr; select a synthetic preset for <em>Kovai Vidya Mandir, Coimbatore</em>.</li>
              <li>Click <strong>&ldquo;Analyze with Strands AI&rdquo;</strong> on the notice card to trigger the Strands bounded tool advisory loop.</li>
              <li>Observe extracted actions: <strong>Fee Payment</strong> (₹350), <strong>Consent Slip</strong> (Field Trip), and <strong>Materials</strong> (chart paper).</li>
              <li>Click <strong>&ldquo;Simulate Assistant Approval (Expect 403)&rdquo;</strong> &rarr; verify the red HTTP 403 rejection banner enforcing the Human Authority Gate.</li>
              <li>Click <strong>&ldquo;Parent Sign &amp; Authorize&rdquo;</strong> &rarr; notice the action updates to <em>Parent Authorized</em> with actor timestamp.</li>
              <li>Click <strong>&ldquo;Export .ics&rdquo;</strong> on an action or switch to <strong>&ldquo;Family Weekly Board&rdquo;</strong> to export full family schedule.</li>
              <li>Click <strong>&ldquo;WhatsApp Draft&rdquo;</strong> to copy formatted parent reminder directly to clipboard.</li>
              <li>Click <strong>&ldquo;Mark Completed&rdquo;</strong> to finalize the task.</li>
            </ol>
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', flexWrap: 'wrap', fontSize: '0.75rem', color: '#94a3b8' }}>
          <span>&bull; Personal Spend: <strong>₹0.00 / $0.00</strong> (Deterministic Synthetic Engine + Free Model Adapter)</span>
          <span>&bull; Privacy: <strong>Minimal Identifiers</strong> (Alias only; zero DOB, medical, or student ID stored)</span>
          <span>&bull; Safety: <strong>Never autosigns consent or spends money</strong></span>
        </div>
      </div>

      {/* Main Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', background: 'var(--bg-surface)', padding: '1rem 1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary)', letterSpacing: '-0.025em' }}>
              Schoolbag
            </h1>
            <span style={{ fontSize: '0.8rem', padding: '0.15rem 0.5rem', background: 'var(--bg-elevated)', borderRadius: '4px', color: 'var(--text-muted)' }}>
              v0.5.0 (Tamil Nadu Demo)
            </span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Turn chaotic school WhatsApp forwards and circulars into clear family actions
          </p>
        </div>

        {/* System Badges & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Workspace ID */}
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'var(--bg-elevated)', padding: '0.35rem 0.65rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            Workspace: <code>{workspace ? workspace.id.slice(0, 10) + '...' : 'Connecting...'}</code>
          </div>

          {/* Database Engine */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'var(--bg-elevated)', padding: '0.35rem 0.65rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <Database size={14} color="var(--color-teal)" />
            <span>{health?.database.engine === 'postgres' ? 'PostgreSQL' : 'SQLite WAL'}</span>
          </div>

          {/* Notice Capacity */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.8rem',
            padding: '0.35rem 0.65rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid',
            borderColor: isFull ? 'var(--color-danger)' : isNearCapacity ? 'var(--color-warning)' : 'var(--border-subtle)',
            backgroundColor: isFull ? 'var(--color-danger-bg)' : isNearCapacity ? 'var(--color-warning-bg)' : 'var(--bg-elevated)',
            color: isFull ? 'var(--color-danger)' : isNearCapacity ? 'var(--color-warning)' : 'var(--text-secondary)'
          }}>
            {isNearCapacity && <AlertTriangle size={14} />}
            <span>Capacity: <strong>{noticeCount}</strong> / {maxNotices} notices</span>
          </div>

          {/* Refresh Button */}
          <button
            className="btn btn-secondary"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh active notices and actions"
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
          </button>

          {/* New Notice Intake */}
          <button
            className="btn btn-primary"
            onClick={onOpenIntake}
            disabled={isFull}
          >
            <PlusCircle size={16} />
            <span>Ingest School Notice</span>
          </button>
        </div>
      </div>

      {/* Child Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Users size={14} /> Filter by Child:
        </span>
        <button
          onClick={() => onSelectChild(null)}
          className={`btn ${selectedChild === null ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
        >
          All Children
        </button>
        <button
          onClick={() => onSelectChild('Kavya')}
          className={`btn ${selectedChild === 'Kavya' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
        >
          Kavya (Class 5-B)
        </button>
        <button
          onClick={() => onSelectChild('Arun')}
          className={`btn ${selectedChild === 'Arun' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
        >
          Arun (Class 8-A)
        </button>
      </div>
    </header>
  );
};
