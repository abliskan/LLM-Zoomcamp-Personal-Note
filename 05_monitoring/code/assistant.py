import sys
import os

from dotenv import load_dotenv
from ingest import load_faq_data, build_index
from rag_helper import RAGBase
from google import genai
from google.genai import types
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def create_assistant():
    load_dotenv()

    documents = load_faq_data()
    index = build_index(documents)

    return RAGBase(
        index=index,
        llm_client=client,
    )
    

if __name__ == "__main__":
    assistant = create_assistant()

    query = "How do I join the course?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = assistant.rag(query)
    print(answer)