# Project README

## Overview

This project aims to build a web application that evaluates the responses of different Large Language Models (LLMs) in a Question and Answering (Q&A) task. The models to be compared are:

1. GPT-3.5-turbo
2. GPT-4
3. Llama-2-70b-chat
4. Falcon-40b-instruct

## Key Features

- **API Development with FastAPI**: Utilizes FastAPI for building efficient and scalable APIs.
- **Vector Database Integration**: Integrates with ChromaDB for storing and querying vectorized data.
- **Machine Learning Model Integration**: Incorporates machine learning models for text processing and embedding generation using PyTorch and Transformers.
- **Web Scraping**: Includes a web scraper for collecting data from a specific website and processing it for database insertion.
- **Custom Embedding Functionality**: Provides a custom embedding function to generate and normalize embeddings using specified transformer models.
- **Prompt Engineering**: Constructs prompts that ensure LLMs reference search results from the vector database to generate responses.

## Project Structure

The project is organized into several key directories:

- `backend_service`: Contains the main logic for the backend service, including API endpoints, application logic, and data processing.
- `chromadb_data`: Stores indexed data and metadata for the ChromaDB instance.
- `scrapped_data`: Holds the data scraped from the webpages in CSV format.
- `web_scrapper`: Manages the scraping of data from the webpages and its upload to ChromaDB.

### Key Components

#### Backend Service

The `backend_service` directory is the core of the project, featuring several Python files that handle different aspects of the application:

- `api.py` & `app.py`: Define the FastAPI application and its routes.
- `custom_exceptions.py`: Contains custom exception classes for error handling.
- `embedding_func.py`: Implements the custom embedding function for creating embeddings for user input query.
- `generation_models.py`, `helper_functions.py`, `prompt.py`, `schema.py`: Support various backend functionalities, including classes for generation models, helper utilities, prompt management, and data schema definitions.

#### ChromaDB Data

The `chromadb_data` directory includes files related to the ChromaDB vector database, such as `chroma.sqlite3`, `data_level0.bin`, `header.bin`, `index_metadata.pickle`, `length.bin`, and `link_lists.bin`, which are essential for the database's operation and data storage.

#### Web Scraper

The `web_scrapper` directory contains scripts for web scraping and data processing:

- `chromadb_upload.py`: Manages the upload of scraped data to ChromaDB.
- `data_parsers.py`, `data_scrapper.py`, `embedding_func.py`, `utils.py`: Handle the scraping, parsing, and processing of web data.

## Installation and Setup

To set up this project, follow these steps:

1. **Clone the Repository**: Clone this repository to your local machine.
2. **Install Dependencies**: Run `pip install -r requirements.txt` to install the required Python packages.
3. **Configure Environment**: Set up the  necessary environment variables, such as API keys for OpenAI and Replicate as needed for this setup.
4. **Run the Backend Service**: Navigate to the `backend_service` directory and start the FastAPI server using Uvicorn with the command `uvicorn app:app --host <host_name or url> -- port <port number> --reload` or just run `python main.py`.

## Usage

### API Endpoints

The backend service provides various API endpoints for interacting with the application. These endpoints allow for operations such as submitting text for embedding generation, querying the ChromaDB database, and managing data. Below are the key endpoints available:

1. **Root Endpoint**
   - **URL**: `/api/`
   - **Method**: `GET`
   - **Description**: Returns a greeting message indicating the backend service is running.
   - **Response**: `{"Hello": "Backend Service"}`

2. **Query Models**
   - **URL**: `/api/query`
   - **Method**: `POST`
   - **Description**: Performs a semantic search based on the user's query, generates a prompt, and queries multiple generative models asynchronously.
   - **Request Body**: `QueryRequest` (contains the user's query)
   - **Response**: `QueryResponse` (contains model responses and retrieved contexts)

3. **Evaluate Model Responses**
   - **URL**: `/api/evaluate`
   - **Method**: `POST`
   - **Description**: Evaluates the responses from multiple generative models based on the provided request.
   - **Request Body**: `ModelEvalRequest` (contains the model responses to be evaluated)
   - **Response**: `ModelEvalResponse` (contains the evaluation results)

4. **WebSocket for Model Output**
   - **URL**: `/api/ws/model-output`
   - **Method**: `WebSocket`
   - **Description**: Streams model outputs based on user queries. Accepts a WebSocket connection, receives a user query, and streams the output from multiple generative models back to the client.
   - **WebSocket Messages**:
     - **Receive**: User query as text
     - **Send**: JSON objects containing model outputs for each of the following models:
       - `gpt-3.5-turbo`
       - `gpt-4-turbo`
       - `llama-2-70b-chat`
       - `falcon-40b-instruct`

### Example Usage

#### Query Models
To query multiple generative models and retrieve their responses, send a POST request to the `/api/query` endpoint with a JSON body containing the user's query.

**Request:**
```json
{
  "query": "What is the capital of France?"
}
```

**Response:**
```json
{
  "model_responses": [
    {"model_name": "gpt-3.5-turbo", "response": "The capital of France is Paris."},
    {"model_name": "gpt-4", "response": "Paris is the capital of France."},
    {"model_name": "llama-2-70b-chat","response": "France's capital is Paris."},
    {"model_name": "falcon-40b-instruct","response": "Paris is the capital city of France."}]
  "contexts": ["Relevant context retrieved from ChromaDB",..]
}
```

#### Evaluate Model Responses
To evaluate the responses from multiple generative models, send a POST request to the `/api/evaluate` endpoint with a JSON body containing the model responses to be evaluated.

**Request:**
```json
{
  "query": "captical of france?"
  "model_responses": [
    { "model_name": "gpt-3.5-turbo", "response": "The capital of France is Paris."},
    { "model_name": "gpt-4", "response": "Paris is the capital of France."},
    { "model_name": "llama-2-70b-chat", "response": "France's capital is Paris."},
    { "model_name": "falcon-40b-instruct", "response": "Paris is the capital city of France."}
  ]
  "contexts": ["Relevant context retrieved from ChromaDB",..]
}
```

**Response:**
```json
{
  "model_evaluations": [
    { "model_name": "gpt-3.5-turbo", "faithfullness":0.1, "relevance": 0.2},
    { "model_name": "gpt-4", "faithfullness":0.1, "relevance": 0.4},
    { "model_name": "llama-2-70b-chat", "faithfullness":0.6, "relevance": 0.6},
    { "model_name": "falcon-40b-instruct", "faithfullness":0.1, "relevance": 0.4}
    ],
    "best_model": "llama-2-70b-chat"
}
```

#### WebSocket for Model Output
To stream model outputs based on user queries, establish a WebSocket connection to the `/api/ws/model-output` endpoint. Send the user query as text and receive JSON objects containing model outputs.

**WebSocket Messages:**
- **Send**: `"What is the capital of France?"`
- **Receive**:
  ```json
  {"gpt-3.5-turbo": "The capital of France is Paris."}
  {"gpt-4-turbo": "Paris is the capital of France."}
  {"llama-2-70b-chat": "France's capital is Paris."}
  {"falcon-40b-instruct": "Paris is the capital city of France."}
  ```

These endpoints provide a comprehensive interface for interacting with the backend service, enabling users to query generative models, evaluate their responses, and stream model outputs in real-time.

### Web Scraper

The web scraper component of the project is designed to automate the collection of data from `https://u.ae/en/information-and-services`. This data is then processed and uploaded to the ChromaDB database, where it can be indexed and made searchable. The web scraper is an essential tool for populating the database with relevant and up-to-date information.


`data_scrapper.py`
Purpose: Directly responsible for scraping data from specified web sources. It uses libraries such as BeautifulSoup4 to navigate web pages, extract relevant information, and save it for further processing.
How to Run: This is the main script for initiating the web scraping process. Run it using the following command:
`python data_scrapper.py`


`chromadb_upload.py`
Purpose: Manages the upload of scraped data to ChromaDB. This script contains functions to take the scraped data, after some form of processing or transformation, and insert it into the ChromaDB database for indexing and retrieval.

How to Run: This file can be executed with command:
`python chromadb_upload.py`