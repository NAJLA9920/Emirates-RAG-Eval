from typing import List
import chromadb
from utils import preprocess_data, batch_generator
from embedding_func import CustomEmbeddingFunction


DATA_FILE_PATH = './scrapped_data/scrapped_data_v2.csv'
COLLECTION_NAME = 'info-services-index'
CHROMADB_STORAGE_PATH = '/content/chroma'


def upload_to_chromadb(preprocessed_data: List, collection_name: str, chromadb_storage_path: str):
    """
    Uploads preprocessed data to ChromaDB, creating vector embeddings.

    Args:
        preprocessed_data (List): The preprocessed data to be uploaded.
        collection_name (str): The name of the collection in ChromaDB.
        chromadb_storage_path (str): The storage path for ChromaDB.

    Returns:
        None
    """
    client = chromadb.PersistentClient(path=chromadb_storage_path)
    custom_embeddings = CustomEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=custom_embeddings,
        metadata={"hnsw:space": "cosine", 'dimension': 768}  # l2 is the default
    )
    counter = 0
    batch_generator_obj = batch_generator(array=preprocessed_data, batch_size=64)
    for batch in batch_generator_obj:
        collection.add(
            documents=batch,
            ids=[f"id{idx}" for idx in range(counter, counter + len(batch))]
        )
        counter += len(batch)
    print("successfully created vector embeddings and uploaded to chromadb")
    
     
if __name__ == "__main__":
    preprocessed_data = preprocess_data(DATA_FILE_PATH)
    upload_to_chromadb(preprocessed_data=preprocessed_data,collection_name=COLLECTION_NAME,chromadb_storage_path=CHROMADB_STORAGE_PATH)