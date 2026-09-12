import React from 'react';
import { History, ShieldAlert, CheckCircle, Clock, Bell, FileText, User } from 'lucide-react';
import { AuditEvent } from '../types/schoolbag';

interface AuditEventStreamProps {
  events: AuditEvent[];
}

const getEventIcon = (eventType: string) => {
  switch (eventType) {
    case 'approval_rejected_human_gate':
      return <ShieldAlert size={14} color="var(--color-danger)" />;
    case 'action_approved_by_parent':
      return <CheckCircle size={14} color="var(--color-purple)" />;
    case 'action_completed':
      return <CheckCircle size={14} color="var(--color-success)" />;
    case 'deadline_updated':
      return <Clock size={14} color="var(--color-primary)" />;
    case 'reminder_drafted':
      return <Bell size={14} color="var(--color-warning)" />;
    case 'notice_ingested':
    case 'notice_replayed_duplicate':
      return <FileText size={14} color="var(--color-teal)" />;
    default:
      return <History size={14} color="var(--text-muted)" />;
  }
};

export const AuditEventStream: React.FC<AuditEventStreamProps> = ({ events }) => {
  return (
    <aside className="audit-col">
      <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.75rem' }}>
        <History size={16} /> Audit Event Log ({events.length})
      </h3>

      <div className="card" style={{ maxHeight: '600px', overflowY: 'auto', padding: '0.75rem' }}>
        {events.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem 0' }}>
            No audit events recorded yet
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {events.slice(0, 30).map((evt) => {
              const isSecurityRejection = evt.event_type === 'approval_rejected_human_gate';
              const timeStr = new Date(evt.timestamp).toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZone: 'Asia/Kolkata',
              });

              return (
                <div
                  key={evt.id}
                  style={{
                    padding: '0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid',
                    borderColor: isSecurityRejection ? '#fecaca' : 'var(--border-subtle)',
                    backgroundColor: isSecurityRejection ? '#fef2f2' : 'var(--bg-elevated)',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600, color: isSecurityRejection ? 'var(--color-danger)' : 'var(--text-primary)' }}>
                      {getEventIcon(evt.event_type)}
                      <span>{evt.event_type}</span>
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{timeStr}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                    <User size={11} />
                    <span>Actor: <strong>{evt.actor_type}</strong> ({evt.actor_id})</span>
                  </div>

                  {evt.notes && (
                    <div style={{ color: isSecurityRejection ? 'var(--color-danger)' : 'var(--text-secondary)', fontSize: '0.72rem', fontStyle: 'italic', wordBreak: 'break-word' }}>
                      {evt.notes}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
};
