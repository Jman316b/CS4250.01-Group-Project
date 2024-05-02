from bs4 import BeautifulSoup
from pymongo import MongoClient

client = MongoClient()
db = client['crawler']
pages = db['pages']
professors = db['professors']


for html in pages.find({'url': 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'}):
    bs = BeautifulSoup(html.get('html'), 'html.parser')
    for prof in bs.find('section', class_='text-images').findAll('div', class_="clearfix"):
        if prof.h2 is not None:
            professor = {
                "name": prof.h2.getText(),
                "title": prof.p.strong.next_sibling,
                "office": prof.strong.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling,
                "phone": prof.strong.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling,
                "email": prof.strong.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.getText()
            }
            professors.insert_one(professor)
