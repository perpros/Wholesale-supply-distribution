from pydantic import BaseModel, validator, Field
from datetime import date
from typing import Optional

class ProductNeedRequestBase(BaseModel):
    product_type: str = Field(..., min_length=1)
    product_count: int = Field(..., gt=0)
    promised_delivery_date: date
    expiration_date: date

class ProductNeedRequestCreate(ProductNeedRequestBase):
    @validator('promised_delivery_date')
    def promised_date_must_be_in_future(cls, v):
        if v <= date.today():
            raise ValueError('Promised delivery date must be in the future')
        return v

    @validator('expiration_date')
    def expiration_date_must_be_after_promised_date(cls, v, values, **kwargs):
        if 'promised_delivery_date' in values and v <= values['promised_delivery_date']:
            raise ValueError('Expiration date must be after promised delivery date')
        return v

class ProductNeedRequest(ProductNeedRequestBase):
    id: int
    created_at: date # Should be datetime, will adjust later if DB stores datetime
    status: str

    class Config:
        orm_mode = True # Changed from from_attributes = True for Pydantic v1 compatibility if needed

class ProductNeedRequestSuccessResponse(BaseModel):
    message: str
    id: int
