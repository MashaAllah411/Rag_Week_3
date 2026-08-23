// ============================================================
// app.js — HR Policy RAG  Week 4 M2 Frontend
// Vanilla JS — no frameworks, no build step
// ============================================================

const API = '';   // Same origin (FastAPI serves this file)
let selectedDocumentName = null;

// ── Tab Navigation ────────────────────────────────────────
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
    if (tab.dataset.panel === 'panel-dashboard') loadDashboard();
    if (tab.dataset.panel === 'panel-failures')  loadFailures();
    if (tab.dataset.panel === 'panel-documents') loadDocuments();
  });
});

// ── Range Sliders ─────────────────────────────────────────
document.querySelectorAll('input[type="range"]').forEach(slider => {
  const valueEl = document.getElementById(slider.id + '-val');
  const update = () => {
    if (valueEl) valueEl.textContent = slider.value;
    const pct = ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
    slider.style.setProperty('--pct', pct + '%');
  };
  slider.addEventListener('input', update);
  update();
});

// ── Loading overlay ───────────────────────────────────────
const loadingOverlay = document.getElementById('loading-overlay');
let loadingMsg = document.getElementById('loading-msg');

function showLoading(msg = 'Running RAG pipeline…') {
  if (loadingMsg) loadingMsg.textContent = msg;
  loadingOverlay.classList.add('active');
}
function hideLoading() { loadingOverlay.classList.remove('active'); }

// ── Toast notifications ───────────────────────────────────
function toast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── ASK Panel ─────────────────────────────────────────────
document.getElementById('ask-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const question = document.getElementById('question-input').value.trim();
  if (!question) { toast('Please enter a question.', 'error'); return; }

  const mode       = document.querySelector('input[name="mode"]:checked')?.value || 'hybrid';
  const topK       = parseInt(document.getElementById('top-k').value);
  const threshold  = parseFloat(document.getElementById('threshold').value);
  const useRewrite = document.getElementById('use-rewriter').checked;

  showLoading(`Running ${mode} pipeline…`);
  clearResults();

  try {
    const resp = await fetch(`${API}/api/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        mode,
        top_k: topK,
        similarity_threshold: threshold,
        use_query_rewriter: useRewrite,
        document_name: selectedDocumentName,
      }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    renderResults(data);
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });

  } catch (err) {
    toast(`Error: ${err.message}`, 'error', 6000);
    console.error(err);
  } finally {
    hideLoading();
  }
});

function clearResults() {
  document.getElementById('results-section').classList.add('hidden');
  document.getElementById('answer-text').textContent = '';
  document.getElementById('chunks-container').innerHTML = '';
  document.getElementById('pipeline-steps-list').innerHTML = '';
  document.getElementById('rewrite-pill').classList.add('hidden');
}

function renderResults(data) {
  const section = document.getElementById('results-section');
  section.classList.remove('hidden');

  // Query rewrite pill
  if (data.rewritten_query) {
    const pill = document.getElementById('rewrite-pill');
    pill.classList.remove('hidden');
    document.getElementById('rewrite-original').textContent = data.question;
    document.getElementById('rewrite-new').textContent      = data.rewritten_query;
  }

  // Answer
  document.getElementById('answer-text').textContent = data.answer;
  document.getElementById('answer-mode').textContent  = modeLabel(data.mode);
  document.getElementById('answer-source').textContent = data.source_document;

  // Confidence
  const confEl = document.getElementById('answer-confidence');
  confEl.textContent  = data.confidence.toUpperCase();
  confEl.className    = `confidence-${data.confidence}`;

  // Chunk count
  document.getElementById('chunk-count').textContent = `${data.retrieved_chunks.length} chunks retrieved`;

  // Chunks
  const container = document.getElementById('chunks-container');
  data.retrieved_chunks.forEach((chunk, i) => {
    container.appendChild(buildChunkCard(chunk, i + 1));
  });

  // Pipeline steps
  const stepsList = document.getElementById('pipeline-steps-list');
  data.pipeline_steps.forEach((step, i) => {
    const div = document.createElement('div');
    div.className = 'pipeline-step';
    div.innerHTML = `<span class="step-number">${i + 1}</span><span>${step}</span>`;
    stepsList.appendChild(div);
  });
}

function buildChunkCard(chunk, rank) {
  const card = document.createElement('div');
  card.className = 'chunk-card';

  const scoreDisplay = chunk.rerank_score != null
    ? `<span class="score-pill score-rerank">⚡ Rerank: ${chunk.rerank_score.toFixed(4)}</span>`
    : `<span class="score-pill score-main">◈ Score: ${chunk.score.toFixed(4)}</span>`;

  const ranks = [];
  if (chunk.semantic_rank != null) ranks.push(`<span class="score-pill score-main" title="Semantic rank">↑ Sem: #${chunk.semantic_rank}</span>`);
  if (chunk.bm25_rank     != null) ranks.push(`<span class="score-pill score-bm25" title="BM25 rank">🔤 BM25: #${chunk.bm25_rank}</span>`);

  const short = chunk.text.slice(0, 300).replace(/</g, '&lt;');
  const full  = chunk.text.replace(/</g, '&lt;');
  const hasMore = chunk.text.length > 300;

  card.innerHTML = `
    <div class="chunk-header">
      <div class="flex items-center gap-2">
        <div class="chunk-rank-badge">${rank}</div>
        <span class="chunk-id">${chunk.chunk_id}</span>
      </div>
      <div class="chunk-scores">${scoreDisplay}${ranks.join('')}</div>
    </div>
    <div class="chunk-text" id="chunk-text-${rank}">${short}${hasMore ? '…' : ''}</div>
    ${hasMore ? `<button class="chunk-expand-btn" id="chunk-btn-${rank}" onclick="toggleChunk(${rank}, ${JSON.stringify(full).replace(/"/g, '&quot;')})">
      ▼ Show more
    </button>` : ''}
  `;
  return card;
}

function toggleChunk(rank, fullText) {
  const el  = document.getElementById(`chunk-text-${rank}`);
  const btn = document.getElementById(`chunk-btn-${rank}`);
  if (el.classList.contains('expanded')) {
    el.classList.remove('expanded');
    el.innerHTML = fullText.slice(0, 300) + '…';
    btn.textContent = '▼ Show more';
  } else {
    el.classList.add('expanded');
    el.innerHTML = fullText;
    btn.textContent = '▲ Show less';
  }
}

function modeLabel(mode) {
  return { semantic: 'Semantic', hybrid: 'Hybrid (RRF)', reranked: 'Reranked + MMR' }[mode] || mode;
}

// ── Dashboard Panel ───────────────────────────────────────
async function loadDashboard() {
  try {
    const resp = await fetch(`${API}/api/evaluate/metrics`);
    const data = await resp.json();
    renderMetrics(data);
  } catch (e) {
    console.error('Failed to load metrics:', e);
    toast('Could not load metrics.', 'error');
  }
}

function renderMetrics(data) {
  const b = data.before;
  const a = data.after;

  // Before
  document.getElementById('b-hit').textContent  = (b.hit_rate * 100).toFixed(0) + '%';
  document.getElementById('b-mrr').textContent  = b.mrr.toFixed(2);
  document.getElementById('b-recall').textContent = b.recall.toFixed(2);

  // After
  document.getElementById('a-hit').textContent  = (a.hit_rate * 100).toFixed(0) + '%';
  document.getElementById('a-mrr').textContent  = a.mrr.toFixed(2);
  document.getElementById('a-recall').textContent = a.recall.toFixed(2);

  // Delta
  const hitDelta = Math.round(data.improvement.hit_rate_delta * 100);
  const mrrDelta = (data.improvement.mrr_delta * 100).toFixed(0);
  document.getElementById('delta-hit').textContent = `+${hitDelta}% Hit-Rate@3`;
  document.getElementById('delta-mrr').textContent = `+${mrrDelta}% MRR`;

  // Improvement box
  document.getElementById('one-change-desc').textContent = data.improvement.one_change_made;

  // Fixed / still failing tags
  const fixedContainer  = document.getElementById('fixed-tags');
  const failingContainer = document.getElementById('failing-tags');
  fixedContainer.innerHTML  = '';
  failingContainer.innerHTML = '';

  (data.improvement.fixed_questions || []).forEach(q => {
    const t = document.createElement('span');
    t.className = 'tag fixed';
    t.textContent = '✓ ' + q.slice(0, 50) + (q.length > 50 ? '…' : '');
    fixedContainer.appendChild(t);
  });

  (data.improvement.still_failing || []).forEach(q => {
    const t = document.createElement('span');
    t.className = 'tag broken';
    t.textContent = '✗ ' + q.slice(0, 50) + (q.length > 50 ? '…' : '');
    failingContainer.appendChild(t);
  });

  // Load per-question table
  loadEvalTable('hybrid');
}

async function loadEvalTable(mode) {
  try {
    const resp = await fetch(`${API}/api/evaluate/results/${mode}`);
    const data = await resp.json();
    renderEvalTable(data, mode);
  } catch (e) {
    console.error(`Failed to load eval table for ${mode}:`, e);
  }
}

function renderEvalTable(data, mode) {
  const tbody = document.getElementById('eval-tbody');
  tbody.innerHTML = '';

  data.per_question.forEach(pq => {
    const tr = document.createElement('tr');
    const hitBadge = pq.hit
      ? '<span class="hit-badge hit">✓ HIT</span>'
      : '<span class="hit-badge miss">✗ MISS</span>';

    const effectiveLabel = pq.failure_type || (pq.hit ? 'pass' : 'retrieval_failure');
    const labelBadge = failureBadgeHtml(effectiveLabel);

    tr.innerHTML = `
      <td class="failure-question">${pq.question}</td>
      <td>${hitBadge}</td>
      <td class="font-mono" style="font-size:12px;">${pq.reciprocal_rank.toFixed(2)}</td>
      <td class="font-mono" style="font-size:12px;">${pq.retrieved_ids.slice(0,3).join(', ')}</td>
      <td class="font-mono" style="font-size:11px;color:var(--accent-secondary)">${pq.relevant_chunks.join(', ')}</td>
      <td>${labelBadge}</td>
    `;
    tbody.appendChild(tr);
  });
}

function failureBadgeHtml(label) {
  const map = {
    retrieval_failure: ['retrieval', '⚠ Retrieval Failure'],
    generation_failure: ['generation', '⚡ Generation Failure'],
    pass: ['pass', '✓ Pass'],
  };
  const [cls, text] = map[label] || ['pass', label];
  return `<span class="failure-badge ${cls}">${text}</span>`;
}

// Eval mode toggle
document.querySelectorAll('.eval-mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.eval-mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadEvalTable(btn.dataset.mode);
  });
});

// ── Failures Panel ────────────────────────────────────────
async function loadFailures() {
  const container = document.getElementById('failures-container');
  container.innerHTML = '<div class="skeleton" style="height:120px;"></div>';

  try {
    const resp = await fetch(`${API}/api/failures`);
    const data = await resp.json();
    renderFailures(data.failures);
  } catch (e) {
    console.error(e);
    container.innerHTML = '<p class="text-muted">Failed to load failures data.</p>';
  }
}

function renderFailures(failures) {
  const container = document.getElementById('failures-container');
  container.innerHTML = '';

  failures.forEach(item => {
    const isBaseMiss = item.baseline.hit === 0;
    const isHybMiss  = item.hybrid.hit   === 0;
    if (!isBaseMiss && !isHybMiss) return;   // Only show failures

    const card = document.createElement('div');
    card.className = 'card mt-4';
    card.style.marginBottom = '16px';

    card.innerHTML = `
      <div style="margin-bottom:14px;">
        <div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:6px;">${item.question}</div>
        <div class="text-muted">${item.notes}</div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;">
        <div style="padding:14px;border-radius:10px;background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.2);">
          <div style="font-size:11px;font-weight:700;color:var(--accent-red);letter-spacing:1px;margin-bottom:8px;">BASELINE (Semantic)</div>
          ${buildCompareBlock(item.baseline)}
        </div>
        <div style="padding:14px;border-radius:10px;background:rgba(52,211,153,0.04);border:1px solid rgba(52,211,153,0.15);">
          <div style="font-size:11px;font-weight:700;color:var(--accent-green);letter-spacing:1px;margin-bottom:8px;">HYBRID (BM25 + RRF)</div>
          ${buildCompareBlock(item.hybrid)}
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
        <div>
          <span style="font-size:11px;color:var(--text-muted);margin-right:8px;">EFFECTIVE LABEL:</span>
          ${failureBadgeHtml(item.effective_label)}
        </div>
        ${item.human_evidence ? `<div style="font-size:12px;color:var(--text-secondary);font-style:italic;max-width:500px;">"${item.human_evidence}"</div>` : ''}
        <div style="display:flex;align-items:center;gap:8px;margin-left:auto;">
          <select class="label-select" data-question="${encodeURIComponent(item.question)}">
            <option value="retrieval_failure"  ${item.effective_label==='retrieval_failure' ?'selected':''}>⚠ Retrieval Failure</option>
            <option value="generation_failure" ${item.effective_label==='generation_failure'?'selected':''}>⚡ Generation Failure</option>
            <option value="pass"               ${item.effective_label==='pass'              ?'selected':''}>✓ Pass</option>
          </select>
          <button class="chunk-expand-btn" onclick="saveLabel(this)" style="background:var(--bg-input);border:1px solid var(--border);padding:5px 12px;border-radius:6px;cursor:pointer;color:var(--accent-secondary);font-size:12px;">Save Label</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });

  if (container.children.length === 0) {
    container.innerHTML = '<p class="text-muted" style="padding:20px;">No retrieval failures found — all questions hit on both modes!</p>';
  }
}

function buildCompareBlock(result) {
  const hitBadge = result.hit ? '<span class="hit-badge hit">✓ HIT</span>' : '<span class="hit-badge miss">✗ MISS</span>';
  return `
    <div>${hitBadge}</div>
    <div style="margin-top:8px;font-size:11px;color:var(--text-secondary);">
      Retrieved: <span class="font-mono" style="color:var(--accent-secondary)">${result.retrieved.join(', ') || '—'}</span>
    </div>
    <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
      RR: ${result.reciprocal_rank.toFixed(2)} | Recall: ${result.recall.toFixed(2)}
    </div>
  `;
}

async function saveLabel(btn) {
  const parent = btn.closest('[data-question], div');
  const selectEl = btn.previousElementSibling;
  const question = decodeURIComponent(selectEl.dataset.question);
  const label    = selectEl.value;

  try {
    const resp = await fetch(`${API}/api/failures/label`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, label }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    toast('Label saved!', 'success');
  } catch (e) {
    toast(`Failed to save: ${e.message}`, 'error');
  }
}

// ── Documents Panel & Dynamic UI ──────────────────────────
async function initDocumentContext() {
  try {
    const resp = await fetch(`${API}/api/documents`);
    if (!resp.ok) return;
    const data = await resp.json();

    const activeDoc = data.active_document || (data.documents && data.documents[0]);
    if (!activeDoc) return;

    // Update Header Badge
    const badgeEl = document.getElementById('header-doc-badge');
    if (badgeEl) {
      badgeEl.textContent = activeDoc.badge || activeDoc.title || activeDoc.filename;
    }

    // Update Subtitle & Page Title
    const subEl = document.getElementById('header-subtitle');
    if (subEl) {
      subEl.textContent = `Week 4 · M2 — Retrieval & RAG · ${activeDoc.title} Assistant`;
    }
    const titleEl = document.getElementById('page-title');
    if (titleEl) {
      titleEl.textContent = `RAG Debugger — Week 4 M2 | ${activeDoc.title} Assistant`;
    }

    // Update Quick Questions if available
    const questionsContainer = document.getElementById('quick-questions-container');
    if (questionsContainer && activeDoc.suggested_questions && activeDoc.suggested_questions.length > 0) {
      questionsContainer.innerHTML = '';
      activeDoc.suggested_questions.forEach(q => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chunk-expand-btn';
        btn.style.cssText = 'border:1px solid var(--border);padding:5px 12px;border-radius:6px;background:var(--bg-input);cursor:pointer;';
        btn.textContent = q.label;
        btn.addEventListener('click', () => setQuestion(q.query));
        questionsContainer.appendChild(btn);
      });

      // Update Input Placeholder
      const inputEl = document.getElementById('question-input');
      if (inputEl) {
        inputEl.placeholder = `e.g. ${activeDoc.suggested_questions[0].query}`;
      }
    }
  } catch (err) {
    console.warn('Could not initialize document context dynamically:', err);
  }
}

async function loadDocuments() {
  const container = document.getElementById('documents-container');
  container.innerHTML = '<div class="skeleton" style="height:80px;"></div>';

  try {
    const resp = await fetch(`${API}/api/documents`);
    const data = await resp.json();

    container.innerHTML = '';
    data.documents.forEach(doc => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.marginBottom = '14px';
      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="font-size:32px;">📄</div>
          <div style="flex:1">
            <div style="font-size:16px;font-weight:600;color:var(--text-primary);">${doc.title || doc.filename}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px;">
              ${doc.filename} · ${doc.size_kb} KB ${doc.pages ? `· ${doc.pages} pages` : ''}
            </div>
          </div>
          <div style="text-align:right;">
            <span class="confidence-high">${doc.status}</span>
            <button class="chunk-expand-btn document-use-btn" style="display:block;margin-top:8px;" data-document-name="${doc.filename}">Use for query</button>
            <button class="chunk-expand-btn document-delete-btn" style="display:block;margin-top:8px;color:var(--accent-red);" data-delete-document="${doc.filename}">Delete document</button>
          </div>
        </div>
        <div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
          <div style="font-size:12px;color:var(--text-secondary);">
            <div class="text-muted">Vector Index</div>
            <div class="font-mono" style="font-size:11px;color:var(--accent-secondary);margin-top:4px;">${doc.vector_index}</div>
          </div>
          <div style="font-size:12px;color:var(--text-secondary);">
            <div class="text-muted">Embedding Model</div>
            <div class="font-mono" style="font-size:11px;color:var(--accent-cyan);margin-top:4px;">${doc.embedding_model}</div>
          </div>
          <div style="font-size:12px;color:var(--text-secondary);">
            <div class="text-muted">Chunking</div>
            <div style="font-size:11px;color:var(--accent-amber);margin-top:4px;">${doc.chunking_strategy}</div>
          </div>
        </div>
      `;
      card.querySelector('[data-document-name]').addEventListener('click', () => {
        selectedDocumentName = selectedDocumentName === doc.filename ? null : doc.filename;
        toast(selectedDocumentName ? `Questions will use: ${doc.title || doc.filename}` : 'Questions will search all documents.', 'success');
        updateDocumentSelectionButtons();
      });
      card.querySelector('[data-delete-document]').addEventListener('click', () => deleteDocument(doc.filename));
      container.appendChild(card);
    });

    if (data.documents.length === 0) {
      container.innerHTML = '<p class="text-muted">No documents indexed yet.</p>';
    }
    updateDocumentSelectionButtons();
  } catch (e) {
    container.innerHTML = '<p class="text-muted">Failed to load documents.</p>';
    console.error(e);
  }
}

function updateDocumentSelectionButtons() {
  document.querySelectorAll('.document-use-btn').forEach(button => {
    const selected = button.dataset.documentName === selectedDocumentName;
    button.textContent = selected ? '✓ Used for query' : 'Use for query';
    button.style.background = selected ? 'var(--accent-green)' : 'var(--bg-input)';
    button.style.color = selected ? '#062b1e' : 'var(--accent-secondary)';
    button.style.borderColor = selected ? 'var(--accent-green)' : 'var(--border)';
  });
}

async function deleteDocument(filename) {
  if (!confirm(`Delete ${filename} and all of its indexed chunks? This cannot be undone.`)) return;
  try {
    const response = await fetch(`${API}/api/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Delete failed');
    if (selectedDocumentName === filename) selectedDocumentName = null;
    toast(`${filename} and its indexed chunks were removed.`, 'success');
    await loadDocuments();
  } catch (error) {
    toast(`Delete failed: ${error.message}`, 'error', 6000);
  }
}

document.getElementById('document-upload-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.getElementById('document-file-input');
  const file = input.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await fetch(`${API}/api/documents/upload`, { method: 'POST', body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Upload failed');
    selectedDocumentName = data.filename;
    toast(`${data.filename} uploaded. Indexing started; wait briefly before asking.`, 'success', 6000);
    input.value = '';
    setTimeout(loadDocuments, 1000);
  } catch (error) {
    toast(`Upload failed: ${error.message}`, 'error', 6000);
  }
});

// ── Init ──────────────────────────────────────────────────
(async function init() {
  await initDocumentContext();
  await loadDashboard();
})();
