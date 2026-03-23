<div align="center">

# 🛍️ Discount Tracker Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.3-green.svg?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)

</div>

---

## 📖 О проекте

**Discount Tracker Bot** — это полноценная система для автоматического отслеживания скидок на маркетплейсах. Пользователи добавляют ссылки на товары в Telegram-бота, устанавливают желаемую цену, а бот проверяет цены каждый час и присылает уведомление при достижении целевой цены.

### 🎯 Ключевые особенности

| Особенность | Описание |
|-------------|----------|
| 🤖 **Telegram Bot** | Удобный интерфейс с inline-клавиатурами и поддержкой FSM |
| 🚀 **REST API** | Полноценное API с автодокументацией Swagger |
| ⏰ **Фоновые задачи** | Автоматическая проверка цен через Celery каждые 30 минут |
| 💾 **Надёжное хранение** | PostgreSQL + асинхронный SQLAlchemy |
| 🚦 **Мониторинг** | Prometheus метрики + Grafana дашборды |
| 🐳 **Контейнеризация** | Готовые Dockerfile и docker-compose |

---

## 🏗️ Архитектура

```mermaid
graph TB
    subgraph "Пользователи"
        A[Telegram Users]
        B[Web Clients]
    end
    
    subgraph "Сервисы"
        C[Telegram Bot<br/>aiogram 3.x]
        D[FastAPI<br/>REST API]
        E[Celery Worker<br/>Фоновые задачи]
    end
    
    subgraph "Хранилища"
        F[(PostgreSQL)]
        G[(Redis)]
    end
    
    subgraph "Мониторинг"
        H[Prometheus]
        I[Grafana]
    end
    
    A --> C
    B --> D
    C --> F
    D --> F
    D --> G
    E --> G
    E --> F
    D --> H
    H --> I
    
    Технологический стек
Категория	Технологии
Язык	Python 3.12
Telegram Bot	aiogram 3.x
REST API	FastAPI + Swagger
База данных	PostgreSQL + asyncpg
ORM	SQLAlchemy 2.0 (асинхронный)
Кэширование	Redis
Очереди задач	Celery + Redis
Парсинг	BeautifulSoup4, requests, re
Мониторинг	Prometheus + Grafana
Контейнеризация	Docker, Docker Compose
📱 Функционал
Telegram Bot
Команда	Описание	Пример
/start	Запуск бота и регистрация	/start
/add <URL> [цена]	Добавить товар для отслеживания	/add https://... 5000
/list	Показать список отслеживаемых товаров	/list
/remove <ID>	Удалить товар по ID	/remove 123
/check <ID>	Принудительная проверка цены	/check 123
/stats	Статистика бота	/stats
/help	Справка	/help
REST API

После запуска API доступно по адресу: http://localhost:8000
Эндпоинт	Метод	Описание
/api/users	GET	Список пользователей
/api/users/{id}/products	GET	Товары пользователя
/api/products	GET/POST	Управление товарами
/api/products/{id}	GET/PUT/DELETE	Работа с товаром
/api/products/{id}/check	POST	Проверить цену
/health	GET	Статус сервиса
/metrics	GET	Prometheus метрики

📚 Интерактивная документация: http://localhost:8000/docs
🚀 Быстрый старт
Локальный запуск
bash

# 1. Клонирование репозитория
git clone https://github.com/kepper88-prog/discount-tracker-bot.git
cd discount-tracker-bot

# 2. Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env, добавьте BOT_TOKEN от @BotFather

# 5. Запуск PostgreSQL и Redis
docker-compose up -d postgres redis

# 6. Запуск приложения (в разных терминалах)
# Терминал 1: FastAPI
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Терминал 3: Telegram bot
python -m bot.main

Запуск через Docker
bash

# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

📊 Мониторинг

После запуска доступны:
Сервис	URL	Логин/Пароль
FastAPI	http://localhost:8000	-
Swagger Docs	http://localhost:8000/docs	-
Prometheus	http://localhost:9090	-
Grafana	http://localhost:3000	admin/admin
Метрики

    Количество запросов к API

    Время ответа

    Активные пользователи

    Количество проверок цен

    Ошибки и исключения

    Использование Redis и PostgreSQL

🔧 Парсер цен
Поддерживаемые магазины
Магазин	Статус	Метод парсинга
Wildberries	⚠️	API / требуется прокси
Ozon	⚠️	JSON-LD / требуется прокси
Яндекс.Маркет	✅	JSON-LD
Citilink	✅	HTML + JSON
М.Видео	✅	JSON
DNS	✅	HTML + JSON
Любой другой	✅	Универсальный парсер

    ⚠️ Важно: Wildberries и Ozon активно защищаются от автоматических запросов. Для production рекомендуется:

        Использовать прокси (настройка в .env: PROXY=http://user:pass@ip:port)

        Подключить сервисы обхода блокировок (ScrapingBee, ScrapingAnt)

        Использовать официальные API магазинов

📁 Структура проекта
text

discount-tracker/
├── bot/                        # Telegram бот
│   ├── __init__.py
│   ├── main.py                 # Основная логика бота
│   └── notifications.py        # Уведомления
├── api/                        # REST API
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   └── routes/                 # API эндпоинты
│       ├── users.py
│       └── products.py
├── shared/                     # Общие модули
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy модели
│   ├── database.py             # Подключение к БД
│   ├── config.py               # Настройки
│   └── price_parser.py         # Парсер цен
├── tasks/                      # Фоновые задачи
│   ├── __init__.py
│   ├── celery_app.py           # Celery конфигурация
│   └── price_checker.py        # Проверка цен
├── docker-compose.yml          # Docker Compose
├── Dockerfile.bot              # Dockerfile для бота
├── Dockerfile.api              # Dockerfile для API
├── .env.example                # Пример переменных окружения
├── requirements.txt            # Зависимости
└── README.md                   # Документация

📈 Roadmap

    Telegram бот с базовыми командами

    REST API с документацией

    PostgreSQL с асинхронным SQLAlchemy

    Redis + Celery для фоновых задач

    Docker-контейнеризация

    Prometheus метрики

    Поддержка 6+ маркетплейсов

    📊 Графики цен в боте

    📧 Email-уведомления

    🌐 Веб-интерфейс на React

    🔐 Аутентификация через Telegram

    📱 Мобильное приложение (Flutter)

🤝 Как внести вклад

Буду рад любым предложениям и улучшениям!

    Форкните репозиторий

    Создайте ветку для фичи: git checkout -b feature/amazing-feature

    Закоммитьте изменения: git commit -m 'Add amazing feature'

    Запушьте ветку: git push origin feature/amazing-feature

    Откройте Pull Request

📄 Лицензия

Проект распространяется под лицензией MIT. Подробнее в файле LICENSE.
📬 Контакты
	
Telegram Bot	@discount_pro_2026_bot
GitHub	@kepper88-prog
Email	your-email@example.com
<div align="center">
