import React, { useState } from 'react';
import {
  MessageSquare,
  Mail,
  FileText,
  BookOpen,
  Globe,
  User,
  Tag,
  Sparkles,
  Bot,
  Loader,
  AlertCircle,
  ShieldAlert,
} from 'lucide-react';
import { Notice, SourceType, StrandsAdvisoryResponse } from '../types/schoolbag';
import { api, ApiError } from '../api/client';

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
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [advisory, setAdvisory] = useState<StrandsAdvisoryResponse | null>(null);
  const [advisoryError, setAdvisoryError] = useState<string | null>(null);

  const formattedDate = new Date(notice.created_at).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });

  const handleAnalyzeStrands = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAnalyzing(true);
    setAdvisoryError(null);
    try {
      const noticeId = notice.id || notice.notice_id || '';
      const version = notice.version ?? 1;
      const resp = await api.analyzeNoticeStrands(noticeId, version);
      setAdvisory(resp);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setAdvisoryError(`HTTP ${err.statusCode} - ${err.code}: ${err.message}`);
      } else if (err instanceof Error) {
        setAdvisoryError(err.message);
      } else {
        setAdvisoryError('Failed to analyze notice with Strands AI.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

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

      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.5rem' }}>
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

      {/* Strands AI Action Trigger */}
      <button
        onClick={handleAnalyzeStrands}
        disabled={isAnalyzing}
        className="btn btn-secondary"
        style={{
          fontSize: '0.72rem',
          padding: '0.25rem 0.6rem',
          width: '100%',
          justifyContent: 'center',
          background: '#f8fafc',
          border: '1px solid #cbd5e1',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
        }}
      >
        {isAnalyzing ? (
          <>
            <Loader size={12} className="spin" />
            <span>Analyzing with Strands AI...</span>
          </>
        ) : (
          <>
            <Sparkles size={12} color="#2563eb" />
            <span>Analyze with Strands AI</span>
          </>
        )}
      </button>

      {/* Advisory Error Banner */}
      {advisoryError && (
        <div
          className="banner-warning"
          style={{
            marginTop: '0.5rem',
            padding: '0.4rem 0.6rem',
            fontSize: '0.72rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <AlertCircle size={14} style={{ flexShrink: 0 }} />
          <span>{advisoryError}</span>
        </div>
      )}

      {/* Strands Advisory Result Panel */}
      {advisory && (
        <div
          style={{
            marginTop: '0.6rem',
            padding: '0.65rem',
            background: '#f0fdf4',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #bbf7d0',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#166534', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Bot size={13} />
              <span>Strands Advisory ({advisory.provenance.model || 'openai/gpt-oss-20b'})</span>
            </span>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              padding: '0.1rem 0.35rem',
              borderRadius: '4px',
              background: advisory.is_urgent ? '#fee2e2' : '#dbeafe',
              color: advisory.is_urgent ? '#991b1b' : '#1e40af',
            }}>
              {advisory.is_urgent ? 'Urgent Priority' : 'Standard Priority'}
            </span>
          </div>

          <p style={{ fontSize: '0.75rem', color: '#1e293b', marginBottom: '0.35rem', fontWeight: 500, lineHeight: 1.35 }}>
            {advisory.summary}
          </p>

          {advisory.suggested_actions && advisory.suggested_actions.length > 0 && (
            <div style={{ marginTop: '0.4rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                Suggested Action Drafts ({advisory.suggested_actions.length}):
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {advisory.suggested_actions.map((act, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.4rem 0.5rem',
                      background: '#ffffff',
                      border: '1px solid #cbd5e1',
                      borderRadius: '4px',
                      fontSize: '0.72rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>{act.title}</strong>
                      <span style={{ fontSize: '0.65rem', background: '#f1f5f9', padding: '0.05rem 0.35rem', borderRadius: '3px', fontWeight: 600 }}>
                        {act.category}
                      </span>
                    </div>
                    <div style={{ color: '#64748b', marginTop: '0.15rem' }}>{act.description}</div>
                    <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.25rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      {act.amount_inr != null && (
                        <span style={{ color: '#0369a1', fontWeight: 600 }}>₹{act.amount_inr} INR</span>
                      )}
                      {act.deadline_hint && (
                        <span style={{ color: '#b45309' }}>Due: {act.deadline_hint}</span>
                      )}
                      <span style={{
                        color: '#b91c1c',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        padding: '0.05rem 0.3rem',
                        borderRadius: '3px',
                        fontSize: '0.65rem',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                      }}>
                        <ShieldAlert size={10} />
                        Advisory Draft - Requires Human Parent Approval
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {advisory.advisory_notes && (
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: '#475569', fontStyle: 'italic' }}>
              Note: {advisory.advisory_notes}
            </div>
          )}

          <div style={{
            marginTop: '0.45rem',
            fontSize: '0.66rem',
            color: '#64748b',
            borderTop: '1px dashed #cbd5e1',
            paddingTop: '0.35rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.15rem',
          }}>
            <div>Bounded Tool: <code>get_school_notice_context</code></div>
            <div>Admission Gate: Single-active atomic lock &bull; 6 req/min rate limit &bull; Zero-spend guarantee</div>
          </div>
        </div>
      )}
    </div>
  );
};
