import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

AVATAR_DIR = DATA_DIR / "avatars"
AVATAR_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "chat_history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
USERS_FILE = DATA_DIR / "users.json"
ASSISTANTS_FILE = DATA_DIR / "assistants.json"
SECRET_FILE = DATA_DIR / "secret.key"
ACTIVE_FILE = DATA_DIR / "active_sessions.json"

DEFAULT_SYSTEM_PROMPT = (
    "Sei un assistente AI che supporta il lavoro di psicologi. "
    "Usa un linguaggio clinicamente ordinato, prudente e rispettoso. "
    "Non fornire diagnosi definitive né sostituire il giudizio professionale. "
    "In caso di rischio o emergenza, invita a seguire i protocolli locali."
)

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_PROVIDER = "openai"
DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"


def get_secret_key():
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(encoding="utf-8").strip()
    key = os.urandom(24).hex()
    SECRET_FILE.write_text(key, encoding="utf-8")
    return key


def load_active():
    data = load_json(ACTIVE_FILE, {"sessions": {}})
    if "sessions" not in data:
        data = {"sessions": {}}
    return data


def save_active(data):
    save_json(ACTIVE_FILE, data)


def touch_active():
    if not session.get("user"):
        return
    data = load_active()
    sid = session.get("sid")
    if not sid:
        sid = os.urandom(8).hex()
        session["sid"] = sid
    data["sessions"][sid] = {
        "user": session.get("user"),
        "last_seen": datetime.utcnow().isoformat() + "Z",
    }
    save_active(data)


def load_users():
    data = load_json(USERS_FILE, {"users": []})
    if "users" not in data:
        data = {"users": []}
    for user in data["users"]:
        if "is_admin" not in user:
            user["is_admin"] = False
    return data


def save_users(data):
    save_json(USERS_FILE, data)


def has_users():
    return len(load_users().get("users", [])) > 0


def create_user(username, password, name="", email="", is_admin=False):
    data = load_users()
    if any(u["username"] == username for u in data["users"]):
        return False
    if not data["users"]:
        is_admin = True
    data["users"].append(
        {
            "username": username,
            "name": name,
            "email": email,
            "is_admin": is_admin,
            "password_hash": generate_password_hash(password),
        }
    )
    save_users(data)
    return True


def authenticate(username, password):
    data = load_users()
    for user in data["users"]:
        if user["username"] == username and check_password_hash(user["password_hash"], password):
            return True
    return False


def is_admin_user(username):
    data = load_users()
    for user in data["users"]:
        if user["username"] == username:
            return bool(user.get("is_admin"))
    return False


def load_assistants():
    data = load_json(
        ASSISTANTS_FILE,
        {
            "active_assistant_id": "assistant-1",
            "assistants": [
                {
                    "id": "assistant-1",
                    "name": "Dott.ssa Arianna",
                    "gender": "F",
                    "avatar_url": "/assets/avatar-default.svg",
                    "prompt_addendum": "",
                }
            ],
        },
    )
    if "assistants" not in data:
        data["assistants"] = []
    if not data["assistants"]:
        data["assistants"].append(
            {
                "id": "assistant-1",
                "name": "Dott.ssa Arianna",
                "gender": "F",
                "avatar_url": "/assets/avatar-default.svg",
                "prompt_addendum": "",
            }
        )
        data["active_assistant_id"] = data["assistants"][0]["id"]
    return data


def save_assistants(data):
    save_json(ASSISTANTS_FILE, data)


def get_active_assistant():
    data = load_assistants()
    active_id = data.get("active_assistant_id")
    for assistant in data["assistants"]:
        if assistant["id"] == active_id:
            return data, assistant
    return data, data["assistants"][0]


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_settings():
    settings = load_json(
        SETTINGS_FILE,
        {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "model": DEFAULT_MODEL,
            "offline_mode": False,
            "provider": DEFAULT_PROVIDER,
            "base_url": DEFAULT_BASE_URL,
            "theme": "warm",
            "response_style": "adaptive",
            "safety_banner": True,
            "language": "it",
            "accessibility_large_text": False,
            "accessibility_reduce_motion": False,
            "notifications_email": False,
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": "",
            "smtp_from": "",
            "smtp_tls": True,
        },
    )
    if not settings.get("system_prompt"):
        settings["system_prompt"] = DEFAULT_SYSTEM_PROMPT
    if not settings.get("model"):
        settings["model"] = DEFAULT_MODEL
    if not settings.get("provider"):
        settings["provider"] = DEFAULT_PROVIDER
    if not settings.get("base_url"):
        settings["base_url"] = DEFAULT_BASE_URL
    if "offline_mode" not in settings:
        settings["offline_mode"] = False
    if "theme" not in settings:
        settings["theme"] = "warm"
    if "response_style" not in settings:
        settings["response_style"] = "adaptive"
    if "safety_banner" not in settings:
        settings["safety_banner"] = True
    if "language" not in settings:
        settings["language"] = "it"
    if "accessibility_large_text" not in settings:
        settings["accessibility_large_text"] = False
    if "accessibility_reduce_motion" not in settings:
        settings["accessibility_reduce_motion"] = False
    if "notifications_email" not in settings:
        settings["notifications_email"] = False
    if "smtp_host" not in settings:
        settings["smtp_host"] = ""
    if "smtp_port" not in settings:
        settings["smtp_port"] = 587
    if "smtp_user" not in settings:
        settings["smtp_user"] = ""
    if "smtp_password" not in settings:
        settings["smtp_password"] = ""
    if "smtp_from" not in settings:
        settings["smtp_from"] = ""
    if "smtp_tls" not in settings:
        settings["smtp_tls"] = True
    return settings


def get_history():
    return load_json(HISTORY_FILE, {"messages": []})


def load_sessions():
    sessions = load_json(SESSIONS_FILE, {"sessions": []})
    if "sessions" not in sessions:
        sessions = {"sessions": []}

    if not sessions["sessions"]:
        legacy = get_history()
        if legacy.get("messages"):
            default_session = {
                "id": "session-1",
                "title": "Chat iniziale",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "messages": legacy["messages"],
            }
            sessions["sessions"].append(default_session)
            save_json(SESSIONS_FILE, sessions)
    return sessions


def save_sessions(sessions):
    save_json(SESSIONS_FILE, sessions)


def get_session_by_id(session_id):
    sessions = load_sessions()
    for session in sessions["sessions"]:
        if session["id"] == session_id:
            return sessions, session
    return sessions, None


def new_session(title="Nuova chat"):
    sessions = load_sessions()
    new_id = f"session-{len(sessions['sessions']) + 1}"
    now = datetime.utcnow().isoformat() + "Z"
    session = {
        "id": new_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "assistant_id": None,
    }
    sessions["sessions"].append(session)
    save_sessions(sessions)
    return session


def append_message(session, role, content):
    created_at = datetime.utcnow().isoformat() + "Z"
    session["messages"].append(
        {
            "role": role,
            "content": content,
            "created_at": created_at,
        }
    )
    session["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return created_at


def reset_history():
    save_json(HISTORY_FILE, {"messages": []})


def build_messages(system_prompt, history, user_message):
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history["messages"][-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def call_openai(messages, model, provider, base_url):
    if OpenAI is None:
        raise RuntimeError("Libreria OpenAI non installata.")
    if provider == "lmstudio":
        client = OpenAI(base_url=base_url, api_key="lm-studio")
    else:
        client = OpenAI()
    response = client.responses.create(
        model=model,
        input=messages,
        store=False,
    )
    output_text = response.output_text
    return output_text.strip()


def offline_reply(user_message):
    summary = user_message.strip()
    if len(summary) > 300:
        summary = summary[:300].rstrip() + "..."
    response = (
        "Sintesi clinica preliminare:\n"
        f"- Contenuto principale: {summary}\n\n"
        "Ipotesi di lavoro (non diagnostiche):\n"
        "- Possibili fattori di stress, schemi cognitivi o dinamiche relazionali da esplorare.\n\n"
        "Prossimi passi suggeriti:\n"
        "- Chiarire contesto, durata, intensità e impatto funzionale.\n"
        "- Valutare risorse e fattori protettivi.\n\n"
        "Domande utili:\n"
        "- Quando è iniziato e cosa lo ha innescato?\n"
        "- Cosa lo mantiene nel tempo?\n"
        "- Quali strategie sta già usando la persona?"
    )
    return response


app = Flask(__name__, static_folder="web", static_url_path="")
app.secret_key = get_secret_key()


@app.before_request
def require_auth():
    public_paths = {
        "/login",
        "/api/login",
        "/api/setup",
        "/api/status",
        "/assets/avatar-default.svg",
    }
    if request.path.startswith("/assets/") or request.path.startswith("/avatars/"):
        return
    if request.path in public_paths:
        return
    if request.path.startswith("/api") or request.path == "/":
        if not session.get("user"):
            return redirect("/login") if request.path == "/" else (jsonify({"error": "Non autorizzato"}), 401)
    touch_active()


def require_admin():
    username = session.get("user")
    if not username or not is_admin_user(username):
        return jsonify({"error": "Non autorizzato"}), 403


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/login")
def login_page():
    return send_from_directory(app.static_folder, "login.html")


@app.route("/admin")
def admin_page():
    username = session.get("user")
    if not username or not is_admin_user(username):
        return redirect("/login")
    return send_from_directory(app.static_folder, "admin.html")


@app.route("/settings")
def settings_page():
    if not session.get("user"):
        return redirect("/login")
    return send_from_directory(app.static_folder, "settings.html")


@app.post("/api/login")
def api_login():
    payload = request.get_json(force=True)
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if authenticate(username, password):
        session["user"] = username
        return jsonify({"ok": True})
    return jsonify({"error": "Credenziali non valide"}), 401


@app.post("/api/setup")
def api_setup():
    if has_users():
        return jsonify({"error": "Utente gia creato"}), 400
    payload = request.get_json(force=True)
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    if not username or not password:
        return jsonify({"error": "Dati mancanti"}), 400
    create_user(username, password, name=name, email=email)
    session["user"] = username
    return jsonify({"ok": True})


@app.get("/api/status")
def api_status():
    return jsonify({"has_users": has_users(), "user": session.get("user")})


@app.get("/api/admin/stats")
def api_admin_stats():
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    users = load_users().get("users", [])
    active = load_active().get("sessions", {})
    cutoff = datetime.utcnow().timestamp() - 900
    active_count = 0
    for info in active.values():
        try:
            ts = datetime.fromisoformat(info["last_seen"].replace("Z", "+00:00")).timestamp()
            if ts >= cutoff:
                active_count += 1
        except Exception:
            continue
    return jsonify({"total_users": len(users), "active_users": active_count})


@app.get("/api/profile")
def api_profile():
    username = session.get("user")
    data = load_users()
    for user in data["users"]:
        if user["username"] == username:
            return jsonify(
                {
                    "username": user.get("username"),
                    "name": user.get("name") or user.get("username"),
                    "email": user.get("email") or "",
                    "is_admin": bool(user.get("is_admin")),
                }
            )
    return jsonify({"error": "Utente non trovato"}), 404


@app.post("/api/profile")
def api_update_profile():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Non autorizzato"}), 401
    payload = request.get_json(force=True)
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    data = load_users()
    for user in data["users"]:
        if user["username"] == username:
            if name:
                user["name"] = name
            if email:
                user["email"] = email
            save_users(data)
            return jsonify({"ok": True})
    return jsonify({"error": "Utente non trovato"}), 404


@app.post("/api/notifications/test")
def api_test_email():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Non autorizzato"}), 401
    settings = get_settings()
    smtp_host = settings.get("smtp_host") or ""
    smtp_user = settings.get("smtp_user") or ""
    smtp_password = settings.get("smtp_password") or ""
    smtp_from = settings.get("smtp_from") or smtp_user
    smtp_port = int(settings.get("smtp_port") or 587)
    smtp_tls = bool(settings.get("smtp_tls"))
    if not smtp_host or not smtp_user or not smtp_password or not smtp_from:
        return jsonify({"error": "SMTP non configurato"}), 400

    data = load_users()
    email_to = None
    for user in data["users"]:
        if user["username"] == username:
            email_to = user.get("email") or ""
            break
    if not email_to:
        return jsonify({"error": "Email utente mancante"}), 400

    msg = EmailMessage()
    msg["Subject"] = "Neuro AI Studio - Test email"
    msg["From"] = smtp_from
    msg["To"] = email_to
    msg.set_content("Questo e un test di notifica email da Neuro AI Studio.")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if smtp_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as exc:
        return jsonify({"error": f"Invio email fallito: {exc}"}), 500

    return jsonify({"ok": True})


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/history")
def api_history():
    return jsonify(get_history())


@app.get("/api/settings")
def api_get_settings():
    if not session.get("user"):
        return jsonify({"error": "Non autorizzato"}), 401
    settings = get_settings()
    if not is_admin_user(session.get("user")):
        return jsonify(
            {
                "theme": settings.get("theme"),
                "response_style": settings.get("response_style"),
                "safety_banner": settings.get("safety_banner"),
                "language": settings.get("language"),
                "accessibility_large_text": settings.get("accessibility_large_text"),
                "accessibility_reduce_motion": settings.get("accessibility_reduce_motion"),
                "notifications_email": settings.get("notifications_email"),
            }
        )
    return jsonify(settings)


@app.get("/api/assistant-active")
def api_active_assistant():
    _, assistant = get_active_assistant()
    return jsonify(
        {
            "id": assistant.get("id"),
            "name": assistant.get("name"),
            "gender": assistant.get("gender"),
            "avatar_url": assistant.get("avatar_url"),
        }
    )


@app.get("/avatars/<path:filename>")
def api_avatar(filename):
    return send_from_directory(AVATAR_DIR, filename)


@app.post("/api/settings")
def api_set_settings():
    payload = request.get_json(force=True)
    settings = get_settings()
    if "theme" in payload:
        settings["theme"] = payload["theme"]
    if "response_style" in payload:
        settings["response_style"] = payload["response_style"]
    if "safety_banner" in payload:
        settings["safety_banner"] = bool(payload["safety_banner"])
    if "language" in payload:
        settings["language"] = payload["language"]
    if "accessibility_large_text" in payload:
        settings["accessibility_large_text"] = bool(payload["accessibility_large_text"])
    if "accessibility_reduce_motion" in payload:
        settings["accessibility_reduce_motion"] = bool(payload["accessibility_reduce_motion"])
    if "notifications_email" in payload:
        settings["notifications_email"] = bool(payload["notifications_email"])

    is_admin = is_admin_user(session.get("user"))
    system_prompt = payload.get("system_prompt", "").strip()
    if system_prompt and is_admin:
        settings["system_prompt"] = system_prompt
    if "offline_mode" in payload:
        if is_admin:
            settings["offline_mode"] = bool(payload["offline_mode"])
    provider = payload.get("provider")
    if provider and is_admin:
        settings["provider"] = provider
    base_url = payload.get("base_url")
    if base_url and is_admin:
        settings["base_url"] = base_url
    model = payload.get("model")
    if model and is_admin:
        settings["model"] = model
    if "smtp_host" in payload and is_admin:
        settings["smtp_host"] = payload.get("smtp_host", "")
    if "smtp_port" in payload and is_admin:
        try:
            settings["smtp_port"] = int(payload.get("smtp_port") or 587)
        except Exception:
            settings["smtp_port"] = 587
    if "smtp_user" in payload and is_admin:
        settings["smtp_user"] = payload.get("smtp_user", "")
    if "smtp_password" in payload and is_admin:
        settings["smtp_password"] = payload.get("smtp_password", "")
    if "smtp_from" in payload and is_admin:
        settings["smtp_from"] = payload.get("smtp_from", "")
    if "smtp_tls" in payload and is_admin:
        settings["smtp_tls"] = bool(payload.get("smtp_tls"))
    save_json(SETTINGS_FILE, settings)
    return jsonify({"ok": True})


@app.get("/api/assistants")
def api_get_assistants():
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    data = load_assistants()
    return jsonify(data)


@app.post("/api/assistants")
def api_create_assistant():
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    payload = request.get_json(force=True)
    data = load_assistants()
    new_id = f"assistant-{len(data['assistants']) + 1}"
    assistant = {
        "id": new_id,
        "name": (payload.get("name") or "Assistente").strip(),
        "gender": (payload.get("gender") or "N").strip(),
        "avatar_url": payload.get("avatar_url") or "/assets/avatar-default.svg",
        "prompt_addendum": payload.get("prompt_addendum") or "",
    }
    data["assistants"].append(assistant)
    data["active_assistant_id"] = new_id
    save_assistants(data)
    return jsonify(assistant)


@app.put("/api/assistants/<assistant_id>")
def api_update_assistant(assistant_id):
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    payload = request.get_json(force=True)
    data = load_assistants()
    for assistant in data["assistants"]:
        if assistant["id"] == assistant_id:
            if payload.get("name"):
                assistant["name"] = payload["name"].strip()
            if payload.get("gender"):
                assistant["gender"] = payload["gender"].strip()
            if payload.get("prompt_addendum") is not None:
                assistant["prompt_addendum"] = payload.get("prompt_addendum", "")
            if payload.get("avatar_url"):
                assistant["avatar_url"] = payload["avatar_url"]
            save_assistants(data)
            return jsonify({"ok": True})
    return jsonify({"error": "Assistente non trovato"}), 404


@app.post("/api/assistants/<assistant_id>/select")
def api_select_assistant(assistant_id):
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    data = load_assistants()
    if any(a["id"] == assistant_id for a in data["assistants"]):
        data["active_assistant_id"] = assistant_id
        save_assistants(data)
        return jsonify({"ok": True})
    return jsonify({"error": "Assistente non trovato"}), 404


@app.post("/api/assistants/<assistant_id>/avatar")
def api_upload_avatar(assistant_id):
    unauthorized = require_admin()
    if unauthorized:
        return unauthorized
    if "file" not in request.files:
        return jsonify({"error": "File mancante"}), 400
    file = request.files["file"]
    filename = secure_filename(file.filename or "")
    if not filename:
        return jsonify({"error": "Nome file non valido"}), 400
    ext = Path(filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify({"error": "Formato non supportato"}), 400
    new_name = f"{assistant_id}-{int(datetime.utcnow().timestamp())}{ext}"
    dest = AVATAR_DIR / new_name
    file.save(dest)
    data = load_assistants()
    for assistant in data["assistants"]:
        if assistant["id"] == assistant_id:
            assistant["avatar_url"] = f"/avatars/{new_name}"
            save_assistants(data)
            return jsonify({"avatar_url": assistant["avatar_url"]})
    return jsonify({"error": "Assistente non trovato"}), 404


@app.post("/api/chat")
def api_chat():
    payload = request.get_json(force=True)
    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id")
    assistant_id = payload.get("assistant_id")
    if not message:
        return jsonify({"error": "Messaggio vuoto."}), 400

    settings = get_settings()
    assistants_data, active_assistant = get_active_assistant()
    if assistant_id:
        for a in assistants_data["assistants"]:
            if a["id"] == assistant_id:
                active_assistant = a
                assistants_data["active_assistant_id"] = a["id"]
                save_assistants(assistants_data)
                break
    sessions, session = get_session_by_id(session_id) if session_id else (load_sessions(), None)
    if session is None:
        session = new_session()
    session["assistant_id"] = active_assistant["id"]
    history = {"messages": session["messages"]}
    profile = (
        f"Nome: {active_assistant.get('name','Assistente')}\n"
        f"Genere: {active_assistant.get('gender','N')}\n"
    )
    if active_assistant.get("prompt_addendum"):
        profile += f"Note persona: {active_assistant['prompt_addendum']}\n"
    user_pref = settings.get("response_style", "adaptive")
    style_line = (
        "Adatta la lunghezza: breve se il messaggio e breve, "
        "piu approfondito se il messaggio e lungo."
    )
    if user_pref == "brief":
        style_line = "Rispondi in modo breve e diretto (1-3 frasi quando possibile)."
    elif user_pref == "detailed":
        style_line = "Rispondi in modo piu approfondito e strutturato."
    system_prompt = (
        settings["system_prompt"]
        + "\n\nPreferenze utente:\n"
        + style_line
        + "\n\nProfilo assistente:\n"
        + profile
    )
    messages = build_messages(system_prompt, history, message)

    if settings.get("offline_mode"):
        reply = offline_reply(message)
    else:
        try:
            reply = call_openai(
                messages,
                settings["model"],
                settings["provider"],
                settings["base_url"],
            )
        except Exception as exc:
            return jsonify({"error": f"Errore OpenAI: {exc}"}), 500

    user_time = append_message(session, "user", message)
    assistant_time = append_message(session, "assistant", reply)

    if session["title"] in ("Nuova chat", "Chat iniziale") and session["messages"]:
        first_user = next((m for m in session["messages"] if m["role"] == "user"), None)
        if first_user:
            session["title"] = first_user["content"][:40].strip() or session["title"]
    save_sessions(sessions)

    note = "Ricontrolla sempre e integra secondo il tuo giudizio clinico."
    return jsonify(
        {
            "reply": reply,
            "note": note,
            "total_messages": len(session["messages"]),
            "session_id": session["id"],
            "user_time": user_time,
            "assistant_time": assistant_time,
        }
    )


@app.post("/api/clear")
def api_clear():
    reset_history()
    return jsonify({"ok": True})


@app.get("/api/sessions")
def api_sessions():
    sessions = load_sessions()
    return jsonify(
        {
            "sessions": [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "created_at": s["created_at"],
                    "updated_at": s["updated_at"],
                    "assistant_id": s.get("assistant_id"),
                    "count": len(s["messages"]),
                }
                for s in sessions["sessions"]
            ]
        }
    )


@app.post("/api/sessions")
def api_create_session():
    payload = request.get_json(force=True, silent=True) or {}
    title = (payload.get("title") or "Nuova chat").strip()
    session = new_session(title=title)
    return jsonify(session)


@app.get("/api/sessions/<session_id>")
def api_get_session(session_id):
    _, session = get_session_by_id(session_id)
    if session is None:
        return jsonify({"error": "Sessione non trovata"}), 404
    return jsonify(session)


@app.post("/api/sessions/<session_id>/rename")
def api_rename_session(session_id):
    payload = request.get_json(force=True)
    title = (payload.get("title") or "").strip()
    sessions, session = get_session_by_id(session_id)
    if session is None:
        return jsonify({"error": "Sessione non trovata"}), 404
    if title:
        session["title"] = title
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_sessions(sessions)
    return jsonify({"ok": True})


@app.post("/api/sessions/<session_id>/clear")
def api_clear_session(session_id):
    sessions, session = get_session_by_id(session_id)
    if session is None:
        return jsonify({"error": "Sessione non trovata"}), 404
    session["messages"] = []
    session["updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_sessions(sessions)
    return jsonify({"ok": True})


@app.delete("/api/sessions/<session_id>")
def api_delete_session(session_id):
    sessions = load_sessions()
    original_len = len(sessions["sessions"])
    sessions["sessions"] = [s for s in sessions["sessions"] if s["id"] != session_id]
    if len(sessions["sessions"]) == original_len:
        return jsonify({"error": "Sessione non trovata"}), 404
    save_sessions(sessions)
    return jsonify({"ok": True})


@app.get("/api/export")
def api_export():
    history = get_history()
    return app.response_class(
        json.dumps(history, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=neuro-ai-chat.json"},
    )


@app.get("/api/sessions/<session_id>/export")
def api_export_session(session_id):
    _, session = get_session_by_id(session_id)
    if session is None:
        return jsonify({"error": "Sessione non trovata"}), 404
    return app.response_class(
        json.dumps(session, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={session_id}.json"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=False)
