import chromadb
import os
from typing import Dict, List
import logging
import asyncio
from logging.handlers import RotatingFileHandler
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
)
from datasets import Dataset
from ragas import evaluate
from backend_service.embedding_func import CustomEmbeddingFunction
from backend_service.prompt import prompt_template
from backend_service.schema import ModelEvalResponse, ModelEvalRequest, ModelResponse, ModelEvaluation


def get_chromadb_client():
    """
    Initializes and returns a ChromaDB client using the relative path to the 'chromadb_data' directory.
    """
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the folder one level up
    relative_path = os.path.join(current_dir, '..', '..', 'chromadb_data')
    return chromadb.PersistentClient(path=relative_path)


def get_chromadb_collection(collection_name: str):
    """
    Retrieves a specific collection from ChromaDB using a custom embedding function.
    :param collection_name: The name of the collection to retrieve.
    :return: The requested ChromaDB collection.
    """
    client = get_chromadb_client()
    custom_embedding_function = CustomEmbeddingFunction()
    collection = client.get_collection(name=collection_name, embedding_function=custom_embedding_function)
    return collection
    


def perform_semantic_search(query: str, collection: Dict[str,chromadb.PersistentClient]):
    """
    Performs a semantic search on a given ChromaDB collection.
    :param query: The search query string.
    :param collection: A dictionary containing the ChromaDB collection to search in.
    :return: A list of search results.
    """
    search_results = collection['chromadb_collection'].query(
        query_texts=[query],
        n_results=5,
    )
    return [result for result in search_results['documents']]



def setup_logger(name, level=logging.INFO, log_file='backend_service.log'):
    """
    Sets up and returns a logger with specified name, level, and log file.
    :param name: The name of the logger.
    :param level: The logging level.
    :param log_file: The file to log messages to.
    :return: Configured logger instance.
    """
    # Creating logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Create handlers
    stream_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)  # 10MB per file, max 5 files
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(message)s')
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # Add handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger

def get_port(default=9007):
    """"
    Sets up and returns a logger with specified name, level, and log file.
    :param name: The name of the logger.
    :param level: The logging level.
    :param log_file: The file to log messages to.
    :return: Configured logger instance.
    """
    try:
        return int(os.environ.get('PORT', default))
    except ValueError:
        return default
    
    
def generate_prompt(question, summaries):
    """
    Generates a prompt for model querying based on a question and a list of summaries.
    :param question: The user's question.
    :param summaries: A list of summaries to include in the prompt.
    :return: A string containing the generated prompt.
    """
    prompt = prompt_template.format(question=question, summaries='\n'.join(summaries[0]))
    return prompt
    
      
async def query_models_async(user_query:str, generative_models) -> List[ModelResponse]:
    """
    Asynchronously queries multiple generative models with a user query.
    :param user_query: The query from the user.
    :param generative_models: A dictionary of generative models to query.
    :return: A list of ModelResponse objects containing the models' responses.
    """
    data= [{"role": "system", "content": user_query}]
    model_names = ['gpt-3.5-turbo response', 'gpt-4-turbo response', 
                   'llama-2-7b-insruct', 'falcon-7b-instruct'
                   ]
    tasks = [generative_models['gpt-3.5-turbo'].generate(data),
    generative_models['gpt-4-turbo'].generate(data),
    generative_models['llama-2-7b-instruct'].generate(user_query),
    generative_models['falcon-7b-instruct'].generate(user_query)
    ]
    responses = await asyncio.gather(*tasks)
    model_responses = [ModelResponse(model_name=model_name,response=response['text']) for model_name, response in zip(model_names, responses)]
    return model_responses


def evaluate_responses(generative_models: Dict, request: ModelEvalRequest) -> ModelEvalResponse:
    """
    Evaluates the responses from different models based on faithfulness and relevancy metrics.
    Determines the best model based on the combined score of faithfulness and relevancy.

    :param generative_models: A dictionary containing the generative models used for evaluation.
    :param request: The ModelEvalRequest object containing the query, model responses, and contexts.
    :return: A ModelEvalResponse object containing the evaluations and the name of the best model.
    """
    model_evaluations = []
    best_model = None
    highest_score = -1
    # Prepare evaluation dataset
    eval_samples = {
        'question': [request.query] * len(request.model_responses),
        'answer': [response.response for response in request.model_responses],
        'contexts': [request.contexts] * len(request.model_responses),
    }
    eval_dataset = Dataset.from_dict(eval_samples)
    # Perform evaluation
    result = evaluate(
        eval_dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=generative_models['gpt-4-eval'],
    )
    df = result.to_pandas()
    # Process evaluation results
    for index, (model_response, row) in enumerate(zip(request.model_responses, df.itertuples(index=False))):
        model_faithfulness = row.faithfulness
        model_answer_relevancy = row.answer_relevancy
        total_score = model_faithfulness + model_answer_relevancy
        model_evaluations.append(ModelEvaluation(
            model_name=model_response.model_name,
            faithfulness=model_faithfulness,
            relevance=model_answer_relevancy
        ))
        if total_score > highest_score:
            highest_score = total_score
            best_model = model_response.model_name
    return ModelEvalResponse(model_evaluations=model_evaluations, best_model=best_model)


# def evaluate_responses(generative_models:Dict, request: ModelEvalRequest):
#     """
#     Evaluates the responses from different models based on faithfulness and relevancy metrics.
#     :param generative_models: A dictionary containing the generative models used for evaluation.
#     :param request: The ModelEvalRequest object containing the query, model responses, and contexts.
#     :return: A ModelEvalResponse object containing the evaluations and the name of the best model.
#     """
#     model_evaluations = []
#     max_score = 0
#     best_model_index = 0
#     eval_samples = {
#     'question': [request.query for _ in range(len(request.model_responses))],
#     'answer': [model_response.response for model_response in request.model_responses],
#     'contexts' :[request.contexts for _ in range(len(request.model_responses))],
#     }
#     eval_dataset = Dataset.from_dict(eval_samples)
#     result = evaluate(
#     eval_dataset,
#     metrics=[
#         faithfulness,
#         answer_relevancy,
#     ],
#     llm=generative_models['gpt-4-eval'],
#     )
#     df = result.to_pandas()
#     for index, row in df.iterrows():
#         model_faithfulness = row['faithfulness']
#         model_answer_relevancy = row['answer_relevancy']
#         total_score = model_faithfulness + model_answer_relevancy
#         if total_score > max_score:
#             max_score = total_score
#             best_model_index = index
#         model_evaluations.append(ModelEvaluation(model_name=request.model_responses[index].model_name,faithfulness=model_faithfulness,relevance=model_answer_relevancy))
#     return ModelEvalResponse(model_evaluations=model_evaluations,best_model=request.model_responses[best_model_index].model_name)