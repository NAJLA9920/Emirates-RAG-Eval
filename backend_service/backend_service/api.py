from fastapi import APIRouter, WebSocket
import os
import logging
from typing import List
from backend_service.helper_functions import perform_semantic_search, query_models_async, generate_prompt, evaluate_responses
from backend_service.schema import QueryRequest, ModelEvalRequest, ModelEvalResponse, QueryResponse

CHROMADB_COLLECTION = {}
GENERATIVE_MODELS = {}


REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"] 


PREFIX = "/api"
router = APIRouter(prefix=PREFIX)
logger = logging.getLogger("backend_service_logger")


@router.get("/")
async def app_root():
    """
    Root endpoint of the backend service.

    Returns:
        dict: A greeting message indicating the backend service is running.
    """
    return {"Hello": "Backend Service"}


@router.websocket("/ws/model-output")
async def query_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to stream model outputs based on user queries.

    This endpoint accepts a WebSocket connection, receives a user query, and streams the output
    from multiple generative models back to the client.

    Args:
        websocket (WebSocket): The WebSocket connection instance.

    Raises:
        Exception: If an error occurs during the WebSocket communication.
    """
    await websocket.accept()  # Accept the WebSocket connection
    try:
        user_query = await websocket.receive_text()  # Receive the entire user input at once
        data = [{"role": "system", "content": user_query}]  # Format the user query for the models
        # Stream output from the 'gpt-3.5-turbo-stream' model
        model_output_stream = GENERATIVE_MODELS['gpt-3.5-turbo-stream'].generate(data)
        for chunk in model_output_stream:
            if chunk.choices[0].delta.content is not None:
                await websocket.send_json({'gpt-3.5-turbo': chunk.choices[0].delta.content})
        # Stream output from the 'gpt-4-turbo-stream' model
        model_output_stream = GENERATIVE_MODELS['gpt-4-turbo-stream'].generate(data)
        for chunk in model_output_stream:
            if chunk.choices[0].delta.content is not None:
                await websocket.send_json({'gpt-4-turbo': chunk.choices[0].delta.content})
        # Stream output from the 'llama-2-70b-chat-stream' model
        for text_chunk in GENERATIVE_MODELS['llama-2-70b-chat-stream'].generate(user_query):
            await websocket.send_json({'llama-2-70b-chat': text_chunk})
        # Stream output from the 'falcon-40b-instruct-stream' model
        for text_chunk in GENERATIVE_MODELS['falcon-40b-instruct-stream'].generate(user_query):
            await websocket.send_json({'falcon-40b-instruct': text_chunk})
    except Exception as e:
        print(f"Error: {e}")  # Log any errors that occur
    finally:
        await websocket.close()  # Close the connection after streaming all words

    
@router.post("/query")
async def query_models(request: QueryRequest) -> QueryResponse:
    """
    Endpoint to query multiple generative models and retrieve their responses.

    This endpoint performs a semantic search based on the user's query, generates a prompt,
    and queries multiple generative models asynchronously.

    Args:
        request (QueryRequest): The request object containing the user's query.

    Returns:
        QueryResponse: The response object containing model responses and retrieved contexts.
    """
    retrieved_summaries = perform_semantic_search(query=request.query, collection=CHROMADB_COLLECTION)
    prompt = generate_prompt(question=request.query, summaries=retrieved_summaries)
    model_responses = await query_models_async(user_query=prompt, generative_models=GENERATIVE_MODELS)
    return QueryResponse(model_responses=model_responses, contexts=retrieved_summaries[0])


@router.post("/evaluate")
async def evaluate_model_responses(request: ModelEvalRequest) -> ModelEvalResponse:
    """
    Endpoint to evaluate responses from multiple generative models.

    This endpoint evaluates the responses from multiple generative models based on the provided request.

    Args:
        request (ModelEvalRequest): The request object containing the model responses to be evaluated.

    Returns:
        ModelEvalResponse: The response object containing the evaluation results.
    """
    evaluated_responses = evaluate_responses(GENERATIVE_MODELS,request)
    return evaluated_responses



# @router.websocket("/ws/model-output")
# async def query_websocket_endpoint(websocket: WebSocket):
#     """
#     WebSocket endpoint to stream model outputs based on user queries.

#     This endpoint accepts a WebSocket connection, receives a user query, and streams the output
#     from multiple generative models back to the client.

#     Args:
#         websocket (WebSocket): The WebSocket connection instance.

#     Raises:
#         Exception: If an error occurs during the WebSocket communication.
#     """
#     await websocket.accept()
#     try:
#         user_query = await websocket.receive_text()  # Receive the entire user input at once
#         data= [{"role": "system", "content": user_query}]
#         model_output_stream = GENERATIVE_MODELS['gpt-3.5-turbo-stream'].generate(data)
#         for chunk in model_output_stream:
#             if chunk.choices[0].delta.content is not None:
#                 await websocket.send_json({'gpt-3.5-turbo':chunk.choices[0].delta.content})
                
#         model_output_stream = GENERATIVE_MODELS['gpt-4-turbo-stream'].generate(data)
#         for chunk in model_output_stream:
#             if chunk.choices[0].delta.content is not None:
#                 await websocket.send_json({'gpt-4-turbo':chunk.choices[0].delta.content})

#         for text_chunk in GENERATIVE_MODELS['llama-2-70b-chat-stream'].generate(user_query):
#             await websocket.send_json({'llama-2-70b-chat':text_chunk})
        
#         for text_chunk in GENERATIVE_MODELS['falcon-40b-instruct-stream'].generate(user_query):
#             await websocket.send_json({'falcon-40b-instruct':text_chunk})
            
#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         await websocket.close()  # Close the connection after streaming all words