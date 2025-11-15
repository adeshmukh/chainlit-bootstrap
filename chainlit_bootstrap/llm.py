"""LLM and embeddings configuration."""

import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Currently only OpenAI is supported
DEFAULT_GAI_MODEL = os.getenv("DEFAULT_GAI_MODEL", "gpt-4o-mini")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

llm = ChatOpenAI(
    model_name=DEFAULT_GAI_MODEL,
    temperature=0,
    streaming=True,
    openai_api_key=OPENAI_API_KEY,
)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
