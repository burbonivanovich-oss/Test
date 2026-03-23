# ⚡ Быстрый старт — RSS мониторинг (без SMS!)

## 3 шага до работающего бота

### 1️⃣ Установите зависимости

```bash
pip install -r requirements.txt
```

### 2️⃣ Запустите тест

```bash
python test_rss_monitor.py
```

Если видите сообщения из каналов → всё работает! ✅

### 3️⃣ Запустите полный бот

```bash
export WORDSTAT_OAUTH_TOKEN="your_wordstat_token"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="-1001234567890"

python wordstat_bot.py --config config.yaml
```

---

## ✅ Что получилось?

### Проблема (старая)
```
❌ Code verification failed: The confirmation code has expired
```

### Решение
- ✅ **Telethon заменен на RSS-Hub** (для каналов)
- ✅ **Нет SMS-авторизации**
- ✅ **Автоматический fallback**
- ✅ **Wordstat работает как раньше**

---

## 🔧 Что изменилось в коде?

| Компонент | До | Теперь |
|-----------|----|----|
| **Парсинг каналов** | Telethon (API) | RSS-Hub (по умолчанию) + Telethon (опция) |
| **Авторизация** | 🔑 SMS-код | ✅ Не нужна |
| **Публичные каналы** | ✅ Работают | ✅ Работают (быстрее) |
| **Надежность** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📊 Как это работает?

```
Telegram Channel (@rian_ru)
        ↓
    RSSHub API
        ↓
    RSS Feed (.xml)
        ↓
    feedparser парсит
        ↓
    Ищет ключевые слова
        ↓
    Отправляет в Telegram бот
```

**Это то же самое, что было в вашем рабочем проекте!** ✨

---

## 🚀 Что дальше?

### Протестировать конкретный канал

```bash
python test_rss_monitor.py --channel "@rian_ru" --keyword "тс пиот"
```

### Если нужен Telethon (скорость критична)

```bash
# 1. Получите API credentials: https://my.telegram.org/apps
# 2. Запустите setup (быстро! код действует 5 минут)
python channel_monitor_setup.py <API_ID> <API_HASH>

# 3. Скопируйте session string в .env
TELETHON_SESSION_STRING="1aBcD..."
```

---

## 📚 Документация

- `RSS_MONITORING_GUIDE.md` — полное руководство
- `test_rss_monitor.py` — примеры использования
- `config.yaml` — конфигурация каналов и ключевых слов

---

## 💡 Часто задаваемые вопросы

**В**: Почему RSS медленнее?
**О**: RSS обновляется раз в час. Для real-time используйте Telethon.

**В**: Приватные каналы работают?
**О**: RSS работает только с публичными. Для приватных нужен Telethon.

**В**: Почему не SMS-авторизация исчезла?
**О**: Потому что SMS-коды быстро истекают, а RSS работает стабильнее.

**В**: Сможет ли бот одновременно использовать RSS и Telethon?
**О**: Да! Если есть credentials — использует Telethon, иначе RSS.

---

**Готово!** 🎉 Бот работает без SMS-авторизации.
