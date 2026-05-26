const totalUsers = document.getElementById("totalUsers");
const activeUsers = document.getElementById("activeUsers");
const adminPrompt = document.getElementById("adminPrompt");
const savePromptBtn = document.getElementById("savePromptBtn");
const adminHint = document.getElementById("adminHint");
const smtpHost = document.getElementById("smtpHost");
const smtpPort = document.getElementById("smtpPort");
const smtpUser = document.getElementById("smtpUser");
const smtpPass = document.getElementById("smtpPass");
const smtpFrom = document.getElementById("smtpFrom");
const smtpTls = document.getElementById("smtpTls");
const saveSmtpBtn = document.getElementById("saveSmtpBtn");
const smtpHint = document.getElementById("smtpHint");

async function loadStats() {
  const res = await fetch("/api/admin/stats");
  if (!res.ok) return;
  const data = await res.json();
  totalUsers.textContent = data.total_users || 0;
  activeUsers.textContent = data.active_users || 0;
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  if (!res.ok) return;
  const data = await res.json();
  adminPrompt.value = data.system_prompt || "";
  smtpHost.value = data.smtp_host || "";
  smtpPort.value = data.smtp_port || 587;
  smtpUser.value = data.smtp_user || "";
  smtpPass.value = data.smtp_password || "";
  smtpFrom.value = data.smtp_from || "";
  smtpTls.value = data.smtp_tls === false ? "false" : "true";
}

savePromptBtn.addEventListener("click", async () => {
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ system_prompt: adminPrompt.value.trim() }),
  });
  adminHint.textContent = res.ok ? "Salvato." : "Errore nel salvataggio.";
});

saveSmtpBtn.addEventListener("click", async () => {
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      smtp_host: smtpHost.value.trim(),
      smtp_port: smtpPort.value.trim(),
      smtp_user: smtpUser.value.trim(),
      smtp_password: smtpPass.value.trim(),
      smtp_from: smtpFrom.value.trim(),
      smtp_tls: smtpTls.value === "true",
    }),
  });
  smtpHint.textContent = res.ok ? "SMTP salvato." : "Errore nel salvataggio SMTP.";
});

loadStats();
loadSettings();
setInterval(loadStats, 15000);
