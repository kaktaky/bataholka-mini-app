"""Очередь модерации объявлений.

Вся логика модерации изолирована здесь, чтобы правки в main.py были минимальны.
Сам вызов LLM живёт в backend/lmstudio.py — отсюда просто импортируется moderate().
"""

import sqlite3
import threading
import time

from backend import config
from backend.lmstudio import moderate

DB_PATH = config.DB_PATH
POLL_INTERVAL = config.MODERATION_POLL_INTERVAL  # секунд между проходами очереди

_worker_started = False


def _verdict(title: str, description: str) -> tuple[str, str | None]:
    """Возвращает (moderation_status, reject_reason)."""
    try:
        res = moderate(f"{title}\n{description}")
        if res.get("decision") == "approve":
            return "approved", None
        reason = res.get("reason") or "нарушение правил"
        category = res.get("category") or "другое"
        return "rejected", f"{category}: {reason}"
    except Exception as e:
        print(f"[moderation] ошибка LLM: {e}")
        return "rejected", "Ошибка модерации, попробуйте позже"


def _notify(send_notification, author_id: int, title: str, status: str, reason: str | None):
    if status == "approved":
        text = f'Ваше объявление «{title}» прошло модерацию и опубликовано.'
    else:
        text = f'Ваше объявление «{title}» отклонено модерацией.\nПричина: {reason}'
    try:
        send_notification(author_id, text)
    except Exception as e:
        print(f"[moderation] не удалось отправить уведомление: {e}")


def _process_pending(conn: sqlite3.Connection, send_notification):
    rows = conn.execute(
        "SELECT id, title, description, author_id FROM orders "
        "WHERE moderation_status = 'pending' ORDER BY id"
    ).fetchall()
    
    for row in rows:
        status, reason = _verdict(row["title"] or "", row["description"] or "")
        conn.execute(
            "UPDATE orders SET moderation_status = ?, reject_reason = ? WHERE id = ?",
            (status, reason, row["id"]),
        )
        conn.commit()
        _notify(send_notification, row["author_id"], row["title"] or "Объявление", status, reason)
        print(f"[moderation] объявление #{row['id']}: {status}")


def _worker(send_notification):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    while True:
        try:
            _process_pending(conn, send_notification)
        except Exception as e:
            print(f"[moderation] сбой прохода очереди: {e}")
        time.sleep(POLL_INTERVAL)


def start_worker(send_notification):
    """Запускает фоновый поток модерации (один раз за процесс).

    send_notification(chat_id: int, text: str) — функция отправки уведомления автору.
    На старте отдельная дозагрузка не нужна: поток на каждой итерации сам
    забирает все объявления в статусе 'pending' из базы.
    """
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    threading.Thread(target=_worker, args=(send_notification,), daemon=True).start()
    print("[moderation] фоновый воркер запущен")
