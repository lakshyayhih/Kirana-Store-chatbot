from fastapi import FastAPI
from pydantic import BaseModel
import logging
import db_helperr
import generic_helper

# Initialize the app
app = FastAPI()
ongoing_dish={}
# Enable logging
logging.basicConfig(level=logging.INFO)

# Define a Pydantic model for the webhook request payload
class QueryResult(BaseModel):
    intent: dict
    parameters: dict
    outputContexts: list

class WebhookRequest(BaseModel):
    queryResult: QueryResult

# Define the response model
class FulfillmentResponse(BaseModel):
    fulfillmentText: str

def track_order(parameters:dict,session_id:str):
    order_id = parameters.get("order_id")
    if not order_id:
        return FulfillmentResponse(
            fulfillmentText="Order ID is missing. Please provide a valid Order ID."
        )
    return db_helperr.check_order_status(order_id)
def add_order(parameters:dict,session_id:str):
    dish_name= parameters.get("dish_name")
    quantity=parameters.get("quantity")

    if not dish_name or not quantity:
        return FulfillmentResponse(
            fulfillmentText="Dish name or quantity is missing. Please provide both."
        )
    if len (dish_name) != len(quantity):
        return FulfillmentResponse(
            fulfillmentText="please provide all variable"
        )
    else :
        new_food_dict = dict(zip(dish_name, quantity))

        if session_id in ongoing_dish:
            current_food_dict=ongoing_dish[session_id]
            current_food_dict.update(new_food_dict)
            ongoing_dish[session_id]=current_food_dict
        else:
            ongoing_dish[session_id] = new_food_dict
    order_str= generic_helper.get_str_from_food_dict(ongoing_dish[session_id])

    return FulfillmentResponse(
        fulfillmentText = f"so far you have :{order_str}. you want anything else?"
    )

def final_order(parameters:dict,session_id:str):
    if session_id not in ongoing_dish:
        return FulfillmentResponse(
            fulfillmentText="No ongoing orders to finalize. Please add some items first."
        )

        # Extract dish names and quantities
    dishes_summary = extract_dishes_and_quantities(session_id)
    customer_id,order_id=db_helperr.extract_order_id()

    order_status="completed"

    ingredient_details,total_cost= db_helperr.get_ingredients(dishes_summary)

    response_text = (
        "following groceries is in your orderlist:\n"
        f"{ingredient_details}\n\n"
        f"Total cost: {total_cost:.2f}"
        f"your order id is:{order_id}"
        f"your customer id is:{customer_id}"
    )
    db_helperr.add_order(order_id, customer_id, total_cost, order_status, ingredient_details)
    del ongoing_dish[session_id]
    return FulfillmentResponse(fulfillmentText=response_text)

def extract_dishes_and_quantities(session_id: str):
    if session_id not in ongoing_dish:
        return {}

    current_food_dict = ongoing_dish[session_id]
    if not current_food_dict:
        return {}

    # Return the dictionary directly
    return current_food_dict


# POST endpoint to handle requests
@app.post("/", response_model=FulfillmentResponse)
async def handle_request(request: WebhookRequest):
    intent_name = request.queryResult.intent["displayName"]
    parameters = request.queryResult.parameters
    session_string=None

    for context in request.queryResult.outputContexts:
        if "name" in context:
            session_string = context["name"]
            break

    if not session_string:
        return FulfillmentResponse(
            fulfillmentText="Session information is missing. Please try again."
        )



    session_id= generic_helper.extract_session_id(session_string)
    # Log incoming request data
    logging.info(f"Intent: {intent_name}, Parameters: {parameters}")
    # Handle different intents
    intent_handle={
        "ongoing.tracking": track_order,
        "ongoing.order"   : add_order,
        "final.order"     : final_order
    }
    if intent_name in intent_handle:
        return intent_handle[intent_name](parameters, session_id)
    return FulfillmentResponse(
        fulfillmentText="Sorry, I couldn't process your request. Please try again."
    )



# Run the app (optional for local testing)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
