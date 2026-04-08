# Развертывание на bothost.ru

## Шаг 1: Подготовка API ключей Telegram

1. Зайди на https://my.telegram.org/apps
2. Авторизуйся с номером телефона
3. Создай приложение (App title, Short name)
4. Получи:
   - **API_ID**
   - **API_HASH**

## Шаг 2: Получение Session String

### Локально на своем компьютере:

```bash
# Клонируй репо
git clone https://github.com/burbonivanovich-oss/Test.git
cd Test

# Установи зависимости
pip install -r requirements.txt

# Запусти скрипт аутентификации
python3 channel_monitor_setup.py <API_ID> <API_HASH>
```

Пример:
```bash
python3 channel_monitor_setup.py 12345678 abcdef1234567890abcdef1234567890
```

**Скрипт попросит:**
1. Номер телефона (с кодом страны: +7...)
2. Код подтверждения из Telegram

**Выведет:**
```
export TELETHON_SESSION_STRING="1BVtsOKJ9HKe3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5..."
```

Скопируй эту строку полностью (всю длинную строку после `=`)

## Шаг 3: Загрузка на bothost.ru

1. На bothost.ru создай бота или обнови существующий
2. Загрузи все файлы проекта:
   ```
   - wordstat_bot.py (основной файл бота)
   - config.yaml
   - requirements.txt
   - telegram_channel_monitor/ (папка)
   - .env.example
   - .gitignore
   ```

3. В панели bothost.ru, раздел **"Environment Variables"**, добавь переменные:

| Переменная | Значение |
|---|---|
| `TELETHON_API_ID` | `12345678` (твой API_ID) |
| `TELETHON_API_HASH` | `abcdef1234567890abcdef1234567890` (твой API_HASH) |
| `TELETHON_SESSION_STRING` | `1BVtsOKJ9HKe3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5...` (весь session_string) |

## Шаг 4: Запуск

1. На bothost.ru нажми **"Запустить"** или **"Restart"**
2. Проверь логи
3. Бот начнет мониторить каналы!

## Что мониторит бот?

**Каналы:**
- РИА Новости (@rian_ru)
- ТАСС (@tass_agency)
- РБК (@rbc_news)
- Коммерсант (@kommersant)
- 1C (@1c_rus)
- InfoStart (@infostart_news)
- СБИС (@sbis_news)
- Честный знак (@chestnyznak_official)
- АТОЛ (@atol_online)
- МойСклад (@moysklad_news)
- EcomCrew (@ecomcrew)
- Habr (@habr_com)

**Ключевые слова:**
- тс пиот
- ТС ПИОТ

## Устранение неполадок

- **Ошибка подключения**: Проверь API_ID и API_HASH
- **Session expired**: Получи новый session_string локально
- **Канал не найден**: Убедись, что канал публичный и имя написано правильно

## Дополнительно

Конфиг находится в `config.yaml`. Там можно изменить:
- Список каналов
- Ключевые слова
- Расписание мониторинга
