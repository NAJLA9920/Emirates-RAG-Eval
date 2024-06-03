from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from data_parsers import parse_data, parse_goverment_services
from utils import check_nested_categories, convert_dict_to_list, save_to_csv

MAIN_URL = 'https://u.ae/en/information-and-services'
DATA_FILE_PATH = 'scrapped_data/scrapped_data_v2.csv'

def scrape_website(response, visited_pages: List[str]):
    """
    Recursively scrapes a website for data, handling nested categories.

    Args:
        response (requests.Response): The HTTP response object from the initial request.
        visited_pages (List[str]): A list of URLs that have already been visited to avoid duplication.

    Returns:
        Tuple[Dict[str, str], List[str]]: A tuple containing the scraped data and the updated list of visited pages.
    """
    scraped_data = {}
    is_nested = check_nested_categories(response)
    if not is_nested:
        return parse_data(response), visited_pages
    soup = BeautifulSoup(response.content, 'html.parser')
    sub_category_divs = soup.find_all('div', class_='col-md-3')
    for sub_category_div in sub_category_divs:
        sub_category_link = sub_category_div.find('a')
        try:
            complete_sub_category_link = 'https://u.ae' + sub_category_link.get('href')
        except Exception as e:
            print(f"Incorrect sub-category link: {e}")
            continue
        if complete_sub_category_link in visited_pages:
            print(f"Webpage {complete_sub_category_link} already visited")
            continue
        visited_pages.append(complete_sub_category_link)
        print(f"Fetching contents of webpage: {complete_sub_category_link}")
        sub_category_response = requests.get(complete_sub_category_link)
        if sub_category_response.status_code == 200:
            is_nested = check_nested_categories(sub_category_response)
            if is_nested:
                # Recursively scrape nested categories
                scraped_result, visited_pages = scrape_website(sub_category_response, visited_pages=visited_pages)
                scraped_data.update(scraped_result)
            else:
                try:
                    # Parse data from the current sub-category page
                    scraped_data.update(parse_data(sub_category_response))
                except Exception as e:
                    print(f"Error parsing data from webpage {complete_sub_category_link}: {e}")
                    continue
        else:
            print(f"Failed to retrieve the webpage. Status code: {sub_category_response.status_code}")
            return scraped_data, visited_pages
    return scraped_data, visited_pages


def scraping_pipeline(url: str = 'https://u.ae/en/information-and-services') -> Dict[str, str]:
    """
    Main pipeline to scrape data from the specified URL.

    Args:
        url (str): The URL to start scraping from. Default is 'https://u.ae/en/information-and-services'.

    Returns:
        Dict[str, str]: A dictionary containing the complete scraped data.
    """
    complete_scraped_data = {}
    visited_pages = []
    special_case = 'https://u.ae/en/information-and-services/top-government-services'
    main_page_response = requests.get(url)
    if main_page_response.status_code == 200:
        visited_pages.append(url)
        main_soup = BeautifulSoup(main_page_response.content, 'html.parser')
        category_section = main_soup.find('div', class_='row ui-filter-items row-flex')
        category_links = category_section.findAll('a')
        for category_link in category_links:
            complete_category_link = 'https://u.ae' + category_link.get('href')
            if complete_category_link in visited_pages:
                print(f"Webpage {complete_category_link} already visited")
                continue
            print(f"Fetching contents of webpage: {complete_category_link}")
            category_response = requests.get(complete_category_link)
            if category_response.status_code == 200:
                visited_pages.append(complete_category_link)
                if complete_category_link == special_case:
                    # Handle special case for top government services
                    scrapped_data = parse_goverment_services(category_response)
                    complete_scraped_data.update(scrapped_data)
                else:
                    # Scrape data from the category page
                    scrapped_data, visited_pages = scrape_website(category_response, visited_pages=visited_pages)
                    complete_scraped_data.update(scrapped_data)
            else:
                print(f"Failed to retrieve the webpage. Status code: {category_response.status_code}")
        return complete_scraped_data
    else:
        print(f"Failed to retrieve the webpage. Status code: {main_page_response.status_code}")
        return complete_scraped_data
    

if __name__ == '__main__':
    main_data = scraping_pipeline(url=MAIN_URL)
    converted_data = convert_dict_to_list(main_data)
    save_to_csv(data=converted_data, filename=DATA_FILE_PATH)