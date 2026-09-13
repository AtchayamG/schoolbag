import { afterEach, expect, it, vi } from 'vitest';
import { api } from '../api/client';

afterEach(() => vi.unstubAllGlobals());

it('maps actual server workspace and preset fields for the dashboard', async () => {
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ workspace_id: 'ws_real', created_at: '2026-09-13', notice_count: 0 })))
    .mockResolvedValueOnce(new Response(JSON.stringify([{ preset_id: 'preset-science-kit', raw_body: 'Bring chart paper', raw_due_text: 'Friday 5 PM', title: 'Science kit', child_alias: 'Kavya', class_name: '5-B', source_type: 'whatsapp' }]))));
  expect((await api.getCurrentWorkspace()).id).toBe('ws_real');
  expect((await api.getPresets())[0]).toMatchObject({ id: 'preset-science-kit', body: 'Bring chart paper', due_date: 'Friday 5 PM' });
});
