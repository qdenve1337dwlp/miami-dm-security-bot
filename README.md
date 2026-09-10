# Miami DM Security Bot

Небольшой Telegram-бот для Ubuntu, который следит за системным журналом и сообщает:

- о попытках перебора SSH;
- о событиях Fail2ban;
- о запуске, остановке и критических ошибках игрового systemd-сервиса.

Бот использует только стандартную библиотеку Python и не требует `pip install`.

## Установка

```bash
git clone https://github.com/YOUR_NAME/miami-dm-security-bot.git
cd miami-dm-security-bot
sudo ./install.sh
sudo nano /etc/miami-dm-security-bot.env
sudo systemctl enable --now miami-dm-security-bot
```

В `/etc/miami-dm-security-bot.env` укажите новый токен Telegram-бота и свой chat ID:

```dotenv
TELEGRAM_BOT_TOKEN=replace_with_a_new_bot_token
TELEGRAM_CHAT_ID=replace_with_your_chat_id
GAME_SERVICE=ragemp.service
SUMMARY_INTERVAL=60
```

Проверка состояния и журнала:

```bash
systemctl status miami-dm-security-bot
journalctl -u miami-dm-security-bot -f
```

Токены и пароли в репозиторий добавлять нельзя. Файл `.env.example` содержит только заглушки.
