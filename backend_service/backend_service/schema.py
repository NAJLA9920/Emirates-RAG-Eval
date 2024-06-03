from pydantic import BaseModel
from typing import List


class QueryRequest(BaseModel):
    """
    Represents a request for querying a model with a specific query string.
    
    Attributes:
        query (str): The query string to be sent to the model.
    """
    query: str


class ModelResponse(BaseModel):
    """
    Represents a response from a model to a given query.
    
    Attributes:
        model_name (str): The name of the model that generated the response.
        response (str): The textual response generated by the model.
    """
    model_name: str
    response: str
    
class QueryResponse(BaseModel):
    """
    Represents the aggregated response from multiple models to a given query, including any relevant contexts.
    
    Attributes:
        model_responses (List[ModelResponse]): A list of responses from different models.
        contexts (List[str]): A list of contexts relevant to the query and responses.
    """
    model_responses: List[ModelResponse]
    contexts: List[str]

class ModelEvalRequest(BaseModel):
    """
    Represents a request for evaluating model responses based on a given query and contexts.
    
    Attributes:
        query (str): The original query string that was sent to the models.
        model_responses (List[ModelResponse]): The responses from the models to be evaluated.
        contexts (List[str]): The contexts used for generating the responses.
    """
    query: str
    model_responses: List[ModelResponse]
    contexts: List[str]
    
class ModelEvaluation(BaseModel):
    """
    Represents the evaluation of a model's response, including measures of faithfulness and relevance.
    
    Attributes:
        model_name (str): The name of the model being evaluated.
        faithfulness (str): The faithfulness score of the model's response.
        relevance (float): The relevance score of the model's response.
    """
    model_name: str
    faithfulness: str
    relevance: float
    
    
class ModelEvalResponse(BaseModel):
    """
    Represents the aggregated evaluation results for multiple models, including the identification of the best model.
    
    Attributes:
        model_evaluations (List[ModelEvaluation]): A list of evaluations for the model responses.
        best_model (str): The name of the model determined to be the best based on the evaluations.
    """
    model_evaluations: List[ModelEvaluation]
    best_model: str



class Message(BaseModel):
    """
    Represents a single pair of GPT message in a conversation, indicating the role and content of the message.
    
    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'bot').
        content (str): The content of the message.
    """
    role: str
    content: str


class MessagesRequest(BaseModel):
    """
    Represents a complete user-bot interaction conversation thread, encapsulating the entire conversation history.
    
    Attributes:
        messages (List[Message]): A list of message pairs forming the conversation thread.
    """
    messages: List[Message] 