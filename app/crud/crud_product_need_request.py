from sqlalchemy.orm import Session
from app.models.product_need_request import ProductNeedRequest as ProductNeedRequestModel
from app.schemas.product_need_request import ProductNeedRequestCreate as ProductNeedRequestCreateSchema

def create_product_need_request(db: Session, *, request_in: ProductNeedRequestCreateSchema) -> ProductNeedRequestModel:
    """
    Create a new product need request.
    """
    db_obj = ProductNeedRequestModel(
        product_type=request_in.product_type,
        product_count=request_in.product_count,
        promised_delivery_date=request_in.promised_delivery_date,
        expiration_date=request_in.expiration_date
        # created_at and status have defaults in the model
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
