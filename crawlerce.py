import re
import urllib.request
import urllib.parse
import urllib.error
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


def parse_start_url(html, base_url):
    # Parse the HTML to find the start URL
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a'):
        if 'Faculty and Staff' in link.get_text():
            start_url = urllib.parse.urljoin(base_url, link['href'])
            return start_url
    return None


def parse_professors(html, base_url):
    # Parse the HTML to find the professors and their websites
    professor_info = {}
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
            professor_info[name] = website_url
    return professor_info


def strip_text(text: str) -> str:
    # replace whitespace \n etc with space
    text = re.sub(r'\s+', ' ', text)
    # replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    return text


def crawl_professor_websites(professors_dict, collection):
    professor_pages = []
    for name, website_url in professors_dict.items():
        try:
            with urllib.request.urlopen(website_url) as response:
                html_content = response.read()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Span10 is the top section of the professor's website that contains the professor's info
                span10 = soup.find('div', class_='span10')
                if span10:
                    name = span10.find('h1').get_text(strip=True)
                    title_dept = span10.find('span', class_='title-dept').get_text(strip=True)
                    email = span10.find('div', class_='menu-left').find('a').get_text(strip=True)
                    phone_number = span10.find('div', class_='menu-left').find('p', class_='phoneicon').get_text(strip=True)
                    office_location = span10.find('div', class_='menu-right').find('p', class_='locationicon').get_text(strip=True)
                    office_hours = span10.find('div', class_='menu-right').find('p', class_='hoursicon').get_text(strip=True)
                    
                    # Main body of the professor's website that contains the research interests and other info
                    main_body = soup.find('div', id='main-body')
                    if main_body:
                        
                        # Blurb is each container within the middle portion of the page 
                        sections = main_body.find_all('div', class_='blurb')
                        website_text = []
                        for section in sections:
                            # Section text is the title/text within each blurb
                            section_text = section.find('div', class_='section-text')
                            if section_text:
                                website_text.append(strip_text(section_text.get_text()))
                                
                                # Col div is the text within the section text
                                col_div = section.find('div', class_='col')
                                if col_div:
                                    website_text.append(strip_text(col_div.get_text()))
                        
                        # accolades_aside is the right column of the page that contains the other important stuff
                        accolades_aside = soup.find('aside', class_='span3 fac rightcol')
                        if accolades_aside:
                            website_text.append(
                                strip_text(accolades_aside.find('div', class_='accolades').get_text())
                            )

                        # Add the professor's info to the list of professor pages
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

    # Store the professor pages in the database
    for professor_page in professor_pages:
        collection.insert_one(professor_page)
        print("Stored professor page for", professor_page['name'])


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
    # Connect to database and collection to store the professor pages
    client = MongoClient()
    db = client['ce_crawler_db']
    collection_pages = db['professor_pages']

    # Seed URL to find the start URL
    seed_url = "https://www.cpp.edu/engineering/ce/index.shtml"
    seed_html = retrieve_html(seed_url)
    if seed_html:
        start_url = parse_start_url(seed_html, seed_url)
        if start_url:
            print("Start URL:", start_url)
            frontier = Frontier()
            frontier.add_url(start_url)
            professor_info = {}  # Accumulate professor information here

            # Start the crawler that adds professors + their websites to the dictionary
            while not frontier.done():
                url = frontier.next_url()
                html = retrieve_html(url)
                if html:
                    parsed_info = parse_professors(html, start_url)
                    professor_info.update(parsed_info)  # Update the accumulated professor info
                    for info in parsed_info.values():
                        frontier.add_url(info)
            
            # Crawl each professor website from the dictionary to get all relevant info.
            crawl_professor_websites(professor_info, collection_pages)
        else:
            print("Start URL not found in seed HTML.")
    else:
        print("Failed to retrieve seed HTML.")


if __name__ == "__main__":
    main()
