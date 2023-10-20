import requests
import bs4


def get_defaul_volpiano_string():
    """When creating a new melody, we always initialize with this,
    so that the Volpiano field of a melody is never empty."""
    return '1---'

def get_soup(url):
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    return soup


def get_soup_for_cantus_id(cantus_id):
    url = 'https://cantusindex.org/id/{}'.format(cantus_id)
    return get_soup(url)


def get_full_text_from_cantus_id_soup(soup):
    text_field = soup.find('div', class_='field-name-body')
    print('...CI scrape: text field: {}'.format(text_field))
    text_item = text_field.find(class_='field-item')
    print('...CI scrape: text item: {}'.format(text_item))
    text = text_item.text
    return text


def get_full_text_for_cantus_id(cantus_id):
    soup = get_soup_for_cantus_id(cantus_id)
    return get_full_text_from_cantus_id_soup(soup)
