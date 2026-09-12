import React from 'react';
import { MessageSquare, Mail, FileText, BookOpen, Globe, User, Tag } from 'lucide-react';
import { Notice, SourceType } from '../types/schoolbag';

interface NoticeCardProps {
  notice: Notice;
  isSelected: boolean;
  onSelect: (notice: Notice) => void;
}

const getSourceIcon = (source: SourceType) => {
  switch (source) {
    case 'whatsapp':
      return <MessageSquare size={13} />;
    case 'email':
      return <Mail size={13} />;
    case 'circular':
      return <FileText size={13} />;
    case 'diary':
      return <BookOpen size={13} />;
    case 'portal':
      return <Globe size={13} />;
  }
};

export const NoticeCard: React.FC<NoticeCardProps> = ({ notice, isSelected, onSelect }) => {
  const formattedDate = new Date(notice.created_at).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      onClick={() => onSelect(notice)}
      className="card"
      style={{
        cursor: 'pointer',
        borderColor: isSelected ? 'var(--color-primary)' : 'var(--border-subtle)',
        backgroundColor: isSelected ? '#eff6ff' : 'var(--bg-surface)',
        marginBottom: '0.75rem',
        padding: '0.875rem 1rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
        <span className="badge badge-source" style={{ textTransform: 'capitalize' }}>
          {getSourceIcon(notice.source_type)}
          <span>{notice.source_type}</span>
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formattedDate}</span>
      </div>

      <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
        {notice.title}
      </h4>

      <p style={{
        fontSize: '0.78rem',
        color: 'var(--text-secondary)',
        lineHeight: 1.4,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        marginBottom: '0.5rem',
      }}>
        {notice.raw_content}
      </p>

      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {notice.child_alias && (
          <span style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--color-primary)', background: '#dbeafe', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
            <User size={10} />
            <span>{notice.child_alias}</span>
          </span>
        )}
        {notice.class_name && (
          <span style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--text-secondary)', background: 'var(--bg-elevated)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
            <Tag size={10} />
            <span>{notice.class_name}</span>
          </span>
        )}
      </div>
    </div>
  );
};
