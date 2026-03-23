import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import logging
from sqlalchemy import update
from sqlalchemy.sql import func
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def notify_price_drop(self, user_id: int, product, old_price: float, new_price: float):
        """
        Отправляет уведомление о снижении цены
        """
        # Рассчитываем скидку в процентах
        discount = ((old_price - new_price) / old_price) * 100
        
        # Создаём клавиатуру
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Перейти к товару", url=product.url)],
                [InlineKeyboardButton(text="📊 История цен", callback_data=f"history_{product.id}")]
            ]
        )
        
        message = (
            f"🎉 **Цена снизилась!**\n\n"
            f"Товар: {product.url[:50]}...\n"
            f"Старая цена: {old_price} ₽\n"
            f"Новая цена: {new_price} ₽\n"
            f"Скидка: {discount:.1f}%\n\n"
            f"Целевая цена достигнута!"
        )
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logger.info(f"Уведомление отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

# Добавь эту функцию в конец файла
async def send_notification(user_id: int, product_id: int, old_price: float, new_price: float):
    """
    Отправляет уведомление пользователю о снижении цены
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from shared.database import AsyncSessionLocal
    from shared.models import Product, User
    
    session = AsyncSessionLocal()
    try:
        # Получаем информацию о товаре
        from sqlalchemy import select
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return
        
        # Получаем бота из глобальной переменной (нужно будет передавать)
        from bot.main import bot
        
        # Рассчитываем скидку
        discount = ((old_price - new_price) / old_price) * 100
        
        # Создаём клавиатуру
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Перейти к товару", url=product.url)],
                [InlineKeyboardButton(text="📊 История цен", callback_data=f"history_{product_id}")]
            ]
        )
        
        message = (
            f"🎉 **Цена снизилась!**\n\n"
            f"💰 Старая цена: {old_price:,.0f} ₽\n"
            f"💰 Новая цена: {new_price:,.0f} ₽\n"
            f"📉 Скидка: {discount:.1f}%\n\n"
            f"✅ Целевая цена достигнута!"
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Обновляем статус уведомления в БД
        from shared.models import Notification
        stmt = (
            update(Notification)
            .where(Notification.product_id == product_id)
            .where(Notification.user_id == user_id)
            .values(is_sent=True, sent_at=func.now())
        )
        await session.execute(stmt)
        await session.commit()
        
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления: {e}")
    finally:
        await session.close()

# Celery задача для отправки уведомлений
@celery_app.task(name="tasks.notifications.send_notification")
def send_notification_task(user_id: int, product_id: int, old_price: float, new_price: float):
    """Celery задача для отправки уведомления"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        send_notification(user_id, product_id, old_price, new_price)
    )