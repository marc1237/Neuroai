import json
from pathlib import Path
from getpass import getpass
from werkzeug.security import generate_password_hash


DATA_DIR = Path(__file__).parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def load_users():
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"users": []}


def save_users(data):
    DATA_DIR.mkdir(exist_ok=True)
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    username = input("Username admin: ").strip()
    if not username:
        print("Username mancante.")
        return
    password = getpass("Password admin: ").strip()
    if not password:
        print("Password mancante.")
        return

    data = load_users()
    for user in data["users"]:
        if user.get("username") == username:
            user["is_admin"] = True
            if not user.get("password_hash"):
                user["password_hash"] = generate_password_hash(password)
            save_users(data)
            print("Admin aggiornato.")
            return

    data["users"].append(
        {
            "username": username,
            "name": username,
            "email": "",
            "is_admin": True,
            "password_hash": generate_password_hash(password),
        }
    )
    save_users(data)
    print("Admin creato.")


if __name__ == "__main__":
    main()
