import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")
SESSIONS_FILE = DATA_DIR / "sessions.json"


DISCLAIMER = (
    "Nota: questo strumento supporta il lavoro clinico ma non sostituisce "
    "il giudizio professionale. Non è un servizio di emergenza."
)


def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]", encoding="utf-8")


def load_sessions():
    ensure_storage()
    try:
        return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_sessions(sessions):
    ensure_storage()
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")


def prompt(text, default=None):
    if default:
        text = f"{text} [{default}]"
    value = input(f"{text}: ").strip()
    return value if value else (default or "")


def prompt_yes_no(text, default="n"):
    default = default.lower()
    value = input(f"{text} (s/n) [{default}]: ").strip().lower()
    if not value:
        value = default
    return value.startswith("s")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


@dataclass
class SessionNote:
    client_name: str
    date: str
    presenting_problem: str
    mood: str
    key_events: str
    interventions: str
    plan: str
    risk_flags: str


def intake_questionnaire():
    print("\n-- Intake (prima raccolta dati) --")
    client_name = prompt("Nome cliente/paziente")
    date = prompt("Data", today_str())
    presenting_problem = prompt("Motivo principale della richiesta")
    history = prompt("Storia e contesto rilevante (breve)")
    goals = prompt("Obiettivi dichiarati")
    supports = prompt("Risorse e supporti presenti")
    medication = prompt("Farmaci o trattamenti in corso (se noti)")
    risk = prompt("Indicatori di rischio (se presenti)")

    return {
        "type": "intake",
        "client_name": client_name,
        "date": date,
        "presenting_problem": presenting_problem,
        "history": history,
        "goals": goals,
        "supports": supports,
        "medication": medication,
        "risk": risk,
    }


def session_notes_template():
    print("\n-- Note sessione (struttura breve) --")
    client_name = prompt("Nome cliente/paziente")
    date = prompt("Data", today_str())
    presenting_problem = prompt("Tema/argomento principale")
    mood = prompt("Umore/affettività osservata")
    key_events = prompt("Eventi chiave/insight emersi")
    interventions = prompt("Interventi/tecniche utilizzate")
    plan = prompt("Piano/compiti/next step")
    risk_flags = prompt("Indicatori di rischio (se presenti)")

    note = SessionNote(
        client_name=client_name,
        date=date,
        presenting_problem=presenting_problem,
        mood=mood,
        key_events=key_events,
        interventions=interventions,
        plan=plan,
        risk_flags=risk_flags,
    )
    return {
        "type": "session_note",
        **note.__dict__,
    }


def cbt_thought_record():
    print("\n-- CBT Thought Record (schema rapido) --")
    client_name = prompt("Nome cliente/paziente")
    date = prompt("Data", today_str())
    situation = prompt("Situazione")
    emotions = prompt("Emozioni (0-100)")
    automatic_thoughts = prompt("Pensieri automatici")
    evidence_for = prompt("Evidenze a favore")
    evidence_against = prompt("Evidenze contro")
    alternative = prompt("Pensiero alternativo")
    outcome = prompt("Esito emotivo/nuova valutazione")

    return {
        "type": "cbt_thought_record",
        "client_name": client_name,
        "date": date,
        "situation": situation,
        "emotions": emotions,
        "automatic_thoughts": automatic_thoughts,
        "evidence_for": evidence_for,
        "evidence_against": evidence_against,
        "alternative": alternative,
        "outcome": outcome,
    }


def psychoeducation_prompt():
    print("\n-- Sintesi psicoeducativa (bozza) --")
    topic = prompt("Argomento (es. ansia, stress, insonnia)")
    audience = prompt("Target (adulti, adolescenti, coppia)")
    tone = prompt("Tono desiderato (calmo, motivazionale, pratico)", "calmo")
    bullets = prompt("Punti chiave da includere (separati da ;)")

    # Non genera testo medico: crea una bozza di outline.
    return {
        "type": "psychoeducation_outline",
        "topic": topic,
        "audience": audience,
        "tone": tone,
        "key_points": [b.strip() for b in bullets.split(";") if b.strip()],
    }


def risk_screening():
    print("\n-- Check rapido rischio (non diagnostico) --")
    client_name = prompt("Nome cliente/paziente")
    date = prompt("Data", today_str())
    suicidal_ideation = prompt_yes_no("Ideazione suicidaria riferita")
    plan = prompt_yes_no("Presenza di piano/mezzi accessibili")
    intent = prompt_yes_no("Intenzione attuale percepita")
    protective = prompt("Fattori protettivi (famiglia, obiettivi, rete)")

    level = "basso"
    if suicidal_ideation and (plan or intent):
        level = "alto"
    elif suicidal_ideation:
        level = "moderato"

    advisory = (
        "Se il rischio è alto o moderato, valutare procedure locali e "
        "coinvolgere servizi di emergenza secondo protocolli clinici."
    )

    return {
        "type": "risk_screening",
        "client_name": client_name,
        "date": date,
        "suicidal_ideation": suicidal_ideation,
        "plan": plan,
        "intent": intent,
        "protective_factors": protective,
        "risk_level": level,
        "advisory": advisory,
    }


def print_outline(entry):
    print("\n-- Bozza psicoeducativa (outline) --")
    print(f"Argomento: {entry['topic']}")
    print(f"Target: {entry['audience']}")
    print(f"Tono: {entry['tone']}")
    print("Struttura suggerita:")
    print("1. Definizione semplice del tema")
    print("2. Sintomi/manifestazioni comuni")
    print("3. Fattori che lo mantengono")
    print("4. Strategie pratiche (non cliniche)")
    print("5. Quando cercare aiuto professionale")
    if entry["key_points"]:
        print("Punti chiave:")
        for kp in entry["key_points"]:
            print(f"- {kp}")


def list_sessions(sessions):
    print("\n-- Sessioni salvate --")
    if not sessions:
        print("Nessuna sessione salvata.")
        return
    for i, s in enumerate(sessions, start=1):
        print(f"{i}. {s.get('date','')} - {s.get('client_name','')} ({s.get('type','')})")


def main():
    print("Neuro AI - Assistente per psicologi")
    print(DISCLAIMER)
    sessions = load_sessions()

    while True:
        print("\nScegli una funzione:")
        print("1) Intake (prima raccolta dati)")
        print("2) Note sessione (template)")
        print("3) CBT Thought Record")
        print("4) Bozza psicoeducativa (outline)")
        print("5) Check rapido rischio")
        print("6) Elenco sessioni salvate")
        print("7) Esci")

        choice = prompt("Selezione", "1")

        if choice == "1":
            entry = intake_questionnaire()
            sessions.append(entry)
            save_sessions(sessions)
            print("Intake salvato.")
        elif choice == "2":
            entry = session_notes_template()
            sessions.append(entry)
            save_sessions(sessions)
            print("Nota sessione salvata.")
        elif choice == "3":
            entry = cbt_thought_record()
            sessions.append(entry)
            save_sessions(sessions)
            print("CBT record salvato.")
        elif choice == "4":
            entry = psychoeducation_prompt()
            sessions.append(entry)
            save_sessions(sessions)
            print_outline(entry)
            print("Outline salvato.")
        elif choice == "5":
            entry = risk_screening()
            sessions.append(entry)
            save_sessions(sessions)
            print(f"Livello di rischio stimato: {entry['risk_level']}")
            print(entry["advisory"])
        elif choice == "6":
            list_sessions(sessions)
        elif choice == "7":
            print("A presto.")
            break
        else:
            print("Selezione non valida.")


if __name__ == "__main__":
    main()
