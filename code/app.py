import os
import requests
from dotenv import load_dotenv
# from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from google import genai
from google.genai import types
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

# docs_url = 'https://datatalks.club/faq/json/courses.json'
# response = requests.get(docs_url)
# courses_raw = response.json()

# # print(courses_raw)

# documents = []
# url_prefix = 'https://datatalks.club/faq'

# for course in courses_raw:
#     course_url = f'{url_prefix}{course['path']}'

#     course_response = requests.get(course_url)
#     course_response.raise_for_status()
#     course_data = course_response.json()

#     documents.extend(course_data)

# print("Length of documents", len(documents))
# print("Show inside documents", documents[1100])

def llm_call(prompt: str) -> str:
    client = genai.Client()
    
    # Structure system instructions to ground the model strictly in the provided context
    system_instruction = (
        "You are a helpful assistant. Answer the user's question using ONLY the provided context. "
        "If the context does not contain the answer, politely state that you do not know. "
        "Do not use external knowledge or hallucinate."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
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

answer = llm_call(prompt)
print("Answer:", answer)