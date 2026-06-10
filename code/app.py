import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
load_dotenv()

# Access your environment variables
my_var = os.getenv("GOOGLE_API_KEY")

# Load the Gemini API key
# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=userdata.get('gemini_api'))

# Initialize the Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

response = llm.invoke("I just discovered the course. Can I join now?")
print(response)