"""Application routing endpoints will be managed here"""
from fastapi import FastAPI
import os
from contextlib import asynccontextmanager
from backend_service.api import router, CHROMADB_COLLECTION, GENERATIVE_MODELS, REPLICATE_API_TOKEN
from backend_service.helper_functions import get_chromadb_collection
from backend_service.generation_models import OpenAIStream, OpenAIReg, Replicate, ReplicateReg
from langchain.chat_models import ChatOpenAI


COLLECTION_NAME = 'info-services-index'
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI application, initializing and clearing resources.

    This context manager is used to set up and tear down resources required by the FastAPI application.
    It initializes various generative models and a ChromaDB collection at the start, and clears them at the end.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: This function yields control back to the caller after setting up the resources.
    """
    CHROMADB_COLLECTION['chromadb_collection'] = get_chromadb_collection(COLLECTION_NAME)
    GENERATIVE_MODELS['gpt-3.5-turbo-stream'] = OpenAIStream(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
    GENERATIVE_MODELS['gpt-4-turbo-stream'] = OpenAIStream(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
    GENERATIVE_MODELS['llama-2-70b-chat-stream'] = Replicate(model="meta/llama-2-70b-chat", api_token=REPLICATE_API_TOKEN)
    GENERATIVE_MODELS['falcon-40b-instruct-stream'] = Replicate(model="meta/meta-llama-3-70b-instruct", api_token=REPLICATE_API_TOKEN)
    GENERATIVE_MODELS['gpt-3.5-turbo'] = OpenAIReg(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
    GENERATIVE_MODELS['gpt-4-turbo'] = OpenAIReg(api_key=OPENAI_API_KEY, model="gpt-4-turbo")  # 
    GENERATIVE_MODELS['falcon-40b-instruct'] = ReplicateReg(model="meta/meta-llama-3-70b-instruct", api_token=REPLICATE_API_TOKEN)
    GENERATIVE_MODELS['llama-2-70b-chat'] = ReplicateReg(model="meta/llama-2-70b-chat", api_token=REPLICATE_API_TOKEN)
    GENERATIVE_MODELS['gpt-3.5-turbo-eval'] = ChatOpenAI(model_name="gpt-4-turbo")
    yield
    CHROMADB_COLLECTION.clear()
    GENERATIVE_MODELS.clear()
    
    
app = FastAPI(lifespan=lifespan)
app.include_router(router)