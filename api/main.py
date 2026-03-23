from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging

from shared.database import engine, Base
from shared.database import engine
from shared.config import settings
from api.routes import users, products

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Действия при запуске и остановке"""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Подключаемся к Redis
    app.state.redis = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    logger.info("✅ API запущен")
    yield
    
    # Закрываем соединения
    await engine.dispose()
    await app.state.redis.close()
    logger.info("🛑 API остановлен")

# Создаем приложение
app = FastAPI(
    title="Discount Tracker API",
    description="API для управления отслеживанием скидок",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(products.router, prefix="/api/products", tags=["products"])

@app.get("/")
async def root():
    return {
        "service": "Discount Tracker API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    # Проверка Redis
    redis_ok = False
    try:
        await app.state.redis.ping()
        redis_ok = True
    except:
        pass
    
    # Проверка БД
    db_ok = False
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))  # ← ОТСТУП 4 ПРОБЕЛА
            db_ok = True
    except Exception as e:
        print(f"DB Error: {e}")
    
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus метрики"""
    from prometheus_client import generate_latest, REGISTRY
    return generate_latest(REGISTRY)