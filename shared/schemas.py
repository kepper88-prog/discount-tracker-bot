from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    user_id: int
    url: str
    target_price: float = Field(gt=0)
    name: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    url: Optional[str] = None
    target_price: Optional[float] = Field(gt=0, default=None)
    name: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    current_price: float
    last_checked: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# PriceHistory schemas
class PriceHistoryBase(BaseModel):
    product_id: int
    price: float

class PriceHistoryCreate(PriceHistoryBase):
    pass

class PriceHistory(PriceHistoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Notification schemas
class NotificationBase(BaseModel):
    user_id: int
    product_id: int
    old_price: float
    new_price: float

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True