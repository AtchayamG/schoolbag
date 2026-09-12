import React from 'react';
import { Inbox, Filter } from 'lucide-react';
import { Notice } from '../types/schoolbag';
import { NoticeCard } from './NoticeCard';

interface NoticeListProps {
  notices: Notice[];
  selectedNotice: Notice | null;
  onSelectNotice: (notice: Notice | null) => void;
}

export const NoticeList: React.FC<NoticeListProps> = ({
  notices,
  selectedNotice,
  onSelectNotice,
}) => {
  return (
    <aside>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Inbox size={16} /> Ingested Feed ({notices.length})
        </h3>
        {selectedNotice && (
          <button
            onClick={() => onSelectNotice(null)}
            className="btn btn-secondary"
            style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem' }}
          >
            <Filter size={10} /> Clear Filter
          </button>
        )}
      </div>

      {notices.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
          <Inbox size={32} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
          <p style={{ fontSize: '0.85rem', fontWeight: 500 }}>No notices in this workspace yet</p>
          <p style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
            Click &ldquo;Ingest School Notice&rdquo; above to load a synthetic circular.
          </p>
        </div>
      ) : (
        <div>
          {notices.map((notice) => (
            <NoticeCard
              key={notice.id}
              notice={notice}
              isSelected={selectedNotice?.id === notice.id}
              onSelect={(n) => onSelectNotice(selectedNotice?.id === n.id ? null : n)}
            />
          ))}
        </div>
      )}
    </aside>
  );
};
