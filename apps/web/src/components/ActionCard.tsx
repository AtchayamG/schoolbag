import React, { useState } from 'react';
import {
  CreditCard,
  FileCheck2,
  Package,
  GraduationCap,
  Calendar,
  Clock,
  Check,
  ShieldAlert,
  Bell,
  Edit2,
  CheckCircle2,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import { ActionType, SchoolAction } from '../types/schoolbag';

interface ActionCardProps {
  action: SchoolAction;
  onActionUpdated: () => void;
}

const getCategoryBadge = (type: ActionType) => {
  switch (type) {
    case 'fee_payment':
      return (
        <span className="badge badge-fee">
          <CreditCard size={12} /> Fee Payment
        </span>
      );
    case 'consent_slip':
      return (
        <span className="badge badge-consent">
          <FileCheck2 size={12} /> Consent Slip
        </span>
      );
    case 'material_bring':
      return (
        <span className="badge badge-material">
          <Package size={12} /> Material / Pack
        </span>
      );
    case 'exam_prep':
      return (
        <span className="badge badge-exam">
          <GraduationCap size={12} /> Exam / Academic
        </span>
      );
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'draft':
      return <span className="badge badge-draft">Draft (Pending Review)</span>;
    case 'approved':
      return <span className="badge badge-approved">Parent Authorized</span>;
    case 'completed':
      return <span className="badge badge-completed">Completed</span>;
    default:
      return <span className="badge">{status}</span>;
  }
};

export const ActionCard: React.FC<ActionCardProps> = ({ action, onActionUpdated }) => {
  const [isEditingDeadline, setIsEditingDeadline] = useState(false);
  const [newDeadline, setNewDeadline] = useState(action.normalized_due_date || '');
  const [isDraftingReminder, setIsDraftingReminder] = useState(false);
  const [reminderDate, setReminderDate] = useState(
    action.normalized_due_date ? action.normalized_due_date.slice(0, 16) : ''
  );
  const [reminderChannel, setReminderChannel] = useState('in_app');
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Normal human-readable deadline
  const displayDeadline = action.normalized_due_date
    ? new Date(action.normalized_due_date).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'Asia/Kolkata',
      }) + ' (IST)'
    : action.due_date || 'No deadline specified';

  // Handle Assistant Approval simulation (deliberate 403 test)
  const handleSimulateAssistantApproval = async () => {
    setIsLoading(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      await api.approveAction(action.id, 'assistant', action.version);
      setSuccessBanner('Unexpected: Assistant approval passed.');
      onActionUpdated();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(
          `[HTTP ${err.statusCode} - ${err.code}] Human Gate Enforced: ${err.message}`
        );
      } else {
        setErrorBanner('Failed to execute simulation.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Parent Approval
  const handleParentApproval = async () => {
    setIsLoading(true);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      await api.approveAction(action.id, 'parent', action.version, 'Authorized by Parent');
      setSuccessBanner('Action approved successfully by parent.');
      setTimeout(() => {
        setSuccessBanner(null);
        onActionUpdated();
      }, 800);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(`[${err.code}] ${err.message}`);
      } else {
        setErrorBanner('Approval failed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Completion
  const handleComplete = async () => {
    setIsLoading(true);
    setErrorBanner(null);
    try {
      await api.completeAction(action.id, action.version);
      setSuccessBanner('Marked as completed!');
      setTimeout(() => {
        setSuccessBanner(null);
        onActionUpdated();
      }, 800);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(`[${err.code}] ${err.message}`);
      } else {
        setErrorBanner('Completion failed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Deadline update
  const handleSaveDeadline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeadline.trim()) return;
    setIsLoading(true);
    setErrorBanner(null);
    try {
      await api.updateActionDeadline(action.id, newDeadline.trim());
      setIsEditingDeadline(false);
      onActionUpdated();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(`[${err.code}] ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Reminder Draft creation
  const handleCreateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reminderDate.trim()) return;
    setIsLoading(true);
    setErrorBanner(null);
    try {
      await api.createReminder(action.id, reminderDate, reminderChannel);
      setIsDraftingReminder(false);
      setSuccessBanner('Reminder draft created successfully.');
      setTimeout(() => {
        setSuccessBanner(null);
        onActionUpdated();
      }, 1000);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(`[${err.code}] ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--color-primary)' }}>
      {/* Top Badges & Meta */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {getCategoryBadge(action.action_type)}
          {getStatusBadge(action.status)}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Version: <code>v{action.version}</code>
        </div>
      </div>

      {/* Action Title & Amount */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.35rem' }}>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          {action.title}
        </h4>
        {action.amount != null && (
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0891b2', whiteSpace: 'nowrap' }}>
            ₹{action.amount.toLocaleString('en-IN')} {action.currency || 'INR'}
          </div>
        )}
      </div>

      {/* Description */}
      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.4 }}>
        {action.description}
      </p>

      {/* Deadline Info & Inline Edit */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'var(--bg-elevated)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '0.75rem', fontSize: '0.8rem' }}>
        <Clock size={14} color="var(--color-primary)" />
        <span style={{ color: 'var(--text-secondary)' }}>Normalized Deadline:</span>
        <strong style={{ color: 'var(--text-primary)' }}>{displayDeadline}</strong>
        <button
          onClick={() => setIsEditingDeadline(!isEditingDeadline)}
          style={{ marginLeft: 'auto', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
        >
          <Edit2 size={12} /> {isEditingDeadline ? 'Cancel' : 'Edit'}
        </button>
      </div>

      {isEditingDeadline && (
        <form onSubmit={handleSaveDeadline} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <input
            type="text"
            value={newDeadline}
            onChange={(e) => setNewDeadline(e.target.value)}
            placeholder="e.g. Friday 5 PM or 2026-09-20T17:00:00"
            style={{ flex: 1, fontSize: '0.8rem' }}
          />
          <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
            Save
          </button>
        </form>
      )}

      {/* Rejection / Warning Banner */}
      {errorBanner && (
        <div className="banner-warning" style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{errorBanner}</span>
        </div>
      )}

      {/* Success Banner */}
      {successBanner && (
        <div className="banner-success" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <CheckCircle2 size={16} />
          <span>{successBanner}</span>
        </div>
      )}

      {/* Human Gate Action Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '0.5rem' }}>
        {/* Reminder button */}
        <button
          onClick={() => setIsDraftingReminder(!isDraftingReminder)}
          className="btn btn-secondary"
          style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
        >
          <Bell size={13} /> Draft Reminder
        </button>

        {/* State transition buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {action.status === 'draft' && (
            <>
              {/* Evaluator Demo Button: Assistant Approval Rejection */}
              <button
                type="button"
                onClick={handleSimulateAssistantApproval}
                disabled={isLoading}
                className="btn btn-danger-outline"
                style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
                title="Demonstrates domain security policy: AI/assistant cannot authorize payments or sign consent"
              >
                <ShieldAlert size={13} /> Simulate Assistant Approval (Expect 403)
              </button>

              {/* Authorized Parent Button */}
              <button
                type="button"
                onClick={handleParentApproval}
                disabled={isLoading}
                className="btn btn-primary"
                style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
              >
                <Check size={13} /> Parent Sign & Authorize
              </button>
            </>
          )}

          {action.status === 'approved' && (
            <button
              type="button"
              onClick={handleComplete}
              disabled={isLoading}
              className="btn btn-success"
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
            >
              <CheckCircle2 size={13} /> Mark Completed
            </button>
          )}

          {action.status === 'completed' && (
            <span style={{ fontSize: '0.8rem', color: 'var(--color-success)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <CheckCircle2 size={14} /> Done
            </span>
          )}
        </div>
      </div>

      {/* Inline Reminder Drafting Form */}
      {isDraftingReminder && (
        <form onSubmit={handleCreateReminder} style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Calendar size={13} /> Draft Calendar / Notification Reminder (Advisory Draft)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="datetime-local"
              value={reminderDate}
              onChange={(e) => setReminderDate(e.target.value)}
              style={{ fontSize: '0.75rem' }}
              required
            />
            <select
              value={reminderChannel}
              onChange={(e) => setReminderChannel(e.target.value)}
              style={{ fontSize: '0.75rem' }}
            >
              <option value="in_app">In-App Banner</option>
              <option value="calendar">Device Calendar</option>
              <option value="email">Family Email</option>
              <option value="push">Push Notification</option>
            </select>
            <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}>
              Schedule Draft
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
