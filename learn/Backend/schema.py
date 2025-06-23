from pydantic import BaseModel

# Schema for creating a new Item (used for POST/PUT requests)
class ItemCreate(BaseModel):
    name: str                    # Name of the item (required)
    price: float                 # Price of the item (required)
    description: str = None      # Optional description of the item

# Schema for reading/retrieving an Item (used for responses)
class ItemRead(ItemCreate):
    id: int                      # Unique identifier for the item (required in response)
    # Pydantic config: allow loading models from ORM objects (SQLAlchemy)
    model_config = {"from_attributes": True}
