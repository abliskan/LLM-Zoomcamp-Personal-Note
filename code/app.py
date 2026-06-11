import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
load_dotenv()

# Access your environment variables
my_var = os.getenv("GOOGLE_API_KEY")

# Load the Gemini API key
# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=userdata.get('gemini_api'))

# Initialize the Gemini model
# llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

# response = llm.invoke("I just discovered the course. Can I join now?")
# print(response)

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

print("Length of documents", len(documents))
print("Show inside documents", documents[1100])