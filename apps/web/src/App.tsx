import React, { useEffect, useState, useCallback } from 'react';
import { api } from './api/client';
import { Header } from './components/Header';
import { NoticeList } from './components/NoticeList';
import { ActionList } from './components/ActionList';
import { AuditEventStream } from './components/AuditEventStream';
import { NoticeIntakeModal } from './components/NoticeIntakeModal';
import { ProvenanceCard } from './components/ProvenanceCard';
import { FamilyWeeklyBoard } from './components/FamilyWeeklyBoard';
import {
  AuditEvent,
  HealthResponse,
  Notice,
  SchoolAction,
  SchoolPreset,
  Workspace,
} from './types/schoolbag';

export const App: React.FC = () => {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [presets, setPresets] = useState<SchoolPreset[]>([]);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [actions, setActions] = useState<SchoolAction[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [selectedNotice, setSelectedNotice] = useState<Notice | null>(null);
  const [selectedChild, setSelectedChild] = useState<string | null>(null);
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'feed' | 'board'>('feed');

  // Initialize or load workspace
  const initWorkspace = useCallback(async () => {
    try {
      let currentWs: Workspace;
      try {
        currentWs = await api.getCurrentWorkspace();
      } catch {
        currentWs = await api.createWorkspace('Demo Family Workspace');
      }
      setWorkspace(currentWs);
    } catch (err) {
      console.error('Failed to initialize workspace:', err);
    }
  }, []);

  // Fetch all state
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [healthData, presetsData, noticesData, actionsData, auditData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getPresets().catch(() => []),
        api.getNotices(selectedChild || undefined).catch(() => []),
        api.getActions().catch(() => []),
        api.getAuditEvents().catch(() => []),
      ]);

      if (healthData) setHealth(healthData);
      setPresets(presetsData);
      setNotices(noticesData);
      setAuditEvents(auditData);

      // Filter actions by selected notice if applicable
      if (selectedNotice) {
        setActions(actionsData.filter((a) => a.notice_id === selectedNotice.id));
      } else {
        // If child filter selected, filter actions by notices belonging to that child
        if (selectedChild) {
          const childNoticeIds = new Set(
            noticesData.filter((n) => n.child_alias === selectedChild).map((n) => n.id)
          );
          setActions(actionsData.filter((a) => childNoticeIds.has(a.notice_id)));
        } else {
          setActions(actionsData);
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedChild, selectedNotice]);

  useEffect(() => {
    initWorkspace();
  }, [initWorkspace]);

  useEffect(() => {
    if (workspace) loadData();
  }, [loadData, workspace]);

  return (
    <div className="app-container">
      <Header
        workspace={workspace}
        health={health}
        noticeCount={notices.length}
        selectedChild={selectedChild}
        onSelectChild={(child) => {
          setSelectedChild(child);
          setSelectedNotice(null);
        }}
        onOpenIntake={() => setIsIntakeOpen(true)}
        onRefresh={loadData}
        isLoading={isLoading}
      />

      {/* View Switcher Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          marginTop: '1rem',
          marginBottom: '1rem',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.6rem',
        }}
      >
        <button
          type="button"
          className={`btn ${viewMode === 'feed' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setViewMode('feed')}
          style={{ fontSize: '0.85rem' }}
          data-testid="tab-feed-view"
        >
          Feed & Action View
        </button>
        <button
          type="button"
          className={`btn ${viewMode === 'board' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setViewMode('board')}
          style={{ fontSize: '0.85rem' }}
          data-testid="tab-board-view"
        >
          Family Weekly Board (Visual Diary)
        </button>
      </div>

      {viewMode === 'feed' ? (
        <main className="grid-layout">
          {/* Left Column: Notice Feed */}
          <NoticeList
            notices={notices}
            selectedNotice={selectedNotice}
            onSelectNotice={(n) => setSelectedNotice(n)}
          />

          {/* Center Column: Actions */}
          <ActionList
            actions={actions}
            onActionUpdated={loadData}
            filterChildName={selectedChild}
          />

          {/* Right Column: Audit Log */}
          <AuditEventStream events={auditEvents} />
        </main>
      ) : (
        <main style={{ marginTop: '0.5rem', marginBottom: '1.5rem' }}>
          <FamilyWeeklyBoard
            actions={actions}
            notices={notices}
            onActionUpdated={loadData}
          />
        </main>
      )}

      {/* Footer Provenance and Security Disclosures */}
      <ProvenanceCard health={health} />

      {/* Intake Modal */}
      <NoticeIntakeModal
        isOpen={isIntakeOpen}
        onClose={() => setIsIntakeOpen(false)}
        onNoticeCreated={loadData}
        presets={presets}
      />
    </div>
  );
};
