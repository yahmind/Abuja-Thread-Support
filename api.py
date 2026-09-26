from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

app = FastAPI(title= "Abua Threads Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

print("API Client Ready")


class Agent:
    def _init_(self, name, role, instructions):
        self.name = name
        self.role = role
        self.instructions = instructions

    def run(self, task):
        print(" " + self.name + " is working...")
        response = client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[
                {"role": "system", "content": "You are " + self.name + ", " + self.role + ".\n" + self.instructions},
                {"role": "user", "content": task}
            ],
            temperature=0.3,
            max_tokens=500
        )
        result = response.choices[0].message.content
        print(" " + self.name + " completed")
        return result


# Specialized agent
sales_agent = Agent(
    "sales Agent",
    "A friendly sales respresentative for Abuja-based fashion store called Abua Threads",
    "Answer questions about products, prices and availability. Be warm and helpful. Use Nigerian English phrases when appropriate. Encourage the customer to make a purchase."
)

support_agent = Agent(
    "Support Agent",
    "A customer support specialist for a Nigerian e-commerce business",
    "Handle complaints about late deliveries/orders, wrong items or poor service. Be empathetic and solution-oriented. Never make promises you cannot keep."
)

order_agent = Agent(
    "Order Agent",
    "An order status specialist",
    "Provide information about order tracking, delivery timelines and shipping. Be precise and reassuring."
)

router_agent = Agent(
    "Router",
    "A customer service dispatcher",
    "Classify the customer's message into one of the three categories: SALES, SUPPORT or ORDER. Reply with ONLY the category name"
)


# API models
class CustomerMessage(BaseModel):
    message: str


# Endpoint
@app.post("/support")
async def handle_customer_message(request: Request):
    try:
        body = await request.body()
        content_type = request.headers.get("content-type", "").lower()
        raw_message = ""

        if body:
            if "application/json" in content_type:
                try:
                    payload = await request.json()
                except ValueError:
                    payload = None

                if isinstance(payload, dict):
                    raw_message = (
                        payload.get("message")
                        or payload.get("text")
                        or payload.get("query")
                        or payload.get("prompt")
                        or ""
                    )
                elif isinstance(payload, str):
                    raw_message = payload
                elif payload is not None:
                    raw_message = str(payload)
            else:
                raw_message = body.decode("utf-8", errors="ignore")

        if not raw_message or not str(raw_message).strip():
            return {
                "success": False,
                "Category": "UNKNOWN",
                "reply": "Please send a message so I can help you."
            }

        message = str(raw_message).strip()

        # Classify
        category = router_agent.run("Classify this message: " + message).strip().upper()

        # Route to specialist
        if "SALES" in category:
            response = sales_agent.run(message)
        elif "SUPPORT" in category:
            response = support_agent.run(message)
        elif "ORDER" in category:
            response = order_agent.run(message)
        else:
            response = "I'm sorry, I didn't understand that. Could you please rephrase your question?"

        return {
            "success": True,
            "Category": category,
            "reply": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"status": "Abuja Threads Support API is running"}
