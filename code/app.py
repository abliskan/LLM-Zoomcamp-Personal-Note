from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()

# Load the Gemini API key
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=userdata.get('gemini_api'))

# Initialize the Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3