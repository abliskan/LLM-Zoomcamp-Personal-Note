import sys
import os

from dotenv import load_dotenv
from ingest import load_faq_data, build_index
# from rag_helper import RAGBase
from metrics import RAGWithMetrics
from db_save import save_conversation
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def create_assistant():
    load_dotenv()

    documents = load_faq_data()
    index = build_index(documents)

    return RAGWithMetrics(
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
    
    save_conversation(assistant.last_call, query, "llm-zoomcamp")