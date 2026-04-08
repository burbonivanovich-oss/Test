# ⚡ Быстрый старт (5 минут)

## Что нужно?

Бот, который:
- ✅ Проверяет 12 Telegram-каналов каждый день
- ✅ Ищет в них "тс пиот"
- ✅ Отправляет сводку по расписанию

## Шаг 1: Получить Telegram API credentials

1. Откройте https://my.telegram.org/apps
2. Залогиньтесь в аккаунт
3. Создайте App (если нет) или скопируйте существующий:
   - **API ID** = `37195258`
   - **API Hash** = `da6a76c5c4884bceac2fa904ab029b02`

## Шаг 2: Авторизация (выберите ОДИН способ)

### ⭐ Вариант A: QR-код (РЕКОМЕНДУЕТСЯ)

```bash
python setup_session_qr.py <API_ID> <API_HASH>
```

**Пример:**
```bash
python setup_session_qr.py 37195258 da6a76c5c4884bceac2fa904ab029b02
```

**Что дальше:**
1. Откройте Telegram на телефоне
2. Settings → Devices → Link Desktop Device
3. Сканируйте QR-код
4. Скопируйте строку `TELETHON_SESSION_STRING` из вывода

### 🔄 Вариант B: SMS с автоматическим вводом

```bash
python setup_session_auto.py <API_ID> <API_HASH> <PHONE>
```

**Пример:**
```bash
python setup_session_auto.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79122009231
```

**Что дальше:**
1. Ждите SMS с кодом
2. Скопируйте код в консоль (целое число, без пробелов)
3. Нажмите Enter
4. Скопируйте `TELETHON_SESSION_STRING` из вывода

## Шаг 3: Сохранить credentials в `.env`

```bash
cat > .env << 'EOF'
TELETHON_API_ID=37195258
TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
TELETHON_SESSION_STRING="1aBcD1234567890AbCdEfGhIjKlMnOpQrStUvWxYz..."

TELEGRAM_BOT_TOKEN="123456:ABCDEFGHijklmnopqrstuvwxyz123456"
TELEGRAM_CHAT_ID="-1001234567890"
EOF
```

**Где взять:**
- `TELETHON_*` — из вывода Шага 2
- `TELEGRAM_BOT_TOKEN` — от @BotFather
- `TELEGRAM_CHAT_ID` — ID группы, где будут отправляться отчеты

## Шаг 4: Запустить бот

```bash
pip install -r requirements.txt

python wordstat_bot.py --config config.yaml
```

## ✅ Готово!

Бот теперь будет:
- Проверять каналы каждый день
- Искать "тс пиот"
- Отправлять сводку в ваш чат

---

## 🔧 Тестирование

### Проверить, что бот работает:

```bash
python wordstat_bot.py --config config.yaml --dry-run
```

Выведет отчет в консоль без отправки в Telegram.

### Получить список каналов:

Отредактируйте `config.yaml` в секции `channel_monitor.channels`

### Изменить время отправки отчета:

В `config.yaml`:
```yaml
channel_monitor:
  schedule:
    weekday: 1    # 0=Пн, 1=Вт, 2=Ср, ... 6=Вс
    hour: 10      # UTC время
    minute: 0
```

---

## ❓ Что-то не сработало?

| Проблема | Решение |
|----------|---------|
| QR-код не сканируется | Используйте `setup_session_auto.py` вместо QR |
| "The confirmation code has expired" | Используйте QR-код (не требует SMS) |
| ModuleNotFoundError: telethon | `pip install telethon` |
| Бот не отправляет сообщения | Проверьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` |

---

**На этом всё!** 🎉

Теперь посмотрите `SETUP_GUIDE.md` для более подробных инструкций.
