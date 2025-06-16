import mysql.connector
from fastapi import  HTTPException
import logging
from pydantic import BaseModel
import random


class FulfillmentResponse(BaseModel):
    fulfillmentText: str
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Replace with your database username
            password="Patel9047@",  # Replace with your database password
            database="recipedb"  # Replace with your database name
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Database connection failed: {err}")
        raise HTTPException(status_code=500, detail="Database connection error")


def extract_order_id():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT MAX(order_id) AS max_order_id FROM orders"
        cursor.execute(query)
        result = cursor.fetchone()

        # Extract the maximum order ID or handle NULL case
        max_order_id = result['max_order_id'] if result and result['max_order_id'] is not None else 0


        query = "SELECT MAX(customer_id) AS max_customer_id FROM customer_details"
        cursor.execute(query)
        result = cursor.fetchone()

        # Get the maximum customer ID or default to 0 if none exists
        max_customer_id = result['max_customer_id'] if result and result['max_customer_id'] is not None else 0

        # Return the next customer ID
        return max_customer_id + 1,max_order_id+1
    finally:
        # Ensure cursor is closed
        cursor.close()

def check_order_status(order_id: str) -> FulfillmentResponse:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT status_update FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()

        if result:
            return FulfillmentResponse(
                fulfillmentText=f"The status of order {order_id} is: {result['status_update']}."
            )
        else:
            return FulfillmentResponse(
                fulfillmentText=f"Order ID {order_id} not found in the database."
            )
    except mysql.connector.Error as err:
        logging.error(f"Error querying the database: {err}")
        raise HTTPException(status_code=500, detail="Error querying the database")
    finally:
        cursor.close()

def check_order_status(order_id: str) -> FulfillmentResponse:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT status_update FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()

        if result:
            return FulfillmentResponse(
                fulfillmentText=f"The status of order {order_id} is: {result['status_update']}."
            )
        else:
            return FulfillmentResponse(
                fulfillmentText=f"Order ID {order_id} not found in the database."
            )
    except mysql.connector.Error as err:
        logging.error(f"Error querying the database: {err}")
        raise HTTPException(status_code=500, detail="Error querying the database")
    finally:
        cursor.close()


from decimal import Decimal
from fastapi.responses import JSONResponse


def get_ingredients(dishes_summary):
    # Initialize total cost and ingredient list
    overall_cost = Decimal(0)
    aggregated_ingredients = {}

    # Get database connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Iterate through the dishes and quantities in the summary
        for dish_name, quantity in dishes_summary.items():
            # Fetch the dish ID for the given dish name
            cursor.execute("SELECT dish_id FROM dishes WHERE dish_name = %s", (dish_name,))
            dish = cursor.fetchone()

            if not dish:
                return FulfillmentResponse(
                    fulfillmentText=f"Dish '{dish_name}' not found in the database."
                )
            dish_id = dish["dish_id"]

            # Fetch ingredient details for the dish
            query = """
                SELECT i.ingredient_name, i.ingredient_id,i.price, i.unit, di.quantity AS quantity_per_person
                FROM dish_ingredients di
                INNER JOIN ingredients i ON di.ingredient_id = i.ingredient_id
                WHERE di.dish_id = %s
            """
            cursor.execute(query, (dish_id,))
            ingredients = cursor.fetchall()

            if not ingredients:
                return FulfillmentResponse(
                    fulfillmentText=f"No ingredients found for dish '{dish_name}'."
                )

            # Calculate total quantities and costs
            quantity = Decimal(quantity)  # Convert quantity to Decimal

            for ingredient in ingredients:
                ingredient_name = ingredient["ingredient_name"]
                price_per_unit = Decimal(ingredient["price"])
                quantity_per_person = Decimal(ingredient["quantity_per_person"])
                unit = ingredient["unit"]
                ig_id=ingredient["ingredient_id"]

                if ingredient_name not in aggregated_ingredients:
                    aggregated_ingredients[ingredient_name] = {
                        "total_quantity": 0,
                        "unit": unit,
                        "price_per_unit": price_per_unit,
                        "total_cost": 0,
                        "ingredient_id":ig_id
                    }

                aggregated_ingredients[ingredient_name]["total_quantity"] += quantity_per_person
                aggregated_ingredients[ingredient_name]["total_cost"] += quantity_per_person * price_per_unit
                cost = quantity_per_person * price_per_unit
                overall_cost += cost

            ingredient_list = [
                f"||{name} --> {data['total_quantity']:.2f} {data['unit']} @ {data['price_per_unit']:.2f} = {data['total_cost']:.2f},{data['ingredient_id']}"
                for name, data in aggregated_ingredients.items()
            ]

        # Create the final response text
        ingredient_details = "\n".join(ingredient_list)
        return ingredient_details,overall_cost

    except Exception as e:
        logging.error(f"Error fetching ingredients: {e}")
        return FulfillmentResponse(
            fulfillmentText="An error occurred while processing your order. Please try again."
        )
    finally:
        # Close the database cursor and connection
        cursor.close()




import datetime


def add_order(order_id, customer_id, total_amount, order_status,ingredient_details:dict):
    connection = get_db_connection()  # Assumes this function is defined elsewhere
    cursor = connection.cursor()
    order_date = datetime.datetime.now()

    try:
        # Verify if customer_id exists
        cursor.execute("SELECT customer_id FROM customer_details WHERE customer_id = %s", (customer_id,))
        customer_exists = cursor.fetchone()

        if not customer_exists:

            import random

            # Lists of options
            mobile_numbers = ["111", "222", "333", "444", "555", "666", "777", "8888"]
            email_ids = ["e@example.com", "r@example.com", "t@example.com", "y@example.com", "u@example.com",
                         "i@example.com", "o@example.com", "p@example.com"]

            # Sets to track used values
            used_mobiles = set()
            used_emails = set()

            # Function to get a unique mobile number
            def get_unique_mobile():
                available_mobiles = set(mobile_numbers) - used_mobiles
                if not available_mobiles:
                    raise ValueError("No unique mobile numbers left!")
                mobile = random.choice(list(available_mobiles))
                used_mobiles.add(mobile)
                return mobile

            # Function to get a unique email
            def get_unique_email():
                available_emails = set(email_ids) - used_emails
                if not available_emails:
                    raise ValueError("No unique email IDs left!")
                email = random.choice(list(available_emails))
                used_emails.add(email)
                return email

            # Example Usage
            try:
                random_mobile = get_unique_mobile()
                random_email = get_unique_email()
                add_customer(customer_id, "suresh", random_email, random_mobile, "abc", order_date)
                print(f"Random Mobile: {random_mobile}")
                print(f"Random Email: {random_email}")
            except ValueError as e:
                print(e)





        # Get the current timestamp


        # Insert the order into the database
        query = """
                INSERT INTO orders (order_id, customer_id, order_date, total_amount, order_status)
                VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(query, (order_id, customer_id, order_date, total_amount, order_status))

        # Commit the transaction
        connection.commit()
        print(f"Order {order_id} successfully added!")
        add_order_details(ingredient_details,order_id)
    except Exception as e:
        connection.rollback()
        print(f"Failed to add order: {e}")
    finally:
        cursor.close()
        connection.close()


def add_customer(customer_id, customer_name, customer_email, customer_phone,adress,created_at):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO customer_details (customer_id, customer_name, customer_email,customer_phone,address,created_at)
            VALUES (%s, %s, %s, %s,%s,%s)
        """
        cursor.execute(query, (customer_id, customer_name, customer_email, customer_phone,adress,created_at))
        connection.commit()
        print(f"Customer {customer_id} successfully added!")
    except Exception as e:
        connection.rollback()
        print(f"Failed to add customer: {e}")
    finally:
        cursor.close()


def add_order_details(ingredient_details: str, order_id: str):
    connection = get_db_connection()  # Assumes this function is defined elsewhere
    cursor = connection.cursor()

    try:
        parsed_ingredients = parse_ingredient_details(ingredient_details)

        for ingredient in parsed_ingredients:
            # Extract values
            ingredient_id = ingredient["ingredient_id"]
            quantity = ingredient["total_quantity"]
            price_per_unit = ingredient["price_per_unit"]
            total_cost = ingredient["total_cost"]

            # Insert into the order details table
            query = """
                INSERT INTO order_details (order_id, ingredient_id, quantity, price_per_unit, total_price)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (order_id, ingredient_id, quantity, price_per_unit, total_cost))

        # Commit the transaction
        connection.commit()
        print(f"Order details for order_id {order_id} successfully added!")
    except Exception as e:
        connection.rollback()
        print(f"Failed to add order details: {e}")
    finally:
        cursor.close()
        connection.close()


import re

def parse_ingredient_details(ingredient_details):
    # Split into individual lines
    lines = ingredient_details.strip().split("\n")
    parsed_ingredients = []

    for line in lines:
        # Parse each line using regex
        match = re.match(
            r"\|\|(.+?) --> ([\d.]+) (.+?) @ ([\d.]+) = ([\d.]+),(\d+)", line
        )
        if match:
            parsed_ingredients.append({
                "name": match.group(1),  # Ingredient name
                "total_quantity": float(match.group(2)),  # Total quantity
                "unit": match.group(3),  # Unit (e.g., kg)
                "price_per_unit": float(match.group(4)),  # Price per unit
                "total_cost": float(match.group(5)),  # Total cost
                "ingredient_id": int(match.group(6))  # Ingredient ID
            })
        else:
            print(f"Could not parse line: {line}")

    return parsed_ingredients
