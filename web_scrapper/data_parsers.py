from bs4 import BeautifulSoup
from utils import ordered_set, combine_result

def parse_nested_text(tag):
    """
    Parses nested text within a given HTML tag, excluding anchor tags.

    Args:
        tag (bs4.element.Tag): The HTML tag to parse.

    Returns:
        str: The concatenated and cleaned text content.
    """
    content = []
    for elem in tag.descendants:
        if elem.name == 'a':
            pass
        elif elem.string:
            content.append(elem.string.strip())
    return " ".join(ordered_set(content)).strip()

def parse_title_and_content(div, section_title: str = ''):
    """
    Parses the title and content from a given div element.

    Args:
        div (bs4.element.Tag): The div element to parse.
        section_title (str, optional): The section title to use. Defaults to ''.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the parsed title and content.
    """
    parsed_content = []
    for child in div.children:
        if child.name == 'h3':
            section_title = child.get_text(strip=True)
        if child.name == 'p':
            content = parse_nested_text(child)
            parsed_content.append({"title": section_title, 'content': content}) if content != '' else False
        elif child.name == 'a':
            href = child.get('href')
            link_text = child.get_text(strip=True)
            content = f"{link_text}"
            parsed_content.append({"title": section_title, 'content': content}) if content != '' else False
        elif child.name == 'ul':
            list_items = child.find_all('li')
            for index, li in enumerate(list_items, start=1):
                content = f"\n{index}) {parse_nested_text(li)}"
                parsed_content.append({"title": section_title, 'content': content}) if content != '' else False
            parsed_content.append({"title": section_title, 'content': '\n'})
        elif child.name is None:
            # This handles the case where the text is directly within the div
            for string in child.stripped_strings:
                parsed_content.append({"title": section_title, 'content': (string)}) if string != '' else False
    return parsed_content

def parse_goverment_services(response):
    """
    Parses government services from the given HTTP response.

    Args:
        response (requests.Response): The HTTP response object.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the parsed government services.
    """
    parsed_data = []
    soup = BeautifulSoup(response.content, 'html.parser')  
    # Parse providing entities
    divs = soup.find_all('div', id='entities')
    for div in divs:
        gov_entities = div.find_all('h3')
        for index, gov_entity in enumerate(gov_entities):
            parsed_data.append({'title': 'Providing entities', 'content': f"{index+1}) {gov_entity.text.strip()}\n"})
    # Parse offered services
    divs = soup.find_all('div', id='services')
    for div in divs:
        services = div.find_all('div', class_='col-md-12')
        for index, service in enumerate(services):
            parsed_data.append({'title': "Offered " + service.find('span').text.strip(), 'content': f"{index+1}) {service.find('h3').text.strip()}\n"})
    # Parse services provided by entities
    divs = soup.find_all('div', id='entitiestype')
    for div in divs:
        gov_entites = div.find_all('div', class_='services-by-entity')
        for gov_entity in gov_entites:
            entity_services = gov_entity.find_all('div', class_='col-md-12')
            for index, entity_service in enumerate(entity_services):
                parsed_data.append({'title': ' Services provided by ' + entity_service.find('span').text.strip(), 'content': f"{index+1}) {entity_service.find('h3').text.strip()}\n"})
    return combine_result(parsed_data)

def parse_data(response):
    """
    Parses data from the given HTTP response.

    Args:
        response (requests.Response): The HTTP response object.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the parsed data.
    """
    scraped_data = []
    # Parse the webpage content
    soup = BeautifulSoup(response.content, 'html.parser')
    qa_divs = soup.find_all('div', class_='child-tab-container')
    # Iterate through each div
    for qa_div in qa_divs:
        scraped_data.extend(parse_title_and_content(qa_div))
    if len(scraped_data) < 1:
        heading = soup.find('h2')
        if heading:
            heading = heading.text.strip()
        content_outer_div = soup.find('div', class_='row list-content-page')
        content_div = content_outer_div.find('div', class_='col-md-12')
        scraped_data = parse_title_and_content(content_div, section_title=heading)
    return combine_result(scraped_data)