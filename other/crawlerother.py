import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient


def retrieveHTML(url):
    return urlopen(url)


def storePage(url, htmlFromURL):
    page = {
        "url": url,
        "html": htmlFromURL.read().decode('utf-8', 'ignore')
    }

    client = MongoClient()
    db = client['crawler']
    collection = db['pages']
    collection.insert_one(page)


def target_page(htmlFromURL):
    target = "Permanent Faculty"
    bs = BeautifulSoup(htmlFromURL, 'html.parser')
    header = bs.h1.getText()
    value = target == header
    return value


def parse(htmlFromURL):
    bs = BeautifulSoup(htmlFromURL, 'html.parser')
    urls = []
    for foundUrl in bs.findAll('a'):
        href = foundUrl.get('href')
        url = urllib.parse.urljoin("https://www.cpp.edu/sci/computer-science/", href)
        if url.startswith("https://www.cpp.edu/sci/computer-science/"):
            urls.append(url)

    return urls


class Frontier:
    def __init__(self):
        self.urls = []
        self.visited_urls = set()

    def addURL(self, url):
        if url not in self.visited_urls:
            self.urls.append(url)

    def nextURL(self):
        url = self.urls.pop(0)
        self.visited_urls.add(url)
        return url

    def done(self):
        return len(self.urls) == 0

    def clear_frontier(self):
        self.urls.clear()
        self.visited_urls.clear()


def crawlerThread(frontier):
    while not frontier.done():
        url = frontier.nextURL()
        storePage(url, retrieveHTML(url))
        if target_page(retrieveHTML(url)):
            frontier.clear_frontier()
        else:
            for url in parse(retrieveHTML(url)):
                frontier.addURL(url)


startURL = 'https://www.cpp.edu/sci/computer-science/'

frontier = Frontier()
frontier.addURL(startURL)
crawlerThread(frontier)
