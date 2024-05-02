import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient

def retrieve_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            print("Retrieved HTML from", url)
            html = response.read()
            return html
    except Exception as e:
        print("Error retrieving HTML:", e)
        return None

def parse(html, base_url):
    professor_info = []
    soup = BeautifulSoup(html, 'html.parser')
    for card in soup.find_all('div', class_='col-md directory-listing'):
        name = card.find('h3').get_text(strip=True)
        website_link = None
        for link in card.find_all('a'):
            if 'Website' in link.get_text():
                website_link = link
                break
        if website_link:
            website_url = urllib.parse.urljoin(base_url, website_link['href'])
            professor_info.append({'name': name, 'website_url': website_url})
    return professor_info
        
def crawl_professor_websites(professors_dict, collection):
    professor_pages = []
    for name, website_url in professors_dict.items():
        try:
            with urllib.request.urlopen(website_url) as response:
                html_content = response.read()
                soup = BeautifulSoup(html_content, 'html.parser')

                span10 = soup.find('div', class_='span10')
                if span10:
                    name = span10.find('h1').get_text(strip=True)
                    title_dept = span10.find('span', class_='title-dept').get_text(strip=True)
                    email = span10.find('div', class_='menu-left').find('a').get_text(strip=True)
                    phone_number = span10.find('div', class_='menu-left').find('p', class_='phoneicon').get_text(strip=True)
                    office_location = span10.find('div', class_='menu-right').find('p', class_='locationicon').get_text(strip=True)
                    office_hours = span10.find('div', class_='menu-right').find('p', class_='hoursicon').get_text(strip=True)

                    main_body = soup.find('div', id='main-body')
                    if main_body:
                        sections = main_body.find_all('div', class_='blurb')
                        website_text = []
                        for section in sections:
                            section_text = section.find('div', class_='section-text')
                            if section_text:

                                website_text.append(section_text.get_text(strip=True))
                                

                                col_div = section.find('div', class_='col')
                                if col_div:

                                    ul_elements = col_div.find_all('ul')
                                    for ul in ul_elements:

                                        li_elements = ul.find_all('li')
                                        for li in li_elements:
                                            website_text.append(li.get_text(strip=True))
                        
                        accolades_aside = soup.find('aside', class_='span3 fac rightcol')
                        if accolades_aside:
                            research_interest = accolades_aside.find('div', class_='accolades').get_text(strip=True)
                            website_text.append(research_interest)
                        
                        professor_pages.append({
                            'name': name,
                            'title_dept': title_dept,
                            'website': website_url,
                            'email': email,
                            'phone_number': phone_number,
                            'office_location': office_location,
                            'office_hours': office_hours,
                            'website_text': website_text
                        })
        except urllib.error.HTTPError as e:
            print(f"HTTPError: {e.code} - {e.reason} for URL: {website_url}")
        except urllib.error.URLError as e:
            print(f"URLError: {e.reason} for URL: {website_url}")

    for professor_page in professor_pages:
        collection.insert_one(professor_page)
        print("Stored professor page for", professor_page['name'])
    


def crawler_thread(frontier, professors_dict, base_url):
    while not frontier.done():
        url = frontier.next_url()
        html = retrieve_html(url)
        if html:
            professor_info = parse(html, base_url)
            for info in professor_info:
                name = info['name']
                website_url = info['website_url']
                if website_url:
                    professors_dict[name] = website_url
            

class Frontier:
    def __init__(self):
        self.urls = []
        self.visited_urls = set()

    def add_url(self, url):
        if url not in self.visited_urls:
            self.urls.append(url)

    def next_url(self):
        url = self.urls.pop(0)
        self.visited_urls.add(url)
        return url

    def done(self):
        return len(self.urls) == 0

    def clear(self):
        self.urls.clear()
        self.visited_urls.clear()

def main():
    start_url = "https://www.cpp.edu/engineering/ce/faculty.shtml"
    frontier = Frontier()
    frontier.add_url(start_url)

    professors_dict = {}

    crawler_thread(frontier, professors_dict, start_url)

    client = MongoClient()
    db = client['ce_crawler_db']
    collectionpages = db['professor_pages']

    crawl_professor_websites(professors_dict, collectionpages)

if __name__ == "__main__":
    main()
