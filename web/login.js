const loginForm = document.getElementById("loginForm");
const usernameInput = document.getElementById("usernameInput");
const passwordInput = document.getElementById("passwordInput");
const loginTitle = document.getElementById("loginTitle");
const loginSubtitle = document.getElementById("loginSubtitle");
const loginHint = document.getElementById("loginHint");
const submitBtn = document.getElementById("submitBtn");
const nameField = document.getElementById("nameField");
const emailField = document.getElementById("emailField");
const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");

let mode = "login";

async function checkStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  if (!data.has_users) {
    mode = "setup";
    loginTitle.textContent = "Crea account";
    loginSubtitle.textContent = "Primo accesso: crea username e password.";
    submitBtn.textContent = "Crea";
    nameField.style.display = "flex";
    emailField.style.display = "flex";
  } else {
    nameField.style.display = "none";
    emailField.style.display = "none";
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();
  if (!username || !password) {
    loginHint.textContent = "Inserisci username e password.";
    return;
  }

  const endpoint = mode === "setup" ? "/api/setup" : "/api/login";
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      password,
      name: nameInput.value.trim(),
      email: emailInput.value.trim(),
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Errore" }));
    loginHint.textContent = err.error || "Errore accesso.";
    return;
  }

  window.location.href = "/";
});

checkStatus();
