import pandas as pd
from collections import OrderedDict
from transformers import AutoTokenizer
import torch
import csv
from typing import Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup

tokenizer = AutoTokenizer.from_pretrained("Alibaba-NLP/gte-base-en-v1.5")

def ordered_set(iterable):
    """
    Removes duplicates from an iterable while preserving order.

    Args:
        iterable (iterable): The input iterable.

    Returns:
        list: A list with duplicates removed.
    """
    return list(OrderedDict.fromkeys(iterable))

def combine_result(parsed_data):
    """
    Combines parsed data into a single dictionary.

    Args:
        parsed_data (List[Dict[str, str]]): The parsed data to combine.

    Returns:
        Dict[str, str]: A dictionary with combined data.
    """
    combined_data = {}
    for data in parsed_data:
        if data['title'] in combined_data:
            combined_data[data['title']] += " " + data['content']
        else:
            combined_data[data['title']] = data['content']
    return combined_data

def check_nested_categories(response):
    """
    Checks if the response contains nested categories.

    Args:
        response (requests.Response): The HTTP response object.

    Returns:
        bool: True if nested categories are found, False otherwise.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    qa_divs = soup.find_all('div', class_='child-tab-container')
    content_outer_div = soup.find_all('div', class_='row list-content-page')
    if len(qa_divs) < 1 and len(content_outer_div) < 1:
        return True
    return False

def batch_generator(array, batch_size):
    """
    Generates batches from an array.

    Args:
        array (list): The input array.
        batch_size (int): The size of each batch.

    Yields:
        list: A batch of the input array.
    """
    for i in range(0, len(array), batch_size):
        yield array[i:i + batch_size]

def save_to_csv(data: Dict, filename: str = 'scrapped_data_v2.csv'):
    """
    Saves data to a CSV file.

    Args:
        data (Dict): The data to save.
        filename (str, optional): The name of the CSV file. Defaults to 'scrapped_data_v2.csv'.

    Returns:
        None
    """
    headers = data[0].keys()
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=headers)
        csvwriter.writeheader()
        csvwriter.writerows(data)
    print(f'Data written to {filename}')

def token_length(text):
    """
    Finds the length of tokenized text.

    Args:
        text (str): The input text.

    Returns:
        int: The length of the tokenized text.
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    global tokenizer
    with torch.no_grad():
        encoded = tokenizer(text, return_tensors='pt').to(device)
    return len(encoded['input_ids'][0])

def convert_dict_to_list(dict_data: Dict):
    """
    Converts a dictionary to a list of dictionaries.

    Args:
        dict_data (Dict): The input dictionary.

    Returns:
        List[Dict[str, str]]: A list of dictionaries.
    """
    list_data = []
    for key, value in dict_data.items():
        list_data.append({'title': key, 'content': value})
    return list_data

def preprocess_data(filepath: str = 'data.csv'):
    """
    Preprocesses data from a CSV file.

    Args:
        filepath (str, optional): The path to the CSV file. Defaults to 'data.csv'.

    Returns:
        List[str]: A list of preprocessed data.
    """
    df = pd.read_csv(filepath)
    preprocessed_data = []
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", ".", ' ', ""], chunk_size=500,
                                                   chunk_overlap=30, length_function=token_length)
    for index, row in df.iterrows():
        title = row['title'] if not pd.isna(row['title']) else ''
        content = row['content']
        chunks = text_splitter.split_text(content)
        for chunk in chunks:
            preprocessed_data.append(title + " " + chunk)
    return list(OrderedDict.fromkeys(preprocessed_data))