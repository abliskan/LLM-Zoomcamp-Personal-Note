import os
import requests
from dotenv import load_dotenv
# from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from google import genai
from google.genai import types
from minsearch import Index
load_dotenv()

# Access your environment variables
# my_var = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the Gemini API key
# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=userdata.get('gemini_api'))

# Initialize the Gemini model
# llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

# response = client.models.generate_content(
#     model="gemini-3.5-flash",
#     contents="I just discovered the course. Can I join now?"
# )
# response = llm.invoke("I just discovered the course. Can I join now?")
# print(response.text)

def llm_call(prompt: str) -> str:
    client = genai.Client()
    
    # Structure system instructions to ground the model strictly in the provided context
    system_instruction = (
        "You are a helpful assistant. Answer the user's question using ONLY the provided context. "
        "If the context does not contain the answer, politely state that you do not know. "
        "Do not use external knowledge or hallucinate."
    )
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0, # Low temperature ensures strict adherence to text and reduces hallucinations
        )
    )
    return response.text

question = 'I just discovered the course. Can I join now?'

context = '''
I just discovered the course. Can I still join?
Yes, but if you want to receive a certificate, you need to submit your project while we’re still accepting submissions.

edit on GitHub
#Course: I have registered for the LLM Zoomcamp. When can I expect to receive the confirmation email?
You don't need it. You're accepted. You can also just start learning and submitting homework (while the form is open) without registering. It is not checked against any registered list. Registration is just to gauge interest before the start date.

edit on GitHub
#What is the video/zoom link to the stream for the “Office Hours” or live/workshop sessions?
The zoom link is only published to instructors/presenters/TAs.

Students participate via YouTube Live and submit questions to Slido (link is pinned in the chat when live). The video URL should be posted in the announcements channel on Telegram &amp; Slack before it begins. You can also watch live on the DataTalksClub YouTube Channel.

Don’t post questions in chat as they may be missed if the room is very active.

edit on GitHub
#Cloud alternatives with GPU
Check the quota and reset cycle carefully. Is the free hours limit per month or per week? Usually, if you change the configuration, the free hours quota might also be adjusted, or it might be billed separately.

Potential options include:

Google Colab
Kaggle
Databricks (possibly)
Consider using Gemini to discover more options. Be aware that some platforms might have restrictions on what you can and cannot install, so ensure to read what is included in the free vs paid tier.
'''

prompt = f'''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."

Question:
{question}

Context:
{context}
'''

# answer = llm_call(prompt)
# print("Answer:", answer)


docs_url = 'https://datatalks.club/faq/json/courses.json'
response = requests.get(docs_url)
courses_raw = response.json()

# print(courses_raw)

documents = []
url_prefix = 'https://datatalks.club/faq'

for course in courses_raw:
    course_url = f'{url_prefix}{course['path']}'

    course_response = requests.get(course_url)
    course_response.raise_for_status()
    course_data = course_response.json()

    documents.extend(course_data)

# len(documents)
# print("Length of documents", len(documents))
# print("Show inside documents", documents[1100])

index = Index(
    text_fields = ['question', 'section', 'answer'],
    keyword_fields = ['course']
)

index.fit(documents)

# search_results = index.search(question, 
#              filter_dict={'course': 'llm-zoomcamp'},
#              num_results=5
# )

def search (question: str, course: str='llm-zoomcamp'):
    boost_dict = {'question': 2.0, 'section': 0.5}
    filter_dict = {'course': course}
    
    return index.search(
        question, 
        boost_dict=boost_dict,
        filter_dict=filter_dict,
        num_results=5
    )
    
search_results = search(question)

# print("Search results:", search_results)

INSTRUCTIONS = '''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
'''

USER_PROMPT_TEMPALATE = '''
Question:
{question}

Context:
{context}
'''

def build_context(search_results: list[dict]) -> str:
    lines = []
    
    for doc in search_results:
        lines.append(doc['question'])
        lines.append('Q: ' + doc['question'])
        lines.append('A: ' + doc['answer'])
        lines.append('')
    
    return '\n'.join(lines).strip()

# context = build_prompt(search_results)
# print(context)

def build_prompt(question: str, search_results:list[dict]) -> str:
    context = build_context(search_results)
    prompt = USER_PROMPT_TEMPALATE.format(
        question=question, 
        context=context
    )
    return prompt.strip()
    
prompt = build_prompt(question, search_results)
# print("Prompt: ", prompt)

# Generate a response from the model
response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt
)

# Extract token usage from metadata
usage = response.usage_metadata
prompt_tokens = usage.prompt_token_count
candidate_tokens = usage.candidates_token_count

# Print individual metrics
# print(f"Prompt (Input) Tokens: {prompt_tokens}")
# print(f"Candidates (Output) Tokens: {candidate_tokens}")
# print(f"Total Tokens Used: {usage.total_token_count}")

# Define pricing (per million tokens)
input_price = 0.75 / 1_000_000
output_price = 4.50 / 1_000_000

# Calculate total cost
cost = (prompt_tokens * input_price) + (candidate_tokens * output_price)

# Display results
# print(f"Current API Cost: ${cost:.6f}")

message_history = [
    {'role': 'developer', 'content': INSTRUCTIONS},
    {'role': 'user', 'content': prompt}
]

def llm_check(instructions, user_prompt, model='gemini-3.5-flash'):
    message_history = [
        {'role': 'developer', 'content': instructions},
        {'role': 'user', 'content': user_prompt}
    ]

    response = client.models.generate_content(
        model=model,
        contents=message_history
    )
    return response.text

def rag(query, model='gemini-3.5-flash'):
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer = llm_check(INSTRUCTIONS, prompt, model=model)
    return answer

answer = rag(question)
print(answer)