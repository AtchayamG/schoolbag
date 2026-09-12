import { Shield } from 'lucide-react';
import { HealthResponse } from '../types/schoolbag';

interface ProvenanceCardProps {
  health: HealthResponse | null;
}

export const ProvenanceCard: React.FC<ProvenanceCardProps> = ({ health }) => {
  return (
    <div className="card" style={{ marginTop: '1.5rem', background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-primary)', fontWeight: 700, fontSize: '0.875rem', marginBottom: '0.5rem' }}>
        <Shield size={16} /> Truthful Provenance & Safety Declarations
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Extraction Engine</div>
          <div>Mode: <code>{health?.extractor.mode || 'deterministic'}</code> (Rule-based)</div>
          <div>Advisory Only: <code>true</code> (No autosigning)</div>
        </div>

        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Synthetic Public Domain Context</div>
          <div>Location: Kovai Vidya Mandir, Coimbatore, TN</div>
          <div>Spend: <strong>₹0.00 / $0.00</strong> (Zero paid cloud APIs)</div>
        </div>

        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Child Privacy Protection</div>
          <div>Identifiers: <strong>Alias Only</strong> (e.g. Kavya, Arun)</div>
          <div>Excluded: No DOB, No Medical, No Student IDs</div>
        </div>

        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Authority Boundary</div>
          <div>Enforcement: <strong>HTTP 403 Human Gate</strong></div>
          <div>Audit Log: Append-only with version concurrency</div>
        </div>
      </div>
    </div>
  );
};
