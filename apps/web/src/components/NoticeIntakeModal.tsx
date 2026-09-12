import React, { useState } from 'react';
import { X, Sparkles, AlertCircle, FileText, CheckCircle } from 'lucide-react';
import { api, ApiError } from '../api/client';
import { SchoolPreset, SourceType } from '../types/schoolbag';

interface NoticeIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNoticeCreated: () => void;
  presets: SchoolPreset[];
}

export const NoticeIntakeModal: React.FC<NoticeIntakeModalProps> = ({
  isOpen,
  onClose,
  onNoticeCreated,
  presets,
}) => {
  const [title, setTitle] = useState('');
  const [rawContent, setRawContent] = useState('');
  const [sourceType, setSourceType] = useState<SourceType>('whatsapp');
  const [childAlias, setChildAlias] = useState('Kavya');
  const [className, setClassName] = useState('Class 5-B');
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleApplyPreset = (preset: SchoolPreset) => {
    setTitle(preset.title);
    setRawContent(preset.body);
    setSourceType(preset.source_type);
    setChildAlias(preset.child_alias);
    setClassName(preset.class_name);
    setErrorMsg(null);
    setSuccessInfo(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !rawContent.trim()) {
      setErrorMsg('Notice title and content are required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    setSuccessInfo(null);

    try {
      const resp = await api.createNotice(
        {
          title: title.trim(),
          raw_content: rawContent.trim(),
          source_type: sourceType,
          child_alias: childAlias.trim() || null,
          class_name: className.trim() || null,
          idempotency_key: idempotencyKey.trim() || null,
        },
        idempotencyKey.trim() || undefined,
      );

      if (resp.deduplicated) {
        setSuccessInfo(`Duplicate notice detected! Replayed existing ${resp.actions.length} action item(s) without duplication.`);
      } else {
        setSuccessInfo(`Successfully ingested notice and extracted ${resp.actions.length} action item(s)!`);
      }

      setTimeout(() => {
        onNoticeCreated();
        onClose();
      }, 1200);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(`[${err.code}] ${err.message}`);
      } else {
        setErrorMsg('Failed to ingest notice. Please check backend connectivity.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Ingest School Communication
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Paste raw school WhatsApp text, email, or circular to extract actions
            </p>
          </div>
          <button onClick={onClose} style={{ color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {/* Synthetic Presets Selector */}
        {presets.length > 0 && (
          <div style={{ background: 'var(--bg-elevated)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-primary)', marginBottom: '0.5rem' }}>
              <Sparkles size={14} /> Quick Synthetic Presets (Kovai Vidya Mandir, Coimbatore)
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {presets.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleApplyPreset(p)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.6rem' }}
                >
                  <FileText size={12} />
                  <span>{p.child_alias}: {p.title.slice(0, 30)}...</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Alerts */}
        {errorMsg && (
          <div className="banner-warning" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successInfo && (
          <div className="banner-success" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} />
            <span>{successInfo}</span>
          </div>
        )}

        {/* Intake Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Child Alias (No DOB/IDs)
              </label>
              <input
                type="text"
                value={childAlias}
                onChange={(e) => setChildAlias(e.target.value)}
                placeholder="e.g. Kavya or Arun"
                style={{ width: '100%' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Class / Section
              </label>
              <input
                type="text"
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                placeholder="e.g. Class 5-B"
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Notice Subject / Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Annual Day Field Trip & Costume Fee"
                style={{ width: '100%' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Source Channel
              </label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value as SourceType)}
                style={{ width: '100%' }}
              >
                <option value="whatsapp">WhatsApp Group</option>
                <option value="circular">School Circular</option>
                <option value="email">Email</option>
                <option value="diary">School Diary</option>
                <option value="portal">Parent Portal</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Raw Communication Text
            </label>
            <textarea
              value={rawContent}
              onChange={(e) => setRawContent(e.target.value)}
              placeholder="Paste raw text here... The deterministic extractor will identify fees, consent slips, materials to bring, and deadlines."
              rows={6}
              style={{ width: '100%', resize: 'vertical' }}
              required
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Optional Idempotency Key (Evaluator Test)
            </label>
            <input
              type="text"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              placeholder="e.g. msg_unique_1001"
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className="btn btn-primary">
              {isSubmitting ? 'Analyzing & Extracting...' : 'Ingest & Extract Actions'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
