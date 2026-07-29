// frontend/js/ui.js
// Handles DOM manipulation and UI states

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

function removeWelcomeScreen() {
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();
}

function appendUserMessage(text) {
  const msgs = document.getElementById('messages');
  const row = document.createElement('div');
  row.className = 'msg-row user';
  row.innerHTML = `
    <div class="msg-avatar user-av">👤</div>
    <div class="user-bubble">${escapeHtml(text)}</div>
  `;
  msgs.appendChild(row);
  scrollToBottom(msgs);
}

function appendAIResponse(data) {
  const msgs = document.getElementById('messages');
  const scope = data.scope_extracted || {};
  const report = data.report || '';

  const scopeHtml = Object.entries(scope).map(([k, v]) =>
    `<div class="scope-chip"><span class="sc-key">${k}:</span>${v}</div>`
  ).join('');

  const row = document.createElement('div');
  row.className = 'msg-row ai';
  row.innerHTML = `
    <div class="msg-avatar ai-av">✦</div>
    <div class="ai-card">
      <div class="ai-card-header">
        <div class="ai-label"><span class="ai-label-dot"></span>EcomIQ Intelligence</div>
        <div class="scope-chips">
          ${scopeHtml || '<div class="scope-chip"><span class="sc-key">scope:</span>all data</div>'}
        </div>
      </div>
      <div class="ai-body">${marked.parse(report)}</div>
    </div>
  `;
  msgs.appendChild(row);
  scrollToBottom(msgs);
}

function appendError(msg) {
  const msgs = document.getElementById('messages');
  const row = document.createElement('div');
  row.className = 'msg-row ai';
  row.innerHTML = `
    <div class="msg-avatar ai-av" style="background: rgba(252,165,165,0.2);">⚠️</div>
    <div class="ai-card" style="border-color: rgba(252,165,165,0.4); max-width: 500px;">
      <div class="ai-body" style="color: #fca5a5;">${escapeHtml(msg)}</div>
    </div>
  `;
  msgs.appendChild(row);
  scrollToBottom(msgs);
}

function scrollToBottom(container) {
  container.scrollTop = container.scrollHeight;
}

/* ── Typing Indicator Logic ───────────────────────────────── */
let typingIdCounter = 0;
const STEPS = ['Extracting scope…', 'Running SQL analytics…', 'Generating report…'];

function showTypingIndicator() {
  const id = ++typingIdCounter;
  const msgs = document.getElementById('messages');

  const stepsHtml = STEPS.map((s, i) =>
    `<div class="typing-step" id="ts-${id}-${i}">
      <div class="step-dot"></div>${s}
    </div>`
  ).join('');

  const row = document.createElement('div');
  row.className = 'msg-row ai';
  row.id = `typing-${id}`;
  row.innerHTML = `
    <div class="msg-avatar ai-av">✦</div>
    <div class="ai-card typing-card" style="max-width: 320px;">
      <div class="typing-header">Investigating space and time…</div>
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
      <div class="typing-steps">${stepsHtml}</div>
    </div>
  `;
  msgs.appendChild(row);
  scrollToBottom(msgs);

  let step = 0;
  activateTypingStep(id, 0);
  const iv = setInterval(() => {
    step++;
    if (step < STEPS.length) activateTypingStep(id, step);
    else clearInterval(iv);
  }, 2500);
  row._interval = iv;

  return id;
}

function advanceTypingStep(id, idx) {
  activateTypingStep(id, idx);
}

function activateTypingStep(id, idx) {
  for (let i = 0; i < STEPS.length; i++) {
    const el = document.getElementById(`ts-${id}-${i}`);
    if (!el) continue;
    if (i < idx)  el.className = 'typing-step done';
    if (i === idx) el.className = 'typing-step active';
    if (i > idx)  el.className = 'typing-step';
  }
}

function removeTypingIndicator(id) {
  const el = document.getElementById(`typing-${id}`);
  if (el) {
    clearInterval(el._interval);
    el.remove();
  }
}

/* ── History Sidebar ─────────────────────────────────────── */
function renderHistory(historyList) {
  const list = document.getElementById('historyList');
  if (!list) return;
  list.innerHTML = historyList.slice(0, 12).map((h, i) =>
    `<div class="history-item ${i === 0 ? 'active' : ''}" data-idx="${i}">${escapeHtml(h)}</div>`
  ).join('');
}
