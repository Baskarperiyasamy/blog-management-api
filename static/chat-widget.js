/**
 * chat-widget.js — a self-contained AI Support Chat bubble.
 *
 * Usage: add this one line before </body> on ANY page of the site:
 *   <script src="/static/chat-widget.js"></script>
 *
 * It injects its own CSS and HTML, so no other setup is needed. It talks
 * to POST /api/ai-support/ (mocked FAQ or OpenAI, decided server-side) and,
 * if a JWT is already saved in sessionStorage under "dashboard_token"
 * (e.g. because the user loaded /static/dashboard.html earlier in this
 * tab), it sends it along so the chat is tied to their account and shows
 * their past history on open. Works fine with no token too - chat still
 * responds, it just isn't tied to a user.
 */
(function () {
  "use strict";

  const API_BASE = window.location.origin;

  // ---------------- Styles ----------------
  const style = document.createElement("style");
  style.textContent = `
    #aichat-root { position: fixed; bottom: 22px; right: 22px; z-index: 9999; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
    #aichat-bubble {
      width: 58px; height: 58px; border-radius: 50%;
      background: #e0a44d; color: #14181f;
      border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 26px;
      box-shadow: 0 8px 24px rgba(0,0,0,.35);
      transition: transform .15s ease;
    }
    #aichat-bubble:hover { transform: scale(1.06); }
    #aichat-bubble .aichat-badge {
      position: absolute; top: -2px; right: -2px;
      width: 12px; height: 12px; border-radius: 50%;
      background: #4fb3a9; border: 2px solid #14181f;
    }
    #aichat-window {
      position: absolute; bottom: 72px; right: 0;
      width: 340px; height: 460px;
      background: #1b2029; border: 1px solid #2a313d; border-radius: 14px;
      box-shadow: 0 16px 48px rgba(0,0,0,.5);
      display: none; flex-direction: column; overflow: hidden;
    }
    #aichat-window.open { display: flex; }
    #aichat-header {
      background: #20262f; padding: 14px 16px; color: #e7e9ee;
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid #2a313d; flex-shrink: 0;
    }
    #aichat-header .title { font-size: 14px; font-weight: 700; }
    #aichat-header .subtitle { font-size: 11px; color: #8a93a3; margin-top: 2px; }
    #aichat-close { background: none; border: none; color: #8a93a3; font-size: 18px; cursor: pointer; line-height: 1; padding: 4px; }
    #aichat-close:hover { color: #e7e9ee; }
    #aichat-messages {
      flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px;
    }
    .aichat-msg { max-width: 82%; padding: 9px 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; }
    .aichat-msg.user { align-self: flex-end; background: #e0a44d; color: #14181f; border-bottom-right-radius: 3px; }
    .aichat-msg.bot { align-self: flex-start; background: #262e3a; color: #e7e9ee; border-bottom-left-radius: 3px; }
    .aichat-msg.typing { align-self: flex-start; background: #262e3a; color: #8a93a3; font-style: italic; }
    #aichat-inputbar {
      display: flex; gap: 8px; padding: 12px; border-top: 1px solid #2a313d; flex-shrink: 0;
    }
    #aichat-input {
      flex: 1; background: #14181f; border: 1px solid #2a313d; color: #e7e9ee;
      border-radius: 8px; padding: 9px 12px; font-size: 13px; resize: none;
      font-family: inherit;
    }
    #aichat-input:focus { outline: none; border-color: #e0a44d; }
    #aichat-send {
      background: #e0a44d; color: #14181f; border: none; border-radius: 8px;
      padding: 0 14px; font-weight: 700; cursor: pointer; font-size: 13px;
    }
    #aichat-send:hover { background: #eab362; }
    #aichat-send:disabled { opacity: .5; cursor: not-allowed; }
    @media (max-width: 420px) {
      #aichat-window { width: calc(100vw - 32px); right: -6px; }
    }
  `;
  document.head.appendChild(style);

  // ---------------- Markup ----------------
  const root = document.createElement("div");
  root.id = "aichat-root";
  root.innerHTML = `
    <div id="aichat-window">
      <div id="aichat-header">
        <div>
          <div class="title">Support Chat</div>
          <div class="subtitle">Ask about posts, billing, dashboard &amp; more</div>
        </div>
        <button id="aichat-close" title="Close">&times;</button>
      </div>
      <div id="aichat-messages"></div>
      <div id="aichat-inputbar">
        <textarea id="aichat-input" rows="1" placeholder="Type a message..."></textarea>
        <button id="aichat-send">Send</button>
      </div>
    </div>
    <button id="aichat-bubble" title="Support chat">💬</button>
  `;
  document.body.appendChild(root);

  const win = document.getElementById("aichat-window");
  const bubble = document.getElementById("aichat-bubble");
  const closeBtn = document.getElementById("aichat-close");
  const messagesEl = document.getElementById("aichat-messages");
  const input = document.getElementById("aichat-input");
  const sendBtn = document.getElementById("aichat-send");

  let opened = false;

  function addMessage(text, who) {
    const el = document.createElement("div");
    el.className = `aichat-msg ${who}`;
    el.textContent = text; // textContent - never render user/API text as HTML
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function getToken() {
    try {
      return sessionStorage.getItem("dashboard_token") || "";
    } catch (e) {
      return "";
    }
  }

  async function loadHistory() {
    const token = getToken();
    if (!token) {
      addMessage("Hi! Ask me about posts, subscriptions, billing, your dashboard, or notifications.", "bot");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/ai-support/history?limit=10`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("history fetch failed");
      const history = await res.json();
      if (history.length === 0) {
        addMessage("Hi! Ask me about posts, subscriptions, billing, your dashboard, or notifications.", "bot");
        return;
      }
      // History comes back newest-first; show it oldest-first like a real thread.
      history.reverse().forEach((h) => {
        addMessage(h.question, "user");
        addMessage(h.ai_response, "bot");
      });
    } catch (e) {
      addMessage("Hi! Ask me about posts, subscriptions, billing, your dashboard, or notifications.", "bot");
    }
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendBtn.disabled = true;
    addMessage(text, "user");

    const typingEl = addMessage("Typing...", "bot typing");

    try {
      const token = getToken();
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/ai-support/`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: text }),
      });
      typingEl.remove();
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      addMessage(data.reply, "bot");
    } catch (err) {
      typingEl.remove();
      addMessage("Sorry, I couldn't reach the server. Please try again.", "bot");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  bubble.addEventListener("click", () => {
    win.classList.toggle("open");
    if (!opened && win.classList.contains("open")) {
      opened = true;
      loadHistory();
    }
  });
  closeBtn.addEventListener("click", () => win.classList.remove("open"));
  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
})();
