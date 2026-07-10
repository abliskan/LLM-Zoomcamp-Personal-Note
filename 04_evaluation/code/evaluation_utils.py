import time
import os
from google import genai
from google.genai import types
from tqdm.auto import tqdm
from rag_helper import RAGBase
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def llm_structured(client, instructions, user_prompt, output_type, model="gemini-2.5-flash"):
    messages = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt),
                   types.Part.from_text(text=instructions)]
        )
    ]

    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=2000,
        response_mime_type="application/json", # Forces Gemini to output strict JSON
        response_schema=output_type            # Enforce your structural blueprint
    )
    
    response = client.models.generate_content(
        model=model,
        contents=messages,
        config=config
    )

    return response.parsed, response.usage_metadata


def llm_structured_retry(
    client,
    instructions,
    user_prompt,
    output_type,
    model="gemini-2.5-flash",
    max_retries=3,
):
    for attempt in range(max_retries):
        try:
            return llm_structured(
                client,
                instructions,
                user_prompt,
                output_type,
                model=model,
            )
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


class RAGWithUsage(RAGBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usages = []
        self.last_usage = None

    def reset_usage(self):
        self.usages = []
        self.last_usage = None

    def search(self, query, num_results=5):
        boost_dict = {"question": 1.0, "answer": 2.0, "section": 0.1}
        filter_dict = {"course": self.course}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict
        )

    def llm(self, prompt):
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

        return response.text

    def total_cost(self):
        return calc_total_price(self.usages)


def map_progress(pool, seq, f):
    results = []

    with tqdm(total=len(seq)) as progress:
        futures = []

        for el in seq:
            future = pool.submit(f, el)
            future.add_done_callback(lambda p: progress.update())
            futures.append(future)

        for future in futures:
            result = future.result()
            results.append(result)

    return results
