# 🛍️ Discount Tracker Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.3-green.svg)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Telegram-бот для отслеживания скидок с REST API и фоновыми задачами. Автоматически проверяет цены и уведомляет пользователя при достижении целевой цены.

## ✨ Возможности

- ✅ **Telegram Bot** — удобный интерфейс для пользователей
- ✅ **REST API** — управление через Swagger документацию
- ✅ **Автоматическая проверка цен** — каждый час
- ✅ **Уведомления** — при достижении целевой цены
- ✅ **Поддержка магазинов** — Wildberries, Ozon, Яндекс.Маркет, Citilink, М.Видео, DNS
- ✅ **История цен** — отслеживание изменений
- ✅ **Inline-клавиатуры** — удобное управление
- ✅ **Мониторинг** — Prometheus метрики + Grafana

## 🏗️ Архитектура
┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ Telegram │────▶│ FastAPI │────▶│ PostgreSQL │
│ Users │ │ API │ │ Database │
└─────────────┘ └──────────────┘ └─────────────┘
│ │
▼ ▼
┌──────────────┐ ┌─────────────┐
│ Redis │ │ Celery │
│ Cache/Queue│ │ Worker │
└──────────────┘ └─────────────┘

## 🛠️ Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Язык** | Python 3.12 | Основной язык разработки |
| **Telegram Bot** | aiogram 3.x | Асинхронный фреймворк для ботов |
| **REST API** | FastAPI + Swagger | Документированное API |
| **База данных** | PostgreSQL + asyncpg | Основное хранилище |
| **ORM** | SQLAlchemy 2.0 | Асинхронная работа с БД |
| **Кэширование** | Redis | Кэш и брокер сообщений |
| **Фоновые задачи** | Celery + Redis | Периодическая проверка цен |
| **Мониторинг** | Prometheus + Grafana | Сбор и визуализация метрик |
| **Контейнеризация** | Docker + docker-compose | Упаковка и деплой |

## 📦 Установка и запуск

### Локальный запуск

```bash
# 1. Клонирование репозитория
git clone https://github.com/kepper88-prog/discount-tracker-bot.git
cd discount-tracker-bot

# 2. Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env, добавьте BOT_TOKEN

# 5. Запуск PostgreSQL и Redis
docker-compose up -d postgres redis

# 6. Запуск приложения
# Терминал 1: FastAPI
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Терминал 3: Telegram bot
python -m bot.main

# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

📱 Использование
Telegram Bot
Команда	Описание	Пример
/start	Начать работу	/start
/add <URL> [цена]	Добавить товар	/add https://... 5000
/list	Список товаров	/list
/remove <ID>	Удалить товар	/remove 123
/check <ID>	Проверить цену сейчас	/check 123
/stats	Статистика	/stats
REST API

После запуска API доступно по адресу: http://localhost:8000

    📚 Документация: http://localhost:8000/docs

    📊 Метрики: http://localhost:8000/metrics

    💓 Health check: http://localhost:8000/health

📊 Мониторинг
Сервис	URL	Логин/Пароль
Prometheus	http://localhost:9090	-
Grafana	        http://localhost:3000	admin/admin
🔧 Парсер цен

⚠️ Важно: Современные маркетплейсы (Ozon, Wildberries, Яндекс.Маркет) активно защищаются от автоматических запросов.
В текущей версии парсер корректно обрабатывает отказ и не нарушает работу основного функционала.

Для production-использования рекомендуется:

    Использовать прокси (настройка в .env: PROXY=http://user:pass@ip:port)

    Подключить сервисы обхода блокировок (ScrapingBee, ScrapingAnt)

    Использовать официальные API магазинов (где доступны)

Поддерживаемые магазины:

    ✅ Wildberries — API (требуется обход)

    ✅ Ozon — JSON-LD (требуется обход)

    ✅ Citilink, М.Видео, DNS — базовый парсинг

    ✅ Универсальный парсер — для любых других сайтов

📁 Структура проекта
discount-tracker/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Telegram бот
│   └── notifications.py     # Уведомления
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   └── routes/              # API эндпоинты
├── shared/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy модели
│   ├── database.py          # Подключение к БД
│   └── price_parser.py      # Парсер цен
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py        # Celery конфигурация
│   └── price_checker.py     # Фоновые задачи
├── docker-compose.yml
├── Dockerfile.bot
├── Dockerfile.api
├── .env.example
├── requirements.txt
└── README.md

📈 Roadmap

    Telegram бот с базовыми командами

    REST API с документацией

    PostgreSQL с SQLAlchemy

    Redis + Celery для фоновых задач

    Docker-контейнеризация

    Prometheus метрики

    📊 Графики цен в боте

    📧 Email-уведомления

    🌐 Веб-интерфейс на React

    🔐 Аутентификация через Telegram
    
    Telegram: @discount_pro_2026_bot

    GitHub: @kepper88-prog
