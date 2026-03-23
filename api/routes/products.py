from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional

from shared.database import get_db
from shared import models, schemas
from tasks.price_checker import check_product_price

router = APIRouter()

@router.get("/", response_model=List[schemas.Product])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список товаров"""
    query = select(models.Product)
    
    if user_id:
        query = query.where(models.Product.user_id == user_id)
    if is_active is not None:
        query = query.where(models.Product.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{product_id}", response_model=schemas.Product)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить товар по ID"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=schemas.Product, status_code=201)
async def create_product(
    product: schemas.ProductCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый товар"""
    # Проверяем пользователя
    user_result = await db.execute(
        select(models.User).where(models.User.id == product.user_id)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Создаем товар
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Запускаем первую проверку цены
    background_tasks.add_task(check_product_price.delay, db_product.id)
    
    return db_product

@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить товар"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    
    await db.commit()
    await db.refresh(product)
    return product

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить товар"""
    result = await db.execute(
        delete(models.Product).where(models.Product.id == product_id)
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted"}

@router.post("/{product_id}/check")
async def check_price_now(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Запустить проверку цены сейчас"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")
    
    background_tasks.add_task(check_product_price.delay, product_id)
    return {"message": "Price check started"}

@router.get("/{product_id}/history", response_model=List[schemas.PriceHistory])
async def get_product_history(
    product_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Получить историю цен товара"""
    from sqlalchemy import desc
    
    result = await db.execute(
        select(models.PriceHistory)
        .where(models.PriceHistory.product_id == product_id)
        .order_by(desc(models.PriceHistory.created_at))
        .limit(limit)
    )
    return result.scalars().all()