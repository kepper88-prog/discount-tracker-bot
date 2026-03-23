import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update, delete
from datetime import datetime


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем модели и асинхронную БД
from shared.models import User, Product, PriceHistory
from shared.database import AsyncSessionLocal, engine, Base
from shared.config import settings
from scheduler import PriceScheduler

# Настройки из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальная переменная для планировщика
scheduler = None

# FSM для добавления товара
class AddProduct(StatesGroup):
    waiting_for_url = State()
    waiting_for_target_price = State()


# ========== ФУНКЦИИ ДЛЯ КЛАВИАТУР ==========

def get_main_keyboard():
    """Главное меню с inline-кнопками"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product"),
        InlineKeyboardButton(text="📋 Мои товары", callback_data="list_products")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
    )
    return builder.as_markup()


def get_product_actions_keyboard(product_id: int):
    """Клавиатура действий для конкретного товара"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data=f"check_{product_id}"),
        InlineKeyboardButton(text="📈 История", callback_data=f"history_{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить цену", callback_data=f"edit_{product_id}"),
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{product_id}")
    )
    return builder.as_markup()


def get_back_keyboard():
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()


# ========== ОБРАБОТЧИКИ КОМАНД ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    async with AsyncSessionLocal() as session:
        # Создаём или находим пользователя в БД
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(user)
            await session.commit()
            logger.info(f"Новый пользователь: @{message.from_user.username} (ID: {message.from_user.id})")

    welcome_text = (
        "🛍️ **Добро пожаловать в бот отслеживания скидок!**\n\n"
        "Я помогу вам следить за ценами на любимые товары. "
        "Как только цена упадёт ниже желаемой — я сразу сообщу!\n\n"
        "**Основные команды:**\n"
        "➕ Добавить товар — начать отслеживание\n"
        "📋 Мои товары — список отслеживаемых товаров\n"
        "❓ Помощь — показать все команды"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 **Справка по командам:**\n\n"
        "**/start** — запустить бота\n"
        "**/add** — добавить товар (пример: /add https://... 1000)\n"
        "**/list** — список ваших товаров\n"
        "**/remove <ID>** — удалить товар по ID\n"
        "**/check <ID>** — проверить цену сейчас\n"
        "**/stats** — статистика\n"
        "**/help** — эта справка\n\n"
        "Также вы можете использовать удобные кнопки в меню! 👆"
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats"""
    async with AsyncSessionLocal() as session:
        total_users = await session.execute(select(User))
        total_products = await session.execute(select(Product))
        user_products = await session.execute(
            select(Product).join(User).where(User.telegram_id == message.from_user.id)
        )
        
        stats_text = (
            "📊 **Статистика бота:**\n\n"
            f"👥 Всего пользователей: {len(total_users.all())}\n"
            f"📦 Всего товаров: {len(total_products.all())}\n"
            f"📋 Ваших товаров: {len(user_products.all())}\n\n"
            f"🕒 Проверка цен: каждый час"
        )
        await message.answer(stats_text, parse_mode="Markdown")


@dp.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    """Обработчик команды /add"""
    args = message.text.split()[1:]
    
    if len(args) == 0:
        await state.set_state(AddProduct.waiting_for_url)
        await message.answer(
            "🔗 Отправьте мне ссылку на товар:",
            reply_markup=get_back_keyboard()
        )
        return
    
    url = args[0]
    
    if len(args) >= 2:
        try:
            target_price = float(args[1])
            await add_product_to_db(message, url, target_price)
        except ValueError:
            await message.answer("❌ Целевая цена должна быть числом!")
    else:
        await state.update_data(url=url)
        await state.set_state(AddProduct.waiting_for_target_price)
        await message.answer(
            "💰 Укажите желаемую цену (в рублях):",
            reply_markup=get_back_keyboard()
        )


@dp.message(AddProduct.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    """Обработка ввода URL"""
    url = message.text.strip()
    await state.update_data(url=url)
    await state.set_state(AddProduct.waiting_for_target_price)
    await message.answer(
        "💰 Укажите желаемую цену (в рублях):",
        reply_markup=get_back_keyboard()
    )


@dp.message(AddProduct.waiting_for_target_price)
async def process_target_price(message: Message, state: FSMContext):
    """Обработка ввода целевой цены"""
    try:
        target_price = float(message.text)
        data = await state.get_data()
        url = data['url']
        await add_product_to_db(message, url, target_price)
        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 999.99)")


async def add_product_to_db(message: Message, url: str, target_price: float):
    """Добавляет товар в БД"""
    async with AsyncSessionLocal() as session:
        # Находим пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала используйте /start")
            return

        # Создаём товар
        product = Product(
            url=url,
            current_price=target_price,
            target_price=target_price,
            user_id=user.id
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

        # Пытаемся сразу получить актуальную цену
        from shared.price_parser import PriceParser
        actual_price = await PriceParser.get_price(url)
        if actual_price:
            product.current_price = actual_price
            await session.commit()
            price_info = f"\n💰 Текущая цена: {actual_price:,.0f} ₽"
        else:
            price_info = "\n⚠️ Не удалось получить текущую цену, бот проверит позже"

        await message.answer(
            f"✅ **Товар добавлен!**\n"
            f"🆔 ID: {product.id}\n"
            f"🎯 Целевая цена: {target_price:,.0f} ₽{price_info}",
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} добавил товар {product.id}")


@dp.message(Command("list"))
async def cmd_list(message: Message):
    """Показывает список отслеживаемых товаров"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.products:
            await message.answer(
                "📭 У вас пока нет отслеживаемых товаров.",
                reply_markup=get_main_keyboard()
            )
            return

        await message.answer("📋 **Ваши товары:**", parse_mode="Markdown")
        
        for product in user.products:
            short_url = product.url[:50] + "..." if len(product.url) > 50 else product.url
            
            product_text = (
                f"🆔 **ID:** {product.id}\n"
                f"🔗 **Ссылка:** `{short_url}`\n"
                f"💰 **Текущая цена:** {product.current_price:,.0f} ₽\n"
                f"🎯 **Целевая цена:** {product.target_price:,.0f} ₽\n"
                f"📅 **Добавлено:** {product.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            
            await message.answer(
                product_text,
                reply_markup=get_product_actions_keyboard(product.id),
                parse_mode="Markdown"
            )


@dp.message(Command("remove"))
async def cmd_remove(message: Message):
    """Удаляет товар по ID"""
    args = message.text.split()[1:]
    if len(args) != 1:
        await message.answer("❌ Использование: /remove <ID>")
        return

    try:
        product_id = int(args[0])
        async with AsyncSessionLocal() as session:
            # Находим пользователя
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return

            # Находим товар
            product_result = await session.execute(
                select(Product).where(
                    Product.id == product_id,
                    Product.user_id == user.id
                )
            )
            product = product_result.scalar_one_or_none()

            if product:
                await session.delete(product)
                await session.commit()
                await message.answer(f"✅ Товар с ID {product_id} удалён.")
                logger.info(f"Пользователь {message.from_user.id} удалил товар {product_id}")
            else:
                await message.answer("❌ Товар с таким ID не найден или не принадлежит вам.")
    except ValueError:
        await message.answer("❌ ID должен быть числом!")


@dp.message(Command("check"))
async def cmd_check(message: Message):
    """Принудительная проверка цены товара"""
    args = message.text.split()[1:]
    if len(args) != 1:
        await message.answer("❌ Использование: /check <ID>")
        return

    try:
        product_id = int(args[0])
        async with AsyncSessionLocal() as session:
            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                await message.answer("❌ Товар не найден")
                return
            
            await message.answer("🔄 Проверяю цену...")
            
            from shared.price_parser import PriceParser
            new_price = await PriceParser.get_price(product.url)
            
            if new_price:
                old_price = product.current_price
                product.current_price = new_price
                product.last_checked = datetime.utcnow()
                await session.commit()
                
                await message.answer(
                    f"✅ **Цена обновлена!**\n"
                    f"Было: {old_price:,.0f} ₽\n"
                    f"Стало: {new_price:,.0f} ₽",
                    parse_mode="Markdown"
                )
            else:
                await message.answer("❌ Не удалось получить цену. Попробуйте позже.")
                
    except ValueError:
        await message.answer("❌ ID должен быть числом!")


# ========== ОБРАБОТЧИКИ INLINE-КНОПОК ==========

@dp.callback_query(lambda c: c.data == "add_product")
async def callback_add_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.waiting_for_url)
    await callback.message.edit_text(
        "🔗 Отправьте мне ссылку на товар:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "list_products")
async def callback_list_products(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.products:
            await callback.message.edit_text(
                "📭 У вас пока нет отслеживаемых товаров.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "📋 **Ваши товары:**",
            parse_mode="Markdown"
        )
        
        for product in user.products[:5]:
            short_url = product.url[:30] + "..." if len(product.url) > 30 else product.url
            
            text = (
                f"🆔 **ID:** {product.id}\n"
                f"🔗 `{short_url}`\n"
                f"💰 {product.current_price:,.0f} ₽ / 🎯 {product.target_price:,.0f} ₽"
            )
            await callback.message.answer(
                text,
                reply_markup=get_product_actions_keyboard(product.id),
                parse_mode="Markdown"
            )
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "help")
async def callback_help(callback: CallbackQuery):
    await cmd_help(callback.message)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "stats")
async def callback_stats(callback: CallbackQuery):
    await cmd_stats(callback.message)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛍️ **Главное меню**",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("check_"))
async def callback_check_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        product_result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            await callback.message.answer("❌ Товар не найден")
            await callback.answer()
            return
        
        await callback.message.answer(f"🔄 Проверяю цену товара #{product_id}...")
        
        from shared.price_parser import PriceParser
        new_price = await PriceParser.get_price(product.url)
        
        if new_price:
            old_price = product.current_price
            product.current_price = new_price
            product.last_checked = datetime.utcnow()
            await session.commit()
            
            await callback.message.answer(
                f"✅ **Цена обновлена!**\n"
                f"#{product_id}: {old_price:,.0f} ₽ → {new_price:,.0f} ₽",
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(f"❌ Не удалось получить цену для товара #{product_id}")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def callback_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await callback.message.answer("❌ Пользователь не найден.")
            await callback.answer()
            return

        product_result = await session.execute(
            select(Product).where(
                Product.id == product_id,
                Product.user_id == user.id
            )
        )
        product = product_result.scalar_one_or_none()

        if product:
            await session.delete(product)
            await session.commit()
            await callback.message.answer(f"✅ Товар с ID {product_id} удалён.")
            logger.info(f"Пользователь {callback.from_user.id} удалил товар {product_id}")
        else:
            await callback.message.answer("❌ Товар с таким ID не найден или не принадлежит вам.")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("history_"))
async def callback_history_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        product_result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            await callback.message.answer("❌ Товар не найден")
            await callback.answer()
            return
        
        history_result = await session.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.created_at.desc())
            .limit(5)
        )
        history = history_result.scalars().all()
        
        if not history:
            await callback.message.answer("📊 История цен пока пуста")
        else:
            history_text = f"📊 **История цен товара #{product_id}:**\n\n"
            for record in history:
                history_text += f"• {record.created_at.strftime('%d.%m.%Y %H:%M')}: {record.price:,.0f} ₽\n"
            
            await callback.message.answer(history_text, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def callback_edit_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        product_result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            await callback.message.answer("❌ Товар не найден")
            await callback.answer()
            return
        
        await state.update_data(edit_product_id=product_id)
        
        await callback.message.answer(
            f"💰 Текущая целевая цена: {product.target_price:,.0f} ₽\n"
            "Введите новую целевую цену:",
            reply_markup=get_back_keyboard()
        )
    await callback.answer()


# Обработчик для ввода новой целевой цены при редактировании
@dp.message(lambda message: message.text and message.text.replace('.', '').replace(',', '').isdigit())
async def process_edit_price(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    
    if not product_id:
        return
    
    try:
        new_price = float(message.text.replace(',', '.'))
        
        async with AsyncSessionLocal() as session:
            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            if product:
                old_price = product.target_price
                product.target_price = new_price
                await session.commit()
                
                await message.answer(
                    f"✅ **Целевая цена обновлена!**\n"
                    f"Было: {old_price:,.0f} ₽\n"
                    f"Стало: {new_price:,.0f} ₽",
                    parse_mode="Markdown"
                )
                logger.info(f"Пользователь {message.from_user.id} изменил цену товара {product_id}")
            else:
                await message.answer("❌ Товар не найден")
            
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число")
    
    await state.clear()


# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

async def main():
    """Основная функция запуска бота"""
    global scheduler
    
    # Создаём таблицы, если их нет (асинхронно)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("🚀 Бот запускается...")
    
    # Инициализируем и запускаем планировщик
    scheduler = PriceScheduler(settings.DATABASE_URL, bot)
    scheduler.start()
    
    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен")
        if scheduler:
            scheduler.shutdown()
