# 🔑 Полное руководство по настройке Telegram авторизации

## Проблема

❌ **"The confirmation code has expired"** — SMS-код действует только 5 минут, а между запросом и вводом проходит больше времени.

## ✅ Решение: 3 способа авторизации

### Способ 1: QR-код (⭐ РЕКОМЕНДУЕТСЯ - САМЫЙ БЫСТРЫЙ)

**Плюсы:**
- ✅ Работает как Telegram Desktop
- ✅ Не требует SMS-кода
- ✅ Быстро (~30 секунд)
- ✅ Надежно

**Как сделать:**

```bash
# 1. Получите API credentials: https://my.telegram.org/apps

# 2. Запустите QR-авторизацию
python setup_session_qr.py <API_ID> <API_HASH>

# Пример:
python setup_session_qr.py 37195258 da6a76c5c4884bceac2fa904ab029b02

# 3. Отсканируйте QR-код телефоном
#    Settings → Devices → Link Desktop Device → Scan

# 4. Скопируйте environment variables из вывода
export TELETHON_API_ID=37195258
export TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
export TELETHON_SESSION_STRING="1aBcD..."

# 5. Запустите бот - всё работает!
python wordstat_bot.py --config config.yaml
```

---

### Способ 2: SMS с автоматическим вводом (подстраховка)

**Плюсы:**
- ✅ Работает если QR недоступен
- ✅ Автоматический ввод кода (быстро)
- ✅ Поддержка 2FA

**Как сделать:**

```bash
# 1. Запустите скрипт
python setup_session_auto.py <API_ID> <API_HASH> <PHONE>

# Пример:
python setup_session_auto.py 37195258 da6a76c5c4884bceac2fa904ab029b02 +79122009231

# 2. Ждите кода в Telegram
#    (код приходит за 30 секунд)

# 3. Как только получите код, немедленно скопируйте его в консоль
#    Enter the code when you receive it (and press Enter):
#    > 62190

# 4. Если 2FA включена, введите пароль
#    Enter 2FA password:
#    > your_password

# 5. Скопируйте environment variables из вывода
```

---

### Способ 3: SMS с ручным вводом (базовый)

```bash
# Используйте стандартный скрипт
python setup_session.py <API_ID> <API_HASH> <PHONE>

# ⚠️  ВАЖНО:
# - Вводите код СРАЗУ, не ждите!
# - Код действует только ~5 минут
```

---

## 📋 Сравнение методов

| Параметр | QR | SMS Auto | SMS Manual |
|----------|-----|----------|-----------|
| **Скорость** | ⚡⚡⚡ Быстро | ⚡⚡ Среднее | 🐢 Медленно |
| **Надежность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Требует SMS** | ❌ Нет | ✅ Да | ✅ Да |
| **Полностью автоматический** | ✅ Да | ✅ Да | ❌ Нет |
| **Поддержка 2FA** | ✅ Есть | ✅ Есть | ✅ Есть |

---

## 🚀 После авторизации

### Сохраните сессию в `.env`

```bash
cat > .env << 'EOF'
TELETHON_API_ID=37195258
TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
TELETHON_SESSION_STRING="1aBcD1234567890..."

WORDSTAT_OAUTH_TOKEN="your_wordstat_token"
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_CHAT_ID="-1001234567890"
EOF
```

### Установите зависимости

```bash
pip install -r requirements.txt
```

### Запустите бот

```bash
python wordstat_bot.py --config config.yaml
```

---

## 🔧 Отладка

### "ModuleNotFoundError: No module named 'telethon'"

```bash
pip install telethon>=1.34.0
```

### "QR code not working"

Используйте **SMS Auto** метод вместо QR:

```bash
python setup_session_auto.py <API_ID> <API_HASH> <PHONE>
```

### "Session invalid / expired"

Сессия может протухнуть через ~180 дней. Просто переавторизуйтесь:

```bash
rm telegram_session.session  # удалите старую сессию
python setup_session_qr.py <API_ID> <API_HASH>  # создайте новую
```

---

## 💾 Сохранение сессии

### Локально (для разработки)

1. Запустите любой из 3 методов выше
2. Получите `TELETHON_SESSION_STRING` из вывода
3. Сохраните в `.env` файл
4. Бот автоматически прочитает из `.env`

### На bothost.ru или другом хостинге

1. Сохраните session string
2. В "Environment Variables" добавьте:
   ```
   TELETHON_API_ID=37195258
   TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
   TELETHON_SESSION_STRING="1aBcD..."
   ```
3. Загрузите `wordstat_bot.py` и `config.yaml`
4. Запустите

---

## ⚠️ Безопасность

❗ **ВАЖНО:**
- 🔐 Никогда не делитесь `TELETHON_SESSION_STRING` с кем-либо
- 🔐 Не коммитьте `.env` файл в Git (добавьте в `.gitignore`)
- 🔐 Используйте переменные окружения на продакшене

---

## 📊 Мониторинг каналов

После авторизации бот будет:

1. **Каждый день** (по расписанию) проверять 12+ Telegram-каналов
2. **Искать** ключевое слово "тс пиот"
3. **Собирать** сообщения из последних 24-36 часов
4. **Отправлять** короткую сводку в Telegram

### Пример сводки:

```
Упоминание "тс пиот" на каналах:

📱 РИА Новости (@rian_ru)
🔗 Ссылка: https://t.me/rian_ru/12345
📝 Текст: На рынке растет спрос на ТС ПИОТ решения...
🕐 Дата: 2024-03-23 10:30 UTC

📱 ТАСС (@tass_agency)
🔗 Ссылка: https://t.me/tass_agency/67890
📝 Текст: Компания запустила новый модуль ТС ПИОТ...
🕐 Дата: 2024-03-23 08:15 UTC
```

---

## ✅ Checklist

- [ ] Получил API credentials на https://my.telegram.org/apps
- [ ] Выбрал способ авторизации (QR / SMS Auto / SMS Manual)
- [ ] Запустил скрипт авторизации
- [ ] Скопировал TELETHON_SESSION_STRING
- [ ] Создал файл `.env` с credentials
- [ ] Установил зависимости: `pip install -r requirements.txt`
- [ ] Отредактировал `config.yaml` (каналы, ключевые слова)
- [ ] Запустил бот: `python wordstat_bot.py --config config.yaml`
- [ ] Проверил, что бот работает и получает сообщения из каналов

---

## 🆘 Нужна помощь?

Если что-то не работает:

1. Проверьте, что API credentials правильные
2. Убедитесь, что интернет соединение стабильно
3. Попробуйте другой способ авторизации
4. Проверьте логи бота на ошибки

---

**Готово!** 🎉 После этого бот будет парсить Telegram-каналы и отправлять вам сводку по расписанию.
