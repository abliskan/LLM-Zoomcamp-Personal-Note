import os
from gitsource import GithubRepositoryDataReader
from dotenv import load_dotenv
from google import genai
from google.genai import types
from minsearch import Index
from rag_helper import RAGBase
from gitsource import chunk_documents
from toyaikit.tools import Tools
from toyaikit.llm import GeminiClient
from toyaikit.chat import IPythonChatInterface
from toyaikit.chat.runners import GeminiResponsesRunner, DisplayingRunnerCallback
load_dotenv()

MODEL_NAME = "gemini-3.5-flash"

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

files = reader.read()

documents = []

for file in files:
    doc = file.parse()
    documents.append(doc)
    
# print(documents)

len(documents)

def build_index(documents):
    index = Index(
        text_fields=["content"],
        keyword_fields=["filename"]
    )
    index.fit(documents)
    return index

index = build_index(documents)

# print(index)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

question = "How does the agentic loop keep calling the model until it stops?"

search_results = index.search(
    question,
    # boost_dict={"question": 2.0, "section": 0.5},
    # filter_dict={"course": "llm-zoomcamp"},
    # num_results=5
)

# print(search_results)

assistant = RAGBase(
    index=index,
    llm_client=client,
    model=MODEL_NAME
)

answer = assistant.rag('How does the agentic loop keep calling the model until it stops?')

# print(answer.output_text)

# print(answer.usage)

chunks = chunk_documents(documents, size=2000, step=1000)

# len(chunks)

chunked_index = build_index(chunks)
chunked_index.fit(chunks)
chunked_search_results = chunked_index.search(
    question
)

# print(chunked_search_results)0

chunked_assistant = RAGBase(
    index=chunked_index,
    llm_client=client,
    model=MODEL_NAME
)

chunked_answer = chunked_assistant.rag('How does the agentic loop keep calling the model until it stops?')

# chunked_answer.usage

# chunked_answer.output_text

search_call_count = 0

def search_chunk_index(query: str) -> list[dict]:
    """
    Search the chunked course lesson dataset for information relevant to the user query.

    Args:
        query: The search keywords or natural language question to look up.

    Returns:
        A list of matching document chunks, each containing 'content' and 'filename'.
    """
    global search_call_count
    search_call_count += 1
    print(f"[Tool Call #{search_call_count}] Searching for: '{query}'")

    # Assuming `index` is your global minsearch.Index instance from Question 5
    results = index.search(
        query=query,
        filter_dict={},
        boost_dict={'content': 1.0},
        num_results=5
    )
    return results

tools_obj = Tools()
tools_obj.add_tool(search_chunk_index)

runner = client.chats.create(
    model=MODEL_NAME,
    config=types.GenerateContentConfig(
        tools=tools_obj,
        temperature=0.7,
    )
)

agent_instructions = (
    "You're a course teaching assistant. Answer the student's question using the search tool. "
    "Make multiple searches with different keywords before answering."
)
student_question = "How does the agentic loop work, and how is it different from plain RAG?"

# print("Starting agentic loop...")

prompt = f"System: {agent_instructions}\n\nStudent Question: {student_question}"

chat_interface = IPythonChatInterface()
callback = DisplayingRunnerCallback(chat_interface)
result = runner.loop(
    prompt=prompt,
    callback=callback,
)

num_search_calls = sum(
    1
    for msg in result.all_messages
    if hasattr(msg, "type") and msg.type == "function_call" and msg.name == "search"
)

print("search() called:", num_search_calls, "times")