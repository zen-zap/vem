import streamlit as st
import requests
import pandas as pd

# Backend API endpoint for CRUD operations on items
API_URL = "http://127.0.0.1:8000/items/"

# Set the title of the Streamlit web app
st.title("CRUD Application")

# Function to fetch all items from the backend API
def fetch_items():
    response = requests.get(API_URL)
    if response.status_code == 200:
        # If the request is successful, return the list of items
        return response.json()
    return []  # Return empty list if request fails

# Function to update an item by its ID (PUT request)
def update_item(item_id, name, price, description):
    payload = {"name": name, "price": price, "description": description}
    # Send updated data to the backend API
    return requests.put(f"{API_URL}{item_id}", json=payload)

# Function to delete an item by its ID (DELETE request)
def delete_item(item_id):
    return requests.delete(f"{API_URL}{item_id}")

# Function to insert a new item (POST request)
def insert_item(name, price, description):
    payload = {"name": name, "price": price, "description": description}
    return requests.post(API_URL, json=payload)

# Fetch the list of items from the backend
items = fetch_items()

# Initialize session state for the edit form if it doesn't exist
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None

# ---------- Insert Item Section ----------
with st.expander("Add New Item"):
    with st.form("insert_form"):
        # Input fields for new item
        new_name = st.text_input("Name", key="insert_name")
        new_price = st.number_input("Price", min_value=0.0, format="%.2f", key="insert_price")
        new_description = st.text_area("Description", key="insert_description")
        insert_submitted = st.form_submit_button("Insert Item")
        if insert_submitted:
            # Send the new item to the backend
            res = insert_item(new_name, new_price, new_description)
            if res.status_code in [200, 201]:
                st.success("Item inserted successfully!")
                st.rerun()  # Refresh the app to show the new item
            else:
                st.error("Failed to insert item.")

st.write("---")  # Separator between insert section and items table

# ---------- Item Table Section ----------
if items:
    # Convert items to a pandas DataFrame for tabular processing
    df = pd.DataFrame(items)
    # Remove the 'id' column for display purposes
    df_display = df.drop(columns=['id'])

    # Create columns for table headers using Streamlit's column layout
    table_cols = st.columns([3, 2, 3, 2, 2])
    table_cols[0].write("Name")
    table_cols[1].write("Price")
    table_cols[2].write("Description")   

    # Display each item as a row in the table
    for i in range(len(items)):
        row = st.columns([3, 2, 3, 2, 2])
        row[0].write(items[i]['name'])         # Show item name
        row[1].write(items[i]['price'])        # Show item price
        row[2].write(items[i]['description'])  # Show item description

        # "Edit" button for each row; sets the edit_item_id in session state
        if row[3].button("Edit", key=f"edit_{i}"):
            st.session_state.edit_item_id = items[i]['id']

        # "Delete" button for each row; deletes the item from backend
        if row[4].button("Delete", key=f"delete_{i}"):
            res = delete_item(items[i]['id'])
            if res.status_code == 200:
                st.success("Item deleted successfully!")
                # If we were editing this item, reset the editing state
                if st.session_state.edit_item_id == items[i]['id']:
                    st.session_state.edit_item_id = None
                st.rerun()  # Refresh the app to show updated data

        # If the current row is being edited, show an edit form
        if st.session_state.edit_item_id == items[i]['id']:
            with st.form(f"edit_form_{i}"):
                # Pre-fill form inputs with current item data
                name = st.text_input("Name", value=items[i]['name'])
                price = st.number_input("Price", value=items[i]['price'])
                description = st.text_area("Description", value=items[i]['description'])
                submitted = st.form_submit_button("Update Item")
                if submitted:
                    # Send updated data to backend when form is submitted
                    res = update_item(items[i]['id'], name, price, description)
                    if res.status_code == 200:
                        st.success("Item updated successfully!")
                        st.session_state.edit_item_id = None  # Reset editing state
                        st.rerun()  # Refresh the app to show updated data
                    else:
                        st.error("Failed to update item.")
else:
    # If no items exist, show an info message
    st.info("No items found.")

# Add a horizontal separator
st.write("---")
