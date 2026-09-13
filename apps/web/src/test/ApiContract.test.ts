import { afterEach, expect, it, vi } from 'vitest';
import { api } from '../api/client';

afterEach(() => vi.unstubAllGlobals());

it('exposes extracted actions for review and sends the current version on edits', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify([{ action_id: 'act_1', status: 'extracted', version: 3 }])))
    .mockResolvedValueOnce(new Response(JSON.stringify({ action_id: 'act_1', status: 'extracted', version: 4 })));
  vi.stubGlobal('fetch', fetchMock);
  expect((await api.getActions())[0].status).toBe('draft');
  await api.updateActionDeadline('act_1', 'Friday 5 PM', 3);
  expect(JSON.parse(fetchMock.mock.calls[1][1].body).expected_version).toBe(3);
});

it('maps actual server workspace and preset fields for the dashboard', async () => {
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ workspace_id: 'ws_real', created_at: '2026-09-13', notice_count: 0 })))
    .mockResolvedValueOnce(new Response(JSON.stringify([{ preset_id: 'preset-science-kit', raw_body: 'Bring chart paper', raw_due_text: 'Friday 5 PM', title: 'Science kit', child_alias: 'Kavya', class_name: '5-B', source_type: 'whatsapp' }]))));
  expect((await api.getCurrentWorkspace()).id).toBe('ws_real');
  expect((await api.getPresets())[0]).toMatchObject({ id: 'preset-science-kit', body: 'Bring chart paper', due_date: 'Friday 5 PM' });
});
