import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy import select

from shared.models import Product, PriceHistory
from shared.price_parser import PriceParser
from shared.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class PriceScheduler:
    def __init__(self, db_url: str, bot_instance):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot_instance
        self.is_running = False
    
    def start(self):
        """Запускает планировщик"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        self.scheduler.add_job(
            self.check_all_prices,
            trigger=IntervalTrigger(hours=1),
            id='check_prices',
            replace_existing=True,
            next_run_time=datetime.now()
        )
        self.scheduler.start()
        self.is_running = True
        logger.info("🕒 Планировщик цен запущен (проверка каждый час)")
    
    async def check_all_prices(self):
        """Проверяет цены всех товаров в базе"""
        logger.info("🔍 Начинаем проверку цен...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product).where(Product.is_active == True)
            )
            products = result.scalars().all()
            logger.info(f"Найдено {len(products)} товаров для проверки")
            
            for product in products:
                try:
                    new_price = await PriceParser.get_price(product.url)
                    
                    if new_price is None:
                        logger.warning(f"Не удалось получить цену для товара {product.id}")
                        continue
                    
                    # Сохраняем в историю
                    history = PriceHistory(
                        product_id=product.id,
                        price=new_price
                    )
                    session.add(history)
                    
                    if new_price != product.current_price:
                        old_price = product.current_price
                        product.current_price = new_price
                        product.last_checked = datetime.utcnow()
                        logger.info(f"Товар {product.id}: цена изменилась {old_price} -> {new_price}")
                        
                        if new_price <= product.target_price:
                            await self.notify_price_drop(
                                user_id=product.user.telegram_id,
                                product=product,
                                old_price=old_price,
                                new_price=new_price
                            )
                    
                    product.last_checked = datetime.utcnow()
                    await session.commit()
                    
                except Exception as e:
                    logger.error(f"Ошибка проверки товара {product.id}: {e}")
                    await session.rollback()
                    continue
            
            logger.info("✅ Проверка цен завершена")
    
    async def notify_price_drop(self, user_id: int, product, old_price: float, new_price: float):
        """Отправляет уведомление о снижении цены"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        discount = ((old_price - new_price) / old_price) * 100
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Перейти к товару", url=product.url)],
                [InlineKeyboardButton(text="📊 История цен", callback_data=f"history_{product.id}")]
            ]
        )
        
        message = (
            f"🎉 **Цена снизилась!**\n\n"
            f"Товар: {product.url[:50]}...\n"
            f"Старая цена: {old_price:,.0f} ₽\n"
            f"Новая цена: {new_price:,.0f} ₽\n"
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
    
    def shutdown(self):
        """Останавливает планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🕒 Планировщик остановлен")
