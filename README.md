# 📊 Wordstat + Telegram Channel Monitor Bot

Полнофункциональный бот, который:

1. **📈 Собирает данные из Yandex Wordstat API**
   - Топ запросов за последний месяц
   - Динамика поиска по неделям
   - Географическое распределение
   - Аналитика по категориям

2. **📱 Мониторит 12 Telegram-каналов**
   - РИА Новости, ТАСС, РБК, Коммерсант и т.д.
   - Ищет ключевое слово "тс пиот"
   - Собирает упоминания за 24-36 часов
   - Отправляет краткую сводку

3. **⏰ Отправляет отчеты по расписанию**
   - Wordstat: каждый понедельник в 7:00 UTC
   - Telegram: каждый вторник в 10:00 UTC
   - Поддерживает команды `/report` и `/channels`

---

## 🚀 Быстрый старт

### 1. Получить credentials

**Для Wordstat:**
- Получи OAuth token на https://yandex.ru/dev/wordstat/

**Для Telegram Channel Monitor:**
- Получи API ID/Hash на https://my.telegram.org/apps
- Авторизуйся:
  ```bash
  python3 setup_session_auto.py <API_ID> <API_HASH> <PHONE>
  # или
  python3 setup_session_qr.py <API_ID> <API_HASH>
  ```

**Для Telegram Bot:**
- Создай бота у @BotFather
- Узнай chat ID (напиши @userinfobot)

### 2. Сохранить в `.env`

```bash
cat > .env << 'EOF'
WORDSTAT_OAUTH_TOKEN="your_wordstat_token"
TELETHON_API_ID=37195258
TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
TELETHON_SESSION_STRING="1ApWapz..."
TELEGRAM_BOT_TOKEN="123456:ABC..."
TELEGRAM_CHAT_ID="-1001234567890"
EOF
```

### 3. Установить и запустить

```bash
pip3 install -r requirements.txt
python3 wordstat_bot.py --config config.yaml
```

---

## 📁 Структура проекта

```
.
├── wordstat_bot.py                 # Основной бот
├── config.yaml                     # Конфигурация
├── requirements.txt                # Зависимости
│
├── telegram_channel_monitor/       # Модуль мониторинга каналов
│   ├── channel_monitor.py          # Telethon client
│   ├── message_filter.py           # Фильтрация по ключевым словам
│   ├── message_parser.py           # Парсинг сообщений
│   ├── summary_formatter.py        # Форматирование отчетов
│   ├── rss_channel_monitor.py      # RSS fallback (резервный)
│   └── __init__.py
│
├── setup_session_auto.py           # SMS авторизация
├── setup_session_qr.py             # QR-код авторизация
│
├── QUICK_START.md                  # 5-минутный гайд
├── SETUP_GUIDE.md                  # Полное руководство
└── README.md                       # Этот файл
```

---

## ⚙️ Конфигурация

### Wordstat (config.yaml)

```yaml
wordstat:
  oauth_token: ""
  base_url: "https://api.wordstat.yandex.net"

analytics:
  - name: "Информационные запросы"
    phrases:
      - "тс пиот"
      - "модуль тс пиот"
    regions: []        # все регионы
    devices: ["all"]
```

### Telegram Channels (config.yaml)

```yaml
channel_monitor:
  enabled: true

  channels:
    - name: "РИА Новости"
      username: "@rian_ru"
    # ... ещё 11 каналов

  keywords:
    - "тс пиот"
    - "ТС ПИОТ"

  hours_lookback: 36   # Смотрим назад на 36 часов

  schedule:
    weekday: 1         # Вторник
    hour: 10           # 10:00 UTC
    minute: 0
```

---

## 📝 Примеры использования

### Запустить в режиме тестирования

```bash
python3 wordstat_bot.py --config config.yaml --dry-run
```

Выведет отчет в консоль без отправки в Telegram.

### Получить отчет сейчас (через бота)

Отправь в чат с ботом:
- `/report` — Wordstat отчет
- `/channels` — Мониторинг каналов
- `/start` — справка

### Запустить с кастомным конфигом

```bash
python3 wordstat_bot.py --config my_config.yaml
```

---

## 🔌 Развертывание на bothost.ru

1. Создай новый бот (Python 3.11+)
2. Загрузи файлы через Git:
   ```bash
   git clone https://github.com/burbonivanovich-oss/Test.git
   cd Test
   git checkout production/wordstat-telegram-full
   ```
3. Добавь переменные окружения:
   - `WORDSTAT_OAUTH_TOKEN`
   - `TELETHON_API_ID`
   - `TELETHON_API_HASH`
   - `TELETHON_SESSION_STRING`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Нажми "Запустить"

Готово! ✨

---

## 🔧 Отладка

### Wordstat не работает

```
ERROR: WORDSTAT_OAUTH_TOKEN not set
```

Решение: Убедись что переменная окружения установлена:
```bash
export WORDSTAT_OAUTH_TOKEN="your_token"
```

### Телеграм каналы не парсятся

```
ERROR: Missing Telethon credentials
```

Решение:
1. Запусти `python3 setup_session_auto.py <API_ID> <API_HASH> <PHONE>`
2. Сохрани `TELETHON_SESSION_STRING` в `.env`

### Бот не отправляет сообщения

1. Проверь `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`
2. Убедись что бот добавлен в чат с нужными правами
3. Проверь логи бота на bothost.ru

---

## 📊 Пример отчета

```
📊 Wordstat дайджест — 23.03.2024

📈 Сводка за неделю 16.03.2024 – 23.03.2024

Информационные запросы:
  Текущая неделя: 12 450
  Прошлая неделя: 11 890
  Изменение: +560 (+4.7%)

ТС ПИОТ — топ запросов
  🔍 тс пиот — 2 340
  🔍 модуль тс пиот — 890
  🔍 настройка тс пиот — 456
  ...

───────────────────────────────────

📊 Мониторинг Telegram-каналов

🔍 Ключевое слово: "тс пиот"
   Найдено упоминаний: 3

📱 РИА Новости
🔗 Ссылка: https://t.me/rian_ru/12345
📝 Текст: На рынке растет спрос на ТС ПИОТ решения...
🕐 Дата: 2024-03-23 10:30 UTC

📱 ТАСС
🔗 Ссылка: https://t.me/tass_agency/67890
📝 Текст: Компания запустила новый модуль ТС ПИОТ...
🕐 Дата: 2024-03-23 08:15 UTC
```

---

## 🔐 Безопасность

⚠️ **ВАЖНО:**

1. **Никогда не коммитьте `.env`** — добавьте в `.gitignore`
2. **На bothost используйте переменные окружения** вместо `.env`
3. **Session string — это как пароль** — не делитесь им
4. **Не загружайте `.env` на GitHub**

---

## 📚 Дополнительные ресурсы

- `QUICK_START.md` — быстрый старт (5 минут)
- `SETUP_GUIDE.md` — подробное руководство
- `config.yaml` — полная конфигурация
- Yandex Wordstat API: https://yandex.ru/dev/wordstat/
- Telethon docs: https://docs.telethon.dev/

---

## 📞 Поддержка

Если что-то не работает:

1. Проверь логи бота
2. Убедись что все credentials установлены
3. Попробуй запустить `--dry-run` для тестирования
4. Проверь `config.yaml` на синтаксические ошибки

---

**Ветка:** `production/wordstat-telegram-full`

**Версия:** 2.0 (Full-featured)

**Последнее обновление:** 2024-03-23
