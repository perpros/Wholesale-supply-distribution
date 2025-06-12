from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func # For server-side default timestamp
from app.db.base_class import Base # Assuming Base is defined in app.db.base_class

class ProductNeedRequest(Base):
    __tablename__ = "product_need_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String(255), nullable=False) # Specify length for String
    product_count = Column(Integer, nullable=False)
    promised_delivery_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, default="Submitted")
