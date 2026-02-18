const api = {
  health: '/health',
  renderHealth: 'http://localhost:9000/health',
  stats: '/ops/stats',
  ingest: '/ops/ingest',
  regulations: '/regulations?limit=20',
  changes: '/changes/updated?limit=20',
  search: (q) => `/search?q=${encodeURIComponent(q)}`,
};

const byId = (id) => document.getElementById(id);

async function safeJson(url, options) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function loadHealth() {
  const apiHealth = await safeJson(api.health);
  const renderHealth = await safeJson(api.renderHealth);
  byId('apiHealth').textContent = apiHealth?.status === 'ok' ? 'Çalışıyor' : 'Hata';
  byId('renderHealth').textContent = renderHealth?.status === 'ok' ? 'Çalışıyor' : 'Hata';
}

async function loadStats() {
  const stats = await safeJson(api.stats);
  byId('statTotal').textContent = stats?.total_regulations ?? 0;
  byId('statUpdated').textContent = stats?.updated_regulations ?? 0;
  byId('statStorm').textContent = stats?.storm_urls ?? 0;
  byId('statRender').textContent = stats?.render_enabled ? 'Aktif' : 'Pasif';
}

function fillList(elementId, rows, formatter) {
  const el = byId(elementId);
  el.innerHTML = '';
  if (!rows || rows.length === 0) {
    const li = document.createElement('li');
    li.textContent = 'Kayıt yok.';
    el.appendChild(li);
    return;
  }
  rows.forEach((row) => {
    const li = document.createElement('li');
    li.textContent = formatter(row);
    el.appendChild(li);
  });
}

async function loadRegulations() {
  const rows = await safeJson(api.regulations);
  fillList('regList', rows, (row) => `${row.id} | v${row.version} | ${row.title}`);
}

async function loadChanges() {
  const rows = await safeJson(api.changes);
  fillList('changeList', rows, (row) => `${row.id} | v${row.version} | ${row.title}`);
}

async function runIngest() {
  const seed = byId('seedInput').value.trim();
  byId('ingestResult').textContent = 'Çalışıyor...';
  const result = await safeJson(`${api.ingest}?seed=${encodeURIComponent(seed)}`, { method: 'POST' });
  byId('ingestResult').textContent = JSON.stringify(result ?? { error: 'Ingest başarısız' }, null, 2);
  await refreshAll();
}

async function doSearch() {
  const q = byId('searchInput').value.trim();
  if (!q) return;
  const rows = await safeJson(api.search(q));
  fillList('searchList', rows, (row) => `${row.id} | v${row.version} | ${row.title}`);
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadStats(), loadRegulations(), loadChanges()]);
}

byId('refreshBtn').addEventListener('click', refreshAll);
byId('ingestBtn').addEventListener('click', runIngest);
byId('searchBtn').addEventListener('click', doSearch);

refreshAll();
