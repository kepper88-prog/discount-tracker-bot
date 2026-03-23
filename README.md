<div align="center">

# 🛍️ Discount Tracker Bot

### *Telegram бот для автоматического отслеживания скидок*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge&logo=opensourceinitiative&logoColor=black)](LICENSE)

</div>

---

## 📖 О проекте

**Discount Tracker Bot** — это полноценная система для автоматического мониторинга цен на маркетплейсах. Пользователи добавляют ссылки на товары в Telegram-бота, устанавливают желаемую цену, а бот автоматически проверяет цены и присылает уведомление при снижении.

### 🎯 Ключевые возможности

| | |
|---|---|
| 🤖 **Telegram Bot** | Удобный интерфейс с inline-клавиатурами и поддержкой FSM |
| 🚀 **REST API** | Полноценное API с автодокументацией Swagger |
| ⏰ **Автоматическая проверка** | Фоновые задачи через Celery каждые 30 минут |
| 💾 **Надёжное хранение** | PostgreSQL + асинхронный SQLAlchemy |
| 🚦 **Мониторинг** | Prometheus метрики + Grafana дашборды |
| 🐳 **Контейнеризация** | Готовые Dockerfile и docker-compose |

---

## 🏗️ Архитектура
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Telegram │────▶│ FastAPI │────▶│ PostgreSQL │
│ Users │ │ API │ │ Database │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│ │ │
│ ▼ ▼
│ ┌─────────────────┐ ┌─────────────────┐
└──────────────▶│ Redis │ │ Celery │
│ Cache/Queue │ │ Worker │
└─────────────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────────────────────────────┐
│ Prometheus + Grafana │
│ Мониторинг │
└─────────────────────────────────────────┘

### Технологический стек

| Категория | Технологии |
|-----------|------------|
| **Язык** | Python 3.12 |
| **Telegram Bot** | aiogram 3.x |
| **REST API** | FastAPI + Swagger |
| **База данных** | PostgreSQL + asyncpg |
| **ORM** | SQLAlchemy 2.0 (асинхронный) |
| **Кэширование** | Redis |
| **Очереди задач** | Celery + Redis |
| **Парсинг** | BeautifulSoup4, requests, re |
| **Мониторинг** | Prometheus + Grafana |
| **Контейнеризация** | Docker, Docker Compose |

---

## 📱 Функционал

### 🤖 Telegram Bot

| Команда | Описание |
|---------|----------|
| `/start` | 🚀 Запуск бота и регистрация |
| `/add <URL> [цена]` | ➕ Добавить товар для отслеживания |
| `/list` | 📋 Список отслеживаемых товаров |
| `/remove <ID>` | ❌ Удалить товар по ID |
| `/check <ID>` | 🔄 Принудительная проверка цены |
| `/stats` | 📊 Статистика бота |
| `/help` | ❓ Справка |

### 🚀 REST API

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/api/users` | GET | 📋 Список пользователей |
| `/api/users/{id}/products` | GET | 📦 Товары пользователя |
| `/api/products` | GET/POST | ➕ Управление товарами |
| `/api/products/{id}` | GET/PUT/DELETE | 🔧 Работа с товаром |
| `/api/products/{id}/check` | POST | 🔄 Проверить цену |
| `/health` | GET | 💓 Статус сервиса |
| `/metrics` | GET | 📊 Prometheus метрики |

📚 **Интерактивная документация**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚀 Быстрый старт

### 📦 Локальный запуск

```bash
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

# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
# 6. Запуск приложения (в разных терминалах)

# Терминал 1: FastAPI
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Терминал 3: Telegram bot
python -m bot.main

📊 Мониторинг

После запуска доступны:
Сервис	               URL	                       Логин/Пароль
FastAPI	               http://localhost:8000	            -
Swagger Docs	       http://localhost:8000/docs           -
Prometheus	       http://localhost:9090	            -
Grafana	               http://localhost:3000	       admin/admin

📈 Метрики

    📊 Количество запросов к API

    ⏱️ Время ответа

    👥 Активные пользователи

    🔄 Количество проверок цен

    ❌ Ошибки и исключения

    💾 Использование Redis и PostgreSQL

🔧 Парсер цен

Поддерживаемые магазины

Магазин	           Статус	               Метод парсинга
Wildberries	        ⚠️	             API / требуется прокси
Ozon	            ⚠️	             JSON-LD / требуется прокси
Яндекс.Маркет	    ✅	             JSON-LD
Citilink	        ✅	             HTML + JSON
М.Видео	            ✅	             JSON
DNS	                ✅	             HTML + JSON
Любой другой	    ✅	             Универсальный парсер

    ⚠️ Важно: Wildberries и Ozon активно защищаются от автоматических запросов. Для production рекомендуется:

        Использовать прокси (настройка в .env: PROXY=http://user:pass@ip:port)

        Подключить сервисы обхода блокировок (ScrapingBee, ScrapingAnt)

        Использовать официальные API магазинов
        
        
       
    📁 Структура проекта
    
discount-tracker/
├── 📁 bot/                        # Telegram бот
│   ├── 📄 __init__.py
│   ├── 📄 main.py                 # Основная логика бота
│   └── 📄 notifications.py        # Уведомления
├── 📁 api/                        # REST API
│   ├── 📄 __init__.py
│   ├── 📄 main.py                 # FastAPI приложение
│   └── 📁 routes/                 # API эндпоинты
│       ├── 📄 users.py
│       └── 📄 products.py
├── 📁 shared/                     # Общие модули
│   ├── 📄 __init__.py
│   ├── 📄 models.py               # SQLAlchemy модели
│   ├── 📄 database.py             # Подключение к БД
│   ├── 📄 config.py               # Настройки
│   └── 📄 price_parser.py         # Парсер цен
├── 📁 tasks/                      # Фоновые задачи
│   ├── 📄 __init__.py
│   ├── 📄 celery_app.py           # Celery конфигурация
│   └── 📄 price_checker.py        # Проверка цен
├── 📄 docker-compose.yml          # Docker Compose
├── 📄 Dockerfile.bot              # Dockerfile для бота
├── 📄 Dockerfile.api              # Dockerfile для API
├── 📄 .env.example                # Пример переменных окружения
├── 📄 requirements.txt            # Зависимости
└── 📄 README.md                   # Документация

📈 Roadmap

    ✅ Выполнено

    Telegram бот с базовыми командами

    REST API с документацией Swagger

    PostgreSQL с асинхронным SQLAlchemy

    Redis + Celery для фоновых задач

    Docker-контейнеризация

    Prometheus метрики

    Поддержка 6+ маркетплейсов

🚀 В планах

    📊 Графики цен в боте

    📧 Email-уведомления

    🌐 Веб-интерфейс на React

    🔐 Аутентификация через Telegram

    📱 Мобильное приложение (Flutter)

    🧠 AI-прогнозирование цен
