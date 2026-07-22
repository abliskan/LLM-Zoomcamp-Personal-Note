import time
import os
from dataclasses import dataclass, field
from datetime import datetime
from rag_helper import RAGBase
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@dataclass
class LLMCallRecord:
    model: str
    prompt: str
    instructions: str
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)

def calculate_cost(model, usage):
    cost = 0
    if "gemini-3.5-flash" in model:
        cost = (usage.prompt_token_count * 0.15 + usage.candidates_token_count * 0.60) / 1_000_000
    return cost

class RAGWithMetrics(RAGBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_call: LLMCallRecord = None

    def llm(self, prompt):
        start_time = time.time()
        response = self._call_llm(prompt)
        response_time = time.time() - start_time
        self._log_response(prompt, response, response_time)
        return response.text
    
    def _call_llm(self, prompt):
        config = types.GenerateContentConfig(
            system_instruction=self.instructions,
            temperature=0.2 # Optional payload configuration
        )
        
        input_messages = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )]
        
        response = client.models.generate_content(
            model=self.model,
            contents=input_messages,
            config=config
        )
        return response
    
    def _log_response(self, prompt, response, response_time):
        usage = response.usage_metadata
        cost = calculate_cost(self.model, usage)

        call_record = LLMCallRecord(
            model=self.model,
            prompt=prompt,
            instructions=self.instructions,
            answer=response.text,
            prompt_tokens=usage.prompt_token_count,
            completion_tokens=usage.candidates_token_count,
            total_tokens=usage.total_token_count,
            response_time=response_time,
            cost=cost,
        )
    
        print(call_record)
        self.last_call = call_record