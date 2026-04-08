# 📡 RSS-Based Channel Monitoring — Полное руководство

## 🎯 Что изменилось?

Добавлена **альтернатива Telethon** — RSS-Hub метод парсинга каналов Telegram, который:

✅ **Не требует SMS-авторизации**
✅ **Не требует сохранения сессии**
✅ **Работает с публичными каналами автоматически**
✅ **Стабилен и проверен** (подтверждено вашим старым проектом)
✅ **Автоматически используется как fallback**

---

## 🚀 Быстрый старт (RSS метод)

### Вариант 1: Просто запустите бот без Telethon (Рекомендуется)

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите бот — он автоматически использует RSS
python wordstat_bot.py --config config.yaml
```

**Готово!** Мониторинг каналов включится автоматически через RSS.

---

## 🔧 Метод 1: RSS-Hub (по умолчанию)

### Как это работает?

1. Бот запрашивает RSS-feeds у RSSHub (список инстансов: `rsshub.app`, `rsshub.rssforever.com`, `rsshub.uneasy.win`)
2. RSSHub преобразует Telegram-канал в RSS-feed
3. Бот парсит feed и ищет ключевые слова
4. Отправляет результаты в Telegram

### Конфигурация

В `config.yaml` каналы указаны как обычно:

```yaml
channel_monitor:
  enabled: true
  channels:
    - name: "РИА Новости"
      username: "@rian_ru"
    - name: "ТАСС"
      username: "@tass_agency"

  keywords:
    - "тс пиот"
    - "ТС ПИОТ"
```

**Важно:** Работает только с **публичными каналами** (доступ без подписки).

### Плюсы и минусы

| Плюс | Минус |
|------|-------|
| Нет авторизации | Нужен доступ к интернету |
| Быстрая настройка | RSS может быть отсроченным на часы |
| Стабильно | Зависит от RSSHub инстансов |
| Поддержка истории | - |

---

## 🔑 Метод 2: Telethon (Прямой API)

Если хотите **более быстрый и надежный** доступ, используйте Telethon.

### Проблема с авторизацией (от которой мы уходим)

❌ **"The confirmation code has expired"** — код действует ~5 минут
❌ **Требует интерактивного ввода** — между Stage 1 и Stage 2 может пройти время
❌ **Проблемы с macOS** — сетевые таймауты при подключении

### Как это работает (правильно)

```bash
# Stage 1: Запросить код
python channel_monitor_setup.py <API_ID> <API_HASH>
# ⏱️ НЕМЕДЛЕННО скопируйте код из Telegram!

# Stage 2: Ввести код ВЫ ПРИ СЕЙЧАС
# Введите код: 62190
```

### Подготовка (если захотите использовать Telethon)

1. Получите API credentials на https://my.telegram.org/apps
2. Запустите setup **на быстром интернете**:
   ```bash
   python channel_monitor_setup.py 37195258 da6a76c5c4884bceac2fa904ab029b02
   ```
3. Немедленно скопируйте код из Telegram
4. Сохраните session string в `.env`:
   ```
   TELETHON_API_ID=37195258
   TELETHON_API_HASH=da6a76c5c4884bceac2fa904ab029b02
   TELETHON_SESSION_STRING=1aBcD...
   ```

### Что изменилось в коде

Теперь `create_monitor()` **автоматически**:
1. **Пробует** Telethon, если credentials есть
2. **Падает на RSS**, если Telethon не удался или credentials отсутствуют

```python
# В wordstat_bot.py — просто вызовите!
channel_monitor = await create_monitor()
# Все работает автоматически ✨
```

---

## 📊 Сравнение методов

| Параметр | Telethon | RSS-Hub |
|----------|----------|---------|
| **Скорость** | ⚡ Быстро (прямой API) | 🐢 Медленнее (RSS feed) |
| **Авторизация** | 🔑 Нужна SMS-верификация | ✅ Не нужна |
| **Настройка** | ⚙️ Сложная (setup скрипт) | ✅ Автоматическая |
| **Надежность** | ⭐ Очень надежно | ⭐ Надежно |
| **История сообщений** | 📜 Весь архив | 📜 ~100 последних |
| **Приватные каналы** | 🔐 Поддерживает | ❌ Только публичные |

---

## 🛠️ Решение проблем

### RSS не работает

```
⚠️  Could not fetch RSS for @channel_name
```

**Решение:**
1. Канал приватный? → Используйте только публичные каналы для RSS
2. RSSHub down? → Проверьте инстансы вручную:
   ```bash
   curl https://rsshub.app/telegram/channel/rian_ru
   ```
3. Нет интернета? → Проверьте сетевое соединение

### Telethon авторизация не работает

```
❌ Code verification failed: The confirmation code has expired
```

**Решение:**
1. **Не вводите код вручную** — используйте stdin:
   ```bash
   echo "62190" | python channel_monitor_setup.py <API_ID> <API_HASH> <PHONE>
   ```

2. **Или** — просто используйте RSS (рекомендуется)

---

## 💡 Рекомендации

### Для большинства пользователей:
✅ **RSS-Hub (по умолчанию)**
- Просто установите и запустите
- Нет сложной настройки
- Работает надежно

### Если вам нужна скорость:
🔑 **Telethon (продвинутое)**
- Для продакшена
- Когда скорость критична
- Когда вам нужны приватные каналы

---

## 📝 Примеры использования

### Пример 1: Полностью RSS (рекомендуется)

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Отредактируйте config.yaml (channels, keywords)

# 3. Установите переменные окружения
export WORDSTAT_OAUTH_TOKEN="your_token"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="-1001234567890"

# 4. Запустите
python wordstat_bot.py --config config.yaml
```

### Пример 2: Комбинированный (Telethon + fallback RSS)

```bash
# 1. Подготовьте Telethon credentials (если хотите)
export TELETHON_API_ID=37195258
export TELETHON_API_HASH=da6a76c...
export TELETHON_SESSION_STRING=1aBcD...

# 2. Установите остальное
export WORDSTAT_OAUTH_TOKEN="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID=...

# 3. Запустите — бот выберет лучший метод
python wordstat_bot.py --config config.yaml
```

---

## 📌 Что помню из вашего проекта?

Ваш старый код использовал ровно этот же подход:

```python
# Ваш рабочий код:
async def fetch_telegram_messages(channels, keywords, hours_back=24):
    for channel in channels:
        rss_url = f"{instance}/telegram/channel/{clean_name}"
        # ... парсить RSS feed ...
        # Ищет ключевые слова в текстах
```

**Я скопировал этот подход** в `rss_channel_monitor.py` — это **то же самое, что работало у вас**.

---

## 🚀 Следующие шаги

1. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Отредактируйте config.yaml**:
   - Добавьте свои каналы
   - Установите ключевые слова

3. **Запустите**:
   ```bash
   python wordstat_bot.py --config config.yaml
   ```

4. **Если нужен Telethon** (факультативно):
   ```bash
   python channel_monitor_setup.py <API_ID> <API_HASH>
   ```

---

## 📞 Вопросы?

Код сейчас:
- ✅ Использует RSS по умолчанию (работает везде)
- ✅ Поддерживает Telethon как опцию (если credentials есть)
- ✅ Автоматически выбирает лучший метод
- ✅ Имеет fallback для надежности

**Просто запустите и пользуйтесь!** 🎉
