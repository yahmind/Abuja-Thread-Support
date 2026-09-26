from groq import Groq
import os 
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key= os.environ.get('GROQ_API_KEY'))
print('Api Cliemt Ready')

# Input Guadrails

class InputGuard:  # Helps validate input before sending llm
    PROHIBITED_TOPICS = ['competitor_x', 'hack', 'exploit', 'illegal']
    MAX_LENGTH = 2000
    MIN_LENGTH = 10

    @classmethod
    def validate(cls, user_input):
        if not user_input or len(user_input.strip()) < cls.MIN_LENGTH:
            return {'valid': False, 'reason': 'input too short. Minimum ' + str(cls.MIN_LENGTH) + ' character.'}
        if len(user_input) > cls.MAX_LENGTH:
            return {'valid': False, 'reason': 'Input too long. Maximum ' + str(cls.MAX_LENGTH) + ' characters.'}

        lower = user_input.lower()
        for topic in cls.PROHIBITED_TOPICS:
            if topic in lower:
                return {'valid': False, 'reason': 'Prohibited topic detected: ' + topic}

        return {'valid': True, 'reason': None}


# Test the input Guard
print("testing input Guard")
print("=" * 40)

tests = [
    "hi",  # Too short
    "What is the maximum timeline to reset DSTV E16 error",  # Valid
    "How do i transfer someone else DSTV subscription to another account?",  # Prohibited
    "x" * 3000  # too long
]

for test_input in tests:
    result = InputGuard.validate(test_input)
    status = "PASS" if result['valid'] else "REJECT"
    reason = result['reason'] or "No issue"
    print(" " + status + ": " + test_input[:50] + "...")
    print(" " + reason)
    print()


# Output Guard : Validate LlM output before it gets to user
class OutputGuard:
    PROHIBITED_PHRASES = ['I promise', 'I guarantee', 'definitely', '100%']
    MAX_RESPONSE_LENGTH = 1000

    @classmethod
    def validate(cls, ai_response, expected_format=None):
      

        if not ai_response:
            return {'valid': False, 'reason': 'Empty response.'}

        if len(ai_response) > cls.MAX_RESPONSE_LENGTH:
            return {'valid': False, 'reason': 'Response too long: ' + str(len(ai_response)) + ' characters.'}

        for phrase in cls.PROHIBITED_PHRASES:
            if phrase.lower() in ai_response.lower():
                return {'valid': False, 'reason': 'Prohibited phrase found: "' + phrase + '"'}

        if expected_format == 'json':
            try:
                json.loads(ai_response)
            except json.JSONDecodeError:
                return {'valid': False, 'reason': 'Response is not valid JSON.'}

        return {'valid': True, 'reason': None}

print()
print('Testing output Guard')
print("="*40)

valid_output = "DSTV E16 error taken within 0 to 15 minutes to reset."
invalid_output = " I guarantee you, it will defintely clear and the customer should be able to view! It's 100% sure."

check1 = OutputGuard.validate(valid_output)
print('valid response:', check1['valid'])

check2 = OutputGuard.validate(invalid_output)
print("Response with prohibited phrases:", check2['valid'])
print("Reason:", check2['reason'])


# Cost Tracker
class CostTracker:
    def _init_(self, daily_budget=1.00):
        self.daily_budget = daily_budget
        self.daily_spend = 0.0
        self.total_tokens = 0
        self.calls = 0

    def track(self, usage):
        self.total_tokens += getattr(usage, 'total_tokens', 0)
        self.calls += 1
        self.daily_spend += 0.0
        return 0.0

    def summary(self):
        return {
            'calls': self.calls,
            'tokens': self.total_tokens,
            'budget_status': 'free tier - no cost'
        }

tracker = CostTracker()

print()
print("Cost Tracker Ready")
print("=" * 40)
print("Model: openai/gpt-oss-120b via Groq")
print("Cost: Free tier")
print("Daily budget tracking still important for production")

# Safe AI function
def safe_ai_call(user_input, system_prompt):

    # Layer 1: validate user input
    input_check = InputGuard.validate(user_input)
    if not input_check['valid']:
        return {
            'success': False,
            'error': input_check['reason'],
            'response': None
        }

    # Layer 2: call the model and validate its output
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
            max_tokens=500
        )
        tracker.track(response.usage)
        ai_text = response.choices[0].message.content

        # Layer 3
        output_check = OutputGuard.validate(ai_text)
        if not output_check['valid']:
            return {
                'success': False,
                'error': 'Reason failed validation:' + output_check['reason'],
                'response': None
            }

        return {
            'success': True,
            'response': ai_text,
            'tokens': response.usage.total_tokens,
            'tracker': tracker.summary()
        }

    except Exception as e:
        return {
            'success': False,
            'error': 'API Error: ' + str(e),
            'response': None
        }

# Testing 
print()
print("Testing Safe AI Function")
print("="*40)

#Valid input 
print()
print("Testing valid question")
result = safe_ai_call("What is the maximum timeline for DSTV E16 error to reset?",
                            "You are a helpful customer service agent. Answer Professionally.")
print(json.dumps(result, indent=2, default= str))


#invalid input 
print()
print("Testing Invalid Input")
result = safe_ai_call("hi",
                      "You are a helpful customer service agent.")
print(json.dumps(result, indent=2, default=str))

# Prohibited topics 
print()
print("Testing rohibited Topics")
result = safe_ai_call("How do i hack into someelse account?",
                      "You are a helpful customer service agent.")
print(json.dumps(result, indent=2, default=str))