import os
from pathlib import Path
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader
from minsearch import Index
from rag_helper import RAGBase
from google import genai
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

COMMIT = "8c1834d"

# --- Load the course lessons (same as HW1, HW2, HW4) ---
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]

index = Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)

load_dotenv()
client = client_gemini
rag = RAGBase(index=index, llm_client=client)

if __name__ == "__main__":
    query = "How does the agentic loop keep calling the model until it stops?"
    answer = rag.ragWithTrace(query)
    print(answer)