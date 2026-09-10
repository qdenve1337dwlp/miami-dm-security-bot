#!/usr/bin/env python3
import json
import os
import queue
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request

TOKEN = (
    os.environ.get("TELEGRAM_BOT_TOKEN")
    or os.environ.get("BOT_TOKEN")
    or ""
).strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GAME_SERVICE = os.environ.get("GAME_SERVICE", "ragemp.service").strip()
SUMMARY_INTERVAL = max(30, int(os.environ.get("SUMMARY_INTERVAL", "60")))
HOST = os.uname().nodename
EVENTS = queue.Queue()


def send(message):
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": message[:4000]}).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read()
    except Exception as exc:
        print(f"telegram send failed: {type(exc).__name__}", flush=True)


def journal_reader():
    units = ["ssh.service", "sshd.service", "fail2ban.service"]
    if GAME_SERVICE:
        units.append(GAME_SERVICE)
    command = ["journalctl", "-f", "-n", "0", "-o", "json"]
    for unit in units:
        command.extend(["-u", unit])

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, text=True, errors="replace"
    )
    if process.stdout is None:
        raise RuntimeError("journalctl stdout is unavailable")
    for line in process.stdout:
        try:
            entry = json.loads(line)
            EVENTS.put((entry.get("_SYSTEMD_UNIT", ""), entry.get("MESSAGE", "")))
        except (json.JSONDecodeError, TypeError):
            continue


def main():
    if not TOKEN or not CHAT_ID:
        raise SystemExit("BOT_TOKEN (or TELEGRAM_BOT_TOKEN) and TELEGRAM_CHAT_ID are required")

    threading.Thread(target=journal_reader, daemon=True).start()
    send(f"🛡️ Мониторинг безопасности включён\nСервер: {HOST}")
    failed = 0
    sources = set()
    last_summary = time.monotonic()

    while True:
        try:
            unit, message = EVENTS.get(timeout=5)
        except queue.Empty:
            unit = message = ""

        if unit in {"ssh.service", "sshd.service"} and re.search(
            r"Failed password|Invalid user|authentication failure", message, re.I
        ):
            failed += 1
            match = re.search(r"from ([0-9a-fA-F:.]+)", message)
            if match:
                sources.add(match.group(1))
        elif unit == "fail2ban.service" and re.search(r"\bBan\b|\bUnban\b", message):
            send(f"🚫 Fail2ban\n{message}\nСервер: {HOST}")
        elif GAME_SERVICE and unit == GAME_SERVICE:
            if re.search(r"Started|Stopped|Failed|Deactivated|Main process exited", message, re.I):
                send(f"🎮 Игровой сервер\n{message}\nСервер: {HOST}")
            elif re.search(r"\b(ERROR|FATAL|EXCEPTION|CRITICAL)\b", message, re.I):
                send(f"⚠️ Ошибка игрового сервера\n{message}\nСервер: {HOST}")

        now = time.monotonic()
        if now - last_summary >= SUMMARY_INTERVAL:
            if failed:
                ips = ", ".join(sorted(sources)[:15]) or "не определены"
                send(
                    f"🔐 Попытки перебора SSH: {failed}\n"
                    f"Источники: {ips}\nСервер: {HOST}"
                )
            failed = 0
            sources.clear()
            last_summary = now


if __name__ == "__main__":
    main()
