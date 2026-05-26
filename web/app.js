const chat = document.getElementById("chat");
const composerForm = document.getElementById("composerForm");
const messageInput = document.getElementById("messageInput");
const activeChatTitle = document.getElementById("activeChatTitle");
const sessionList = document.getElementById("sessionList");
const micBtn = document.getElementById("micBtn");
const assistantAvatar = document.getElementById("assistantAvatar");
const assistantName = document.getElementById("assistantName");
const assistantGender = document.getElementById("assistantGender");
const userAvatar = document.getElementById("userAvatar");
const userName = document.getElementById("userName");
const userEmail = document.getElementById("userEmail");
const newChatBtn = document.getElementById("newChatBtn");
const clearBtn = document.getElementById("clearBtn");
const exportBtn = document.getElementById("exportBtn");
const logoutBtn = document.getElementById("logoutBtn");
const safetyBanner = document.getElementById("safetyBanner");

const state = {
  sessions: [],
  activeSessionId: null,
  activeAssistantId: null,
  assistantAvatarUrl: "/assets/avatar-default.svg",
  userInitial: "U",
};

function addMessage(role, title, text, meta = {}) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  if (role === "assistant") {
    const img = document.createElement("img");
    img.src = state.assistantAvatarUrl || "/assets/avatar-default.svg";
    img.alt = "Assistant avatar";
    img.className = "avatar-img";
    avatar.appendChild(img);
  } else {
    avatar.textContent = state.userInitial || "U";
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (title) {
    const t = document.createElement("div");
    t.className = "title";
    t.textContent = title;
    bubble.appendChild(t);
  }
  const body = document.createElement("div");
  body.className = "text";
  body.textContent = text;
  bubble.appendChild(body);

  if (meta.time) {
    const time = document.createElement("div");
    time.className = "time";
    time.textContent = meta.time;
    bubble.appendChild(time);
  }

  if (meta.note) {
    const note = document.createElement("div");
    note.className = "note";
    note.textContent = meta.note;
    bubble.appendChild(note);
  }

  message.appendChild(avatar);
  message.appendChild(bubble);
  chat.appendChild(message);
  chat.scrollTop = chat.scrollHeight;
}

function formatTime(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function addDateDivider(label) {
  const divider = document.createElement("div");
  divider.className = "date-divider";
  divider.textContent = label;
  chat.appendChild(divider);
}

function addTypingIndicator() {
  const message = document.createElement("div");
  message.className = "message assistant";
  message.id = "typingIndicator";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const typing = document.createElement("div");
  typing.className = "typing";
  typing.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  bubble.appendChild(typing);

  message.appendChild(avatar);
  message.appendChild(bubble);
  chat.appendChild(message);
  chat.scrollTop = chat.scrollHeight;
}

function removeTypingIndicator() {
  const node = document.getElementById("typingIndicator");
  if (node) node.remove();
}

function clearChat() {
  chat.querySelectorAll(".message").forEach((node) => node.remove());
}

function addWelcome() {
  addMessage(
    "assistant",
    "Benvenuto",
    "Scrivi qui sotto e io rispondero con un linguaggio clinicamente ordinato. " +
      "Puoi modificare le istruzioni AI dal pannello admin.",
    {
      note: "Questo strumento supporta il lavoro clinico, non sostituisce il giudizio professionale.",
    }
  );
}

function renderSessions() {
  sessionList.innerHTML = "";
  state.sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `session-item ${state.activeSessionId === session.id ? "active" : ""}`;
    const info = document.createElement("div");
    info.className = "session-info";
    const title = document.createElement("div");
    title.className = "session-title";
    title.textContent = session.title || "Nuova chat";
    title.addEventListener("dblclick", async (event) => {
      event.stopPropagation();
      const newTitle = prompt("Nuovo titolo chat:", session.title || "");
      if (!newTitle) return;
      await fetch(`/api/sessions/${session.id}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle.trim() }),
      });
      await refreshSessions();
    });
    const meta = document.createElement("div");
    meta.className = "session-meta";
    meta.textContent = `${session.count || 0} messaggi`;
    info.appendChild(title);
    info.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "session-actions";
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.title = "Elimina chat";
    del.textContent = "x";
    del.addEventListener("click", async (event) => {
      event.stopPropagation();
      await deleteSession(session.id);
    });
    actions.appendChild(del);

    item.appendChild(info);
    item.appendChild(actions);
    item.addEventListener("click", () => loadSession(session.id));
    sessionList.appendChild(item);
  });
}

async function loadSessions() {
  const res = await fetch("/api/sessions");
  const data = await res.json();
  state.sessions = data.sessions || [];
  if (!state.sessions.length) {
    const newSession = await createSession();
    state.sessions = [newSession];
  }
  if (!state.activeSessionId) {
    state.activeSessionId = state.sessions[0].id;
  }
  renderSessions();
  await loadSession(state.activeSessionId);
}

async function createSession() {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Nuova chat" }),
  });
  return await res.json();
}

async function loadSession(sessionId) {
  state.activeSessionId = sessionId;
  const res = await fetch(`/api/sessions/${sessionId}`);
  const session = await res.json();
  activeChatTitle.textContent = session.title || "Chat clinica";
  clearChat();
  if (!session.messages || session.messages.length === 0) {
    addWelcome();
  } else {
    let lastDate = "";
    session.messages.forEach((msg) => {
      const dateLabel = formatDate(msg.created_at);
      if (dateLabel && dateLabel !== lastDate) {
        addDateDivider(dateLabel);
        lastDate = dateLabel;
      }
      addMessage(msg.role, msg.role === "assistant" ? "Neuro AI" : "Tu", msg.content, {
        time: formatTime(msg.created_at),
      });
    });
  }
  await refreshSessions();
}

async function refreshSessions() {
  const res = await fetch("/api/sessions");
  const data = await res.json();
  state.sessions = data.sessions || [];
  renderSessions();
}

async function deleteSession(sessionId) {
  const res = await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  if (!res.ok) return;
  if (state.activeSessionId === sessionId) {
    state.activeSessionId = null;
  }
  await loadSessions();
}

async function loadProfile() {
  const res = await fetch("/api/profile");
  if (!res.ok) return;
  const data = await res.json();
  userName.textContent = data.username || data.name || "Utente";
  userEmail.textContent = data.email || "";
  const initial = (data.username || data.name || "U").trim().charAt(0).toUpperCase();
  userAvatar.textContent = initial || "U";
  state.userInitial = initial || "U";
}

async function loadActiveAssistant() {
  const res = await fetch("/api/assistant-active");
  if (!res.ok) return;
  const data = await res.json();
  state.activeAssistantId = data.id || null;
  state.assistantAvatarUrl = data.avatar_url || "/assets/avatar-default.svg";
  assistantAvatar.src = data.avatar_url || "/assets/avatar-default.svg";
  assistantName.textContent = data.name || "Assistente";
  assistantGender.textContent = `Genere: ${data.gender || "N"}`;
}

async function applyPreferences() {
  const res = await fetch("/api/settings");
  if (!res.ok) return;
  const settings = await res.json();
  if (settings.theme) {
    document.documentElement.setAttribute("data-theme", settings.theme);
  }
  if (safetyBanner) {
    safetyBanner.style.display = settings.safety_banner === false ? "none" : "block";
  }
  document.documentElement.setAttribute("data-text", settings.accessibility_large_text ? "large" : "normal");
  document.documentElement.setAttribute("data-motion", settings.accessibility_reduce_motion ? "reduced" : "normal");
  applyLanguage(settings.language || "it");
}

composerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = messageInput.value.trim();
  if (!content) return;

  addMessage("user", "Tu", content, { time: formatTime(new Date().toISOString()) });
  messageInput.value = "";
  addTypingIndicator();

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: content,
      session_id: state.activeSessionId,
      assistant_id: state.activeAssistantId,
    }),
  });

  if (!res.ok) {
    removeTypingIndicator();
    const err = await res.json().catch(() => ({ error: "Errore server" }));
    addMessage("assistant", "Errore", err.error || "Errore server.");
    return;
  }

  const data = await res.json();
  removeTypingIndicator();
  if (data.session_id) {
    state.activeSessionId = data.session_id;
  }
  const dateLabel = formatDate(data.assistant_time);
  const lastDivider = Array.from(chat.querySelectorAll(".date-divider")).pop();
  if (!lastDivider || (dateLabel && lastDivider.textContent !== dateLabel)) {
    if (dateLabel) addDateDivider(dateLabel);
  }
  addMessage("assistant", "Neuro AI", data.reply, {
    note: data.note,
    time: formatTime(data.assistant_time),
  });
  await refreshSessions();
  const active = state.sessions.find((s) => s.id === state.activeSessionId);
  if (active) {
    activeChatTitle.textContent = active.title;
  }
});

newChatBtn.addEventListener("click", async () => {
  const session = await createSession();
  state.activeSessionId = session.id;
  await refreshSessions();
  await loadSession(session.id);
});

clearBtn.addEventListener("click", async () => {
  if (!state.activeSessionId) return;
  const res = await fetch(`/api/sessions/${state.activeSessionId}/clear`, { method: "POST" });
  if (res.ok) {
    clearChat();
    addWelcome();
    await refreshSessions();
  }
});

exportBtn.addEventListener("click", async () => {
  if (!state.activeSessionId) return;
  const res = await fetch(`/api/sessions/${state.activeSessionId}/export`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${state.activeSessionId}.json`;
  link.click();
  URL.revokeObjectURL(url);
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
});

loadSessions().catch(() => {
  addWelcome();
});

loadProfile();
loadActiveAssistant();
applyPreferences();

const I18N = {
  it: {
    "brand.subtitle": "Studio Psicologo",
    "chat.new": "+ Nuova chat",
    "chat.saved": "Chat salvate",
    "tools.title": "Strumenti",
    "tools.settings": "Impostazioni",
    "tools.clear": "Pulisci chat",
    "tools.export": "Esporta JSON",
    "tools.logout": "Logout",
    "privacy.title": "Privacy",
    "privacy.text": "Salvataggio locale sul server. Nessuna condivisione automatica.",
    "top.subtitle": "Esperienza simile alla terapia, ma non sostituisce lo psicologo/a",
    "badge.private": "Riservato",
    "badge.local": "Locale",
    "welcome.text": "Scrivi qui sotto e io rispondero con un linguaggio clinicamente ordinato. Puoi modificare le istruzioni AI dal pannello admin.",
    "welcome.note": "Nota: questo strumento supporta il lavoro clinico, non sostituisce il giudizio professionale.",
    "input.placeholder": "Scrivi un messaggio clinico, una sintesi o una domanda...",
    "input.send": "Invia",
    "safety.banner": "L'AI non e un servizio di emergenza. In caso di urgenza segui i protocolli locali.",
  },
  en: {
    "brand.subtitle": "Psychology Studio",
    "chat.new": "+ New chat",
    "chat.saved": "Saved chats",
    "tools.title": "Tools",
    "tools.settings": "Settings",
    "tools.clear": "Clear chat",
    "tools.export": "Export JSON",
    "tools.logout": "Logout",
    "privacy.title": "Privacy",
    "privacy.text": "Data is stored locally on the server. No automatic sharing.",
    "top.subtitle": "Therapy-like experience, but it does not replace a psychologist",
    "badge.private": "Private",
    "badge.local": "Local",
    "welcome.text": "Write below and I will reply in a clinically ordered tone. You can edit AI instructions in the admin panel.",
    "welcome.note": "Note: this tool supports clinical work and does not replace professional judgment.",
    "input.placeholder": "Write a clinical note, summary, or question...",
    "input.send": "Send",
    "safety.banner": "AI is not an emergency service. In urgent situations follow local protocols.",
  },
};

function applyLanguage(lang) {
  const dict = I18N[lang] || I18N.it;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) el.setAttribute("placeholder", dict[key]);
  });
}

// Speech-to-text (browser)
let recognition = null;
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = "it-IT";
  recognition.interimResults = false;
  recognition.onstart = () => micBtn.classList.add("active");
  recognition.onend = () => micBtn.classList.remove("active");
  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    messageInput.value = messageInput.value ? `${messageInput.value.trim()} ${text}` : text;
  };
}

micBtn.addEventListener("click", () => {
  if (!recognition) {
    addMessage("assistant", "Audio non disponibile", "Questo browser non supporta il riconoscimento vocale.");
    return;
  }
  recognition.start();
});
