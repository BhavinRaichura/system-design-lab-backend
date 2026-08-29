from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings


llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=0.3,
)