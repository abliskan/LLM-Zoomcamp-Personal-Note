import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

INSTRUCTIONS = '''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
'''

PROMPT_TEMPLATE = '''
QUESTION: {question}

CONTEXT:
{context}
'''.strip()


class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        model='gemini-3.5-flash'
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.model = model

    def search(self, query, num_results=5):
        return self.index.search(query, num_results=num_results)

    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append(doc['filename'])
            lines.append(doc['content'])
            lines.append('')

        return '\n'.join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
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
        ),
        types.Content(
            role="developer",
            parts=[types.Part.from_text(text=self.instructions)]
        )
        ]
        
        response = client.models.generate_content(
            model=self.model,
            contents=input_messages,
            config=config
        )

        return response

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer