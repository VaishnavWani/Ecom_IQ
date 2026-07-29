// frontend/js/app.js
// Main application logic

let historyList = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Configure marked if available
  if (window.marked) {
    marked.setOptions({ breaks: true, gfm: true });
  }

  const queryInput = document.getElementById('queryInput');
  const sendBtn = document.getElementById('sendBtn');
  
  // Event listeners
  queryInput.addEventListener('input', () => autoResize(queryInput));
  
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  sendBtn.addEventListener('click', handleSend);

  // Setup history clicks (delegated)
  document.getElementById('historyList')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('history-item')) {
      const allItems = document.querySelectorAll('.history-item');
      allItems.forEach(el => el.classList.remove('active'));
      e.target.classList.add('active');
    }
  });

  // Setup chip clicks (global so inline handlers work)
  window.sendQuery = async function(text) {
    const input = document.getElementById('queryInput');
    if (text) {
      input.value = text;
    }
    await handleSend();
  };
  
  // Expose new chat functionality globally
  window.newChat = function() {
    const msgs = document.getElementById('messages');
    msgs.innerHTML = `
      <div class="welcome" id="welcome">
        <div class="welcome-orb" style="width:88px;height:88px;border-radius:26px;background:linear-gradient(135deg,rgba(79,216,232,0.2),rgba(139,124,246,0.2));border:1px solid rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;box-shadow:0 0 50px rgba(79,216,232,0.25),inset 0 1px 0 rgba(255,255,255,0.2);font-size:32px;">✦</div>
        <div>
          <h1>EcomIQ Intelligence</h1>
          <div class="welcome-sub">Real-time · Kafka → Spark → PostgreSQL</div>
        </div>
        <div class="quick-chips">
          <button class="chip" onclick="handleChipClick('Why are payments failing?')">⚡ Why are payments failing?</button>
          <button class="chip" onclick="handleChipClick('Which courier has the best performance?')">🚚 Which courier has the best performance?</button>
          <button class="chip" onclick="handleChipClick('Which SKUs have the most returns?')">📦 Which SKUs have the most returns?</button>
          <button class="chip" onclick="handleChipClick('Are there any operational anomalies?')">📉 Are there any operational anomalies?</button>
        </div>
      </div>
    `;
    // Re-animate chips
    if (window.gsap) {
      gsap.fromTo('.chip', { y:16, opacity:0 }, { y:0, opacity:1, duration:0.45, ease:'power3.out', stagger:0.07, clearProps:'transform' });
    }
  };
});

async function handleSend() {
  const input = document.getElementById('queryInput');
  const sendBtn = document.getElementById('sendBtn');
  const query = input.value.trim();

  if (!query) return;

  // UI Updates before sending
  removeWelcomeScreen();
  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;

  // Add to history
  const histEntry = query.length > 35 ? query.slice(0, 35) + '…' : query;
  historyList.unshift(histEntry);
  renderHistory(historyList);

  appendUserMessage(query);
  const typingId = showTypingIndicator();

  // API Call
  try {
    const data = await fetchInvestigation(query);
    advanceTypingStep(typingId, 3);
    removeTypingIndicator(typingId);
    appendAIResponse(data);
  } catch (error) {
    removeTypingIndicator(typingId);
    appendError(error.message || 'Could not reach the AI Engine.');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}
