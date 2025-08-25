import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict, List

DATA_DIR = Path("data")
DB_PATH = DATA_DIR/"users.json"

class Requisites(TypedDict, total = False):
    id: str
    card: str
    phone: str
    fio: str
    bank: str  # added bank field
    modes: List[str]

def _normalize_phone(phone: str) ->str:
    raw = "".join(ch for ch in (phone or "") if ch.isdigit() or ch == "+")
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    if raw and raw[0] != "+" and len(raw) in (12,13):
        raw = "+" + raw
    return raw

def _normalize_card(card: str) ->str:
    return "".join(ch for ch in (card or "") if ch.isdigit())

def get_user_requisites(user_id: int):
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    raw = user.get("requisites", [])

    if isinstance(raw, dict):
        reqs = [raw] if raw else []
    elif isinstance(raw, list):
        reqs = raw
    else:
        reqs = []

    changed = False
    for r in reqs:
        if not r.get("id"):
            r["id"] = str(uuid.uuid4())
            changed = True
        if "modes" not in r or not isinstance(r.get("modes"), list):
            r["modes"] = []
            changed = True

    if changed:
        user["requisites"] = reqs
        db[key] = user
        _save_db(db)

    return reqs

def set_user_requisites(user_id: int, requisites: Requisites, *, merge: bool = True) -> None:
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    
    item: Requisites = {}
    if "card" in requisites and requisites["card"] is not None:
        item["card"] = _normalize_card(requisites["card"])
    if "phone" in requisites and requisites["phone"] is not None:
        item["phone"] =  _normalize_phone(requisites["phone"])
    if "fio" in requisites and requisites["fio"] is not None:
        item["fio"] = requisites["fio"].strip()
    if "bank" in requisites and requisites["bank"] is not None:
        item["bank"] = requisites["bank"].strip()
    if "modes" not in item:
        item["modes"] = []  

    if not any(item.get(k) for k in ("fio", "phone", "card")):
        raise ValueError("Hech bo‘lmaganda bitta maydon to‘ldirilishi kerak.")
    
    current = user.get("requisites", [])
    if isinstance(current, dict):
        current = [current] if current else []
    elif not isinstance(current, list):
        current = []

    if merge:
        if len(current) >= 10:
            raise ValueError("Maksimal 10 ta rekvizit saqlash mumkin.")
        item["id"] = str(uuid.uuid4())
        current.append(item)
    else:
        item["id"] = str(uuid.uuid4())
        current = [item]

    user["requisites"] = current
    db[key] = user
    _save_db(db)

def delete_requisites_by_id(user_id: int, rid: str) -> bool:
    db = _load_db()
    key = str(user_id)
    user = db.get(key,{})
    reqs = get_user_requisites(user_id)
    new_reqs = [r for r in reqs if r.get("id") != rid]
    if len(new_reqs) == len(reqs):
        return False
    user["requisites"] = new_reqs
    db[key] = user
    _save_db(db)
    return True

def update_modes_by_id(user_id: int, rid: str, modes: List[str]) -> bool:
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    reqs = get_user_requisites(user_id)

    target = None
    for r in reqs:
        if str(r.get("id")) == str(rid):
            target = r
            break
    if target is None:
        return False

    allowed = {"cbp", "c2c"}
    filtered = [m for m in (modes or []) if m in allowed]

    if target.get("modes") == filtered:
        return False

    target["modes"] = filtered
    user["requisites"] = reqs
    db[key] = user
    _save_db(db)
    return True

def set_user_card(user_id: int, card: str) -> None:
    set_user_requisites(user_id,{"card": card})

def set_user_phone(user_id: int, phone: str) -> None:
    set_user_requisites(user_id, {"phone": phone})

def set_user_fio(user_id: int, fio: str) -> None:
    set_user_requisites(user_id, {"fio": fio})


def _ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text("{}", encoding="utf-8")

def _load_db() ->dict:
    _ensure_db()
    try:
        raw = DB_PATH.read_text(encoding="utf-8") or "{}"
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
    
def _save_db(db: dict) -> None:
    _ensure_db()
    tmp = DB_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DB_PATH)

def set_user_token(user_id: int, token:str) -> None:
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    user["token"] = token
    db[key] = user
    _save_db(db)

def get_user_token(user_id: int) -> Optional[str]:
    db = _load_db()
    return db.get(str(user_id), {}).get("token")

def set_user_role(user_id: int, role: str) -> None:
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    user["role"] = role
    db[key] = user
    _save_db(db)

def get_user_role(user_id: int) -> str:
    db = _load_db()
    return db.get(str(user_id), {}).get("role", "user")

def set_user_limits(user_id: int, limits: Dict[str, Any])-> None:
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    user["limits"] = limits
    db[key] = user
    _save_db(db)

def get_user_limits(user_id: int) -> Optional[Dict[str, Any]]:
    db = _load_db()
    return db.get(str(user_id), {}).get("limits") or {}

def set_user_status(user_id: int, status: str) -> None:
    """Set user's online/offline status"""
    db = _load_db()
    key = str(user_id)
    user = db.get(key, {})
    user["status"] = status
    db[key] = user
    _save_db(db)

def get_user_status(user_id: int) -> str:
    """Get user's status, returns 'offline' by default"""
    db = _load_db()
    return db.get(str(user_id), {}).get("status", "offline")

