from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings  

load_dotenv()

def get_llm_model():
    """Lazily initialize the LLM model."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",                     
        temperature=0,                                
    )

def get_embed_model():
    """Lazily initialize the embedding model."""
    return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")