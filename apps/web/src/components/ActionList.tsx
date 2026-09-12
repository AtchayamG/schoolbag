import { useState } from 'react';
import { CheckSquare } from 'lucide-react';
import { SchoolAction } from '../types/schoolbag';
import { ActionCard } from './ActionCard';

interface ActionListProps {
  actions: SchoolAction[];
  onActionUpdated: () => void;
  filterChildName?: string | null;
}

export const ActionList: React.FC<ActionListProps> = ({
  actions,
  onActionUpdated,
  filterChildName,
}) => {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredActions = actions.filter((action) => {
    if (statusFilter !== 'all' && action.status !== statusFilter) {
      return false;
    }
    return true;
  });

  const pendingCount = actions.filter((a) => a.status === 'draft').length;
  const approvedCount = actions.filter((a) => a.status === 'approved').length;
  const completedCount = actions.filter((a) => a.status === 'completed').length;

  return (
    <section>
      {/* Title & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckSquare size={20} color="var(--color-primary)" />
            Extracted Family Actions ({filteredActions.length})
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            The essential tasks requiring attention {filterChildName ? `for ${filterChildName}` : 'across all children'}
          </p>
        </div>

        {/* Status Filter Buttons */}
        <div style={{ display: 'flex', gap: '0.35rem', background: 'var(--bg-elevated)', padding: '0.2rem', borderRadius: 'var(--radius-sm)' }}>
          <button
            onClick={() => setStatusFilter('all')}
            className={`btn ${statusFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem' }}
          >
            All ({actions.length})
          </button>
          <button
            onClick={() => setStatusFilter('draft')}
            className={`btn ${statusFilter === 'draft' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem' }}
          >
            Draft ({pendingCount})
          </button>
          <button
            onClick={() => setStatusFilter('approved')}
            className={`btn ${statusFilter === 'approved' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem' }}
          >
            Approved ({approvedCount})
          </button>
          <button
            onClick={() => setStatusFilter('completed')}
            className={`btn ${statusFilter === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem' }}
          >
            Done ({completedCount})
          </button>
        </div>
      </div>

      {filteredActions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-muted)' }}>
          <CheckSquare size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
          <p style={{ fontSize: '0.95rem', fontWeight: 600 }}>No action items match current filter</p>
          <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
            Ingest a notice from WhatsApp or circulars to automatically generate actionable items.
          </p>
        </div>
      ) : (
        <div>
          {filteredActions.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              onActionUpdated={onActionUpdated}
            />
          ))}
        </div>
      )}
    </section>
  );
};
