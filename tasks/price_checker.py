import asyncio
import logging
from celery import chain, group
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import AsyncSessionLocal
from shared.models import Product, PriceHistory, Notification
from shared.price_parser import PriceParser
from bot.notifications import send_notification_task as send_notification
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.price_checker.check_product_price")
def check_product_price(product_id: int):
    """Проверка цены одного товара"""
    async def _check():
        async with AsyncSessionLocal() as session:
            # Получаем товар
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product or not product.is_active:
                return
            
            # Получаем новую цену
            new_price = await PriceParser.get_price(product.url)
            
            if new_price and new_price != product.current_price:
                old_price = product.current_price
                
                # Обновляем цену
                product.current_price = new_price
                product.last_checked = func.now()
                
                # Сохраняем в историю
                history = PriceHistory(
                    product_id=product.id,
                    price=new_price
                )
                session.add(history)
                
                # Проверяем, нужно ли уведомить
                if new_price <= product.target_price:
                    notification = Notification(
                        user_id=product.user_id,
                        product_id=product.id,
                        old_price=old_price,
                        new_price=new_price
                    )
                    session.add(notification)
                    
                    # Отправляем уведомление через Celery
                    send_notification.delay(
                        user_id=product.user_id,
                        product_id=product.id,
                        old_price=old_price,
                        new_price=new_price
                    )
                
                await session.commit()
                logger.info(f"✅ Товар {product_id}: {old_price} -> {new_price}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_check())

@celery_app.task(name="tasks.price_checker.check_all_prices")
def check_all_prices():
    """Запускает проверку всех активных товаров"""
    async def _get_products():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product.id).where(Product.is_active == True)
            )
            return [row[0] for row in result]
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    product_ids = loop.run_until_complete(_get_products())
    
    # Создаем группу задач для параллельной проверки
    job = group(check_product_price.s(pid) for pid in product_ids)
    result = job.apply_async()
    
    logger.info(f"🚀 Запущена проверка {len(product_ids)} товаров")
    return len(product_ids)

@celery_app.task(name="tasks.price_checker.cleanup_price_history")
def cleanup_price_history(days: int = 30):
    """Очищает старую историю цен"""
    async def _cleanup():
        async with AsyncSessionLocal() as session:
            from sqlalchemy import delete
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = delete(PriceHistory).where(
                PriceHistory.created_at < cutoff_date
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    deleted = loop.run_until_complete(_cleanup())
    logger.info(f"🧹 Удалено {deleted} записей истории цен")
    return deleted