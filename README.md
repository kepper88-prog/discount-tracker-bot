<div align="center">

# 🛍️ Discount Tracker Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.3-green.svg)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![GitHub last commit](https://img.shields.io/github/last-commit/kepper88-prog/discount-tracker-bot)](https://github.com/kepper88-prog/discount-tracker-bot)
[![GitHub stars](https://img.shields.io/github/stars/kepper88-prog/discount-tracker-bot)](https://github.com/kepper88-prog/discount-tracker-bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/kepper88-prog/discount-tracker-bot)](https://github.com/kepper88-prog/discount-tracker-bot/network)
[![GitHub issues](https://img.shields.io/github/issues/kepper88-prog/discount-tracker-bot)](https://github.com/kepper88-prog/discount-tracker-bot/issues)

[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/discount_pro_2026_bot)
[![API Docs](https://img.shields.io/badge/API-Swagger-brightgreen.svg)](http://localhost:8000/docs)

</div>

Telegram-бот для отслеживания скидок с REST API и фоновыми задачами. Автоматически проверяет цены на Wildberries, Ozon, Яндекс.Маркете и уведомляет пользователя при достижении целевой цены.

## ✨ Возможности

- ✅ **Telegram Bot** — удобный интерфейс для пользователей
- ✅ **REST API** — управление через Swagger документацию
- ✅ **Автоматическая проверка цен** — каждый час
- ✅ **Уведомления** — при достижении целевой цены
- ✅ **Поддержка магазинов** — Wildberries, Ozon, Яндекс.Маркет
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
git clone https://github.com/YOUR_USERNAME/discount-tracker-bot.git
cd discount-tracker-bot

# 2. Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env, добавьте BOT_TOKEN

# 5. Запуск PostgreSQL и Redis (через Docker)
docker-compose up -d postgres redis

# 6. Запуск приложения
# Терминал 1: FastAPI
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Терминал 3: Telegram bot
python -m bot.main
