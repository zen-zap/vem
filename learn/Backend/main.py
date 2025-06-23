from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from model import Item
from schema import ItemCreate, ItemRead

# Create all database tables as defined by the SQLAlchemy models
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app instance
app = FastAPI()

# ----------------------------- #
#         CRUD Endpoints        #
# ----------------------------- #

# Create a new item in the database
@app.post("/items/", response_model=ItemRead)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # Convert the Pydantic model to a dictionary and use it to create a SQLAlchemy Item instance
    db_item = Item(**item.model_dump())
    db.add(db_item)         # Add the new item to the session
    db.commit()             # Commit the transaction (save to DB)
    db.refresh(db_item)     # Refresh the instance to get the new DB-generated values (like id)
    return db_item          # Respond with the created item

# Get a list of all items in the database
@app.get("/items/", response_model=List[ItemRead])
def read_items(db: Session = Depends(get_db)):
    return db.query(Item).all()  # Query for all items and return as a list

# Get a specific item by its ID
@app.get("/items/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()  # Query for the item with the given id
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # 404 error if not found
    return item

# Update an existing item by its ID
@app.put("/items/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item_update: ItemCreate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()   # Query for the item with the given id
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # 404 error if not found
    # Update each field of the item with the new data
    for field, value in item_update.model_dump().items():
        setattr(item, field, value)
    db.commit()         # Save changes to the database
    db.refresh(item)    # Refresh to get new state from DB
    return item

# Delete an item by its ID
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()   # Query for the item with the given id
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # 404 error if not found
    db.delete(item)     # Remove the item from the database
    db.commit()         # Save changes to the database
    return {"detail": "Item deleted"}   # Confirmation message after deletion
