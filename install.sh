#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo ./install.sh"
  exit 1
fi

install -d -m 0755 /opt/miami-dm-security-bot
install -m 0755 bot.py /opt/miami-dm-security-bot/bot.py
install -m 0644 miami-dm-security-bot.service /etc/systemd/system/miami-dm-security-bot.service

if [[ ! -f /etc/miami-dm-security-bot.env ]]; then
  install -m 0600 .env.example /etc/miami-dm-security-bot.env
  echo "Edit /etc/miami-dm-security-bot.env, then run:"
  echo "  systemctl enable --now miami-dm-security-bot"
else
  systemctl daemon-reload
  systemctl restart miami-dm-security-bot
  echo "Miami DM security bot restarted."
fi
