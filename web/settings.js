const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");
const saveProfileBtn = document.getElementById("saveProfileBtn");
const profileHint = document.getElementById("profileHint");
const logoutBtn = document.getElementById("logoutBtn");
const responseStyleSelect = document.getElementById("responseStyleSelect");
const safetyBannerSelect = document.getElementById("safetyBannerSelect");
const themeSelect = document.getElementById("themeSelect");
const languageSelect = document.getElementById("languageSelect");
const largeTextSelect = document.getElementById("largeTextSelect");
const reduceMotionSelect = document.getElementById("reduceMotionSelect");
const emailNotifSelect = document.getElementById("emailNotifSelect");
const testEmailBtn = document.getElementById("testEmailBtn");
const emailHint = document.getElementById("emailHint");

async function loadProfile() {
  const res = await fetch("/api/profile");
  if (!res.ok) return;
  const data = await res.json();
  nameInput.value = data.name || "";
  emailInput.value = data.email || "";
}

async function loadPreferences() {
  const res = await fetch("/api/settings");
  if (!res.ok) return;
  const data = await res.json();
  responseStyleSelect.value = data.response_style || "adaptive";
  safetyBannerSelect.checked = data.safety_banner !== false;
  themeSelect.value = data.theme || "warm";
  languageSelect.value = data.language || "it";
  largeTextSelect.checked = !!data.accessibility_large_text;
  reduceMotionSelect.checked = !!data.accessibility_reduce_motion;
  emailNotifSelect.checked = !!data.notifications_email;
  applyLanguage(languageSelect.value);
}

saveProfileBtn.addEventListener("click", async () => {
  const res = await fetch("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: nameInput.value.trim(),
      email: emailInput.value.trim(),
    }),
  });
  profileHint.textContent = res.ok ? "Profilo salvato." : "Errore nel salvataggio.";
});

async function savePreferences() {
  await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      response_style: responseStyleSelect.value,
      safety_banner: safetyBannerSelect.checked,
      theme: themeSelect.value,
      language: languageSelect.value,
      accessibility_large_text: largeTextSelect.checked,
      accessibility_reduce_motion: reduceMotionSelect.checked,
      notifications_email: emailNotifSelect.checked,
    }),
  });
}

responseStyleSelect.addEventListener("change", savePreferences);
safetyBannerSelect.addEventListener("change", savePreferences);
themeSelect.addEventListener("change", savePreferences);
languageSelect.addEventListener("change", () => {
  savePreferences();
  applyLanguage(languageSelect.value);
});
largeTextSelect.addEventListener("change", savePreferences);
reduceMotionSelect.addEventListener("change", savePreferences);
emailNotifSelect.addEventListener("change", savePreferences);

testEmailBtn.addEventListener("click", async () => {
  const res = await fetch("/api/notifications/test", { method: "POST" });
  if (res.ok) {
    emailHint.textContent = "Email di test inviata.";
  } else {
    const err = await res.json().catch(() => ({ error: "Errore" }));
    emailHint.textContent = err.error || "Errore invio email.";
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
});

loadProfile();
loadPreferences();

const I18N = {
  it: {
    "settings.title": "Impostazioni",
    "settings.subtitle": "Profilo, privacy e preferenze",
    "settings.back": "Torna alla chat",
    "settings.logout": "Logout",
    "settings.profile": "Profilo",
    "settings.name": "Nome completo",
    "settings.email": "Email",
    "settings.save": "Salva profilo",
    "settings.privacy": "Privacy",
    "settings.privacyText": "I dati sono salvati localmente sul server. Nessuna condivisione automatica.",
    "settings.chatPrefs": "Preferenze chat",
    "settings.responseStyle": "Lunghezza risposte",
    "settings.safetyBanner": "Banner sicurezza",
    "settings.appearance": "Aspetto",
    "settings.theme": "Tema",
    "settings.language": "Lingua",
    "settings.language.label": "Lingua interfaccia",
    "settings.accessibility": "Accessibilita",
    "settings.largeText": "Testo grande",
    "settings.reduceMotion": "Riduci animazioni",
    "settings.notifications": "Notifiche",
    "settings.emailNotif": "Email di riepilogo",
    "settings.emailNote": "Funzione locale: salva solo la preferenza.",
    "settings.testEmail": "Invia email di test",
  },
  en: {
    "settings.title": "Settings",
    "settings.subtitle": "Profile, privacy and preferences",
    "settings.back": "Back to chat",
    "settings.logout": "Logout",
    "settings.profile": "Profile",
    "settings.name": "Full name",
    "settings.email": "Email",
    "settings.save": "Save profile",
    "settings.privacy": "Privacy",
    "settings.privacyText": "Data is stored locally on the server. No automatic sharing.",
    "settings.chatPrefs": "Chat preferences",
    "settings.responseStyle": "Response length",
    "settings.safetyBanner": "Safety banner",
    "settings.appearance": "Appearance",
    "settings.theme": "Theme",
    "settings.language": "Language",
    "settings.language.label": "Interface language",
    "settings.accessibility": "Accessibility",
    "settings.largeText": "Large text",
    "settings.reduceMotion": "Reduce motion",
    "settings.notifications": "Notifications",
    "settings.emailNotif": "Email summary",
    "settings.emailNote": "Local only: saves preference.",
    "settings.testEmail": "Send test email",
  },
};

function applyLanguage(lang) {
  const dict = I18N[lang] || I18N.it;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
}
