import React, { useMemo } from 'react';
import {
  Calendar,
  AlertTriangle,
  User,
  Download,
} from 'lucide-react';
import { Notice, SchoolAction } from '../types/schoolbag';
import { ActionCard } from './ActionCard';

interface FamilyWeeklyBoardProps {
  actions: SchoolAction[];
  notices: Notice[];
  onActionUpdated: () => void;
}

export const FamilyWeeklyBoard: React.FC<FamilyWeeklyBoardProps> = ({
  actions,
  notices,
  onActionUpdated,
}) => {
  // Map notice ID to child alias
  const noticeMap = useMemo(() => {
    const map = new Map<string, Notice>();
    notices.forEach((n) => map.set(n.id || (n as any).notice_id, n));
    return map;
  }, [notices]);

  // Group actions by child alias
  const { childGroups, totalPendingInr, overlappingDeadlines } = useMemo(() => {
    const groups: Record<string, SchoolAction[]> = {
      Kavya: [],
      Arun: [],
    };
    let pendingInr = 0;
    const deadlineChildrenMap: Record<string, Set<string>> = {};

    actions.forEach((act) => {
      const notice = noticeMap.get(act.notice_id);
      const child = notice?.child_alias || 'Kavya';
      if (!groups[child]) {
        groups[child] = [];
      }
      groups[child].push(act);

      if (act.status === 'draft' && act.amount) {
        pendingInr += act.amount;
      }

      // Check for deadline overlap across children
      const deadlineDate = act.normalized_due_date ? act.normalized_due_date.slice(0, 10) : null;
      if (deadlineDate && act.status !== 'completed') {
        if (!deadlineChildrenMap[deadlineDate]) {
          deadlineChildrenMap[deadlineDate] = new Set<string>();
        }
        deadlineChildrenMap[deadlineDate].add(child);
      }
    });

    // Detect overlapping dates with multiple children
    const overlaps: { date: string; children: string[] }[] = [];
    Object.entries(deadlineChildrenMap).forEach(([date, childSet]) => {
      if (childSet.size > 1) {
        overlaps.push({ date, children: Array.from(childSet) });
      }
    });

    return {
      childGroups: groups,
      totalPendingInr: pendingInr,
      overlappingDeadlines: overlaps,
    };
  }, [actions, noticeMap]);

  const handleDownloadFullCalendar = () => {
    const link = document.createElement('a');
    link.href = '/api/actions/calendar.ics';
    link.setAttribute('download', 'schoolbag_family_schedule.ics');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Board Header & Calendar Feed Export */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, #eff6ff, #f8fafc)',
          border: '1px solid #bfdbfe',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          padding: '1rem 1.25rem',
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#1e3a8a', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Calendar size={20} color="#2563eb" />
            Family Weekly Board (Visual School Diary)
          </h3>
          <p style={{ fontSize: '0.8rem', color: '#475569', marginTop: '0.15rem' }}>
            Multi-child consolidated schedule for Kovai Vidya Mandir parents.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {totalPendingInr > 0 && (
            <div style={{ fontSize: '0.8rem', background: '#e0f2fe', color: '#0369a1', padding: '0.35rem 0.65rem', borderRadius: 'var(--radius-sm)', fontWeight: 600 }}>
              Pending Fees: ₹{totalPendingInr.toLocaleString('en-IN')} INR
            </div>
          )}

          <button
            onClick={handleDownloadFullCalendar}
            className="btn btn-primary"
            style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
            title="Download complete family iCalendar (.ics) feed"
          >
            <Download size={14} /> Export Family Calendar (.ics)
          </button>
        </div>
      </div>

      {/* Family Deadline Overlap Alert */}
      {overlappingDeadlines.length > 0 && (
        <div
          className="banner-warning"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.6rem',
            background: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px', color: '#d97706' }} />
          <div>
            <strong>Family Deadline Overlap Detected:</strong>
            <p style={{ fontSize: '0.8rem', marginTop: '0.2rem' }}>
              Multiple children have concurrent obligations on the same day:
              {' '}
              {overlappingDeadlines.map((o) => `${o.children.join(' & ')} on ${o.date}`).join(', ')}.
              Please coordinate payments and travel logistics in advance.
            </p>
          </div>
        </div>
      )}

      {/* Multi-Child Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
        {Object.entries(childGroups).map(([childName, childActions]) => (
          <div
            key={childName}
            className="card"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
            }}
          >
            {/* Child Column Header */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingBottom: '0.75rem',
                borderBottom: '2px solid #e2e8f0',
                marginBottom: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <div style={{ background: childName === 'Kavya' ? '#dbeafe' : '#fef3c7', padding: '0.35rem', borderRadius: '50%', color: childName === 'Kavya' ? '#1d4ed8' : '#b45309' }}>
                  <User size={16} />
                </div>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {childName}
                  </h4>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {childName === 'Kavya' ? 'Class 5-B' : 'Class 8-A'}
                  </span>
                </div>
              </div>

              <span className="badge" style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.72rem' }}>
                {childActions.length} Actions
              </span>
            </div>

            {/* Actions List for this child */}
            {childActions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                No active actions for {childName}.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {childActions.map((action) => (
                  <ActionCard
                    key={action.id}
                    action={action}
                    onActionUpdated={onActionUpdated}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
