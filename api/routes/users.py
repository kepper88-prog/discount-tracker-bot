from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from shared.database import get_db
from shared import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список пользователей"""
    result = await db.execute(
        select(models.User).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{user_id}", response_model=schemas.User)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить пользователя по ID"""
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/products", response_model=List[schemas.Product])
async def get_user_products(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить товары пользователя"""
    result = await db.execute(
        select(models.Product).where(models.Product.user_id == user_id)
    )
    return result.scalars().all()

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить пользователя"""
    from sqlalchemy import delete
    
    result = await db.execute(
        delete(models.User).where(models.User.id == user_id)
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted"}