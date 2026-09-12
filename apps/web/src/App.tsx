import React, { useEffect, useState, useCallback } from 'react';
import { api } from './api/client';
import { Header } from './components/Header';
import { NoticeList } from './components/NoticeList';
import { ActionList } from './components/ActionList';
import { AuditEventStream } from './components/AuditEventStream';
import { NoticeIntakeModal } from './components/NoticeIntakeModal';
import { ProvenanceCard } from './components/ProvenanceCard';
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
    loadData();
  }, [loadData]);

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
