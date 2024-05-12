from PyQt5.QtWidgets import QMainWindow
from SearchEngineUi import Ui_MainWindow
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class SearchEngineAttached(Ui_MainWindow, QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.client = MongoClient()
        self.db = self.client['ce_crawler_db']
        self.collection_pages = self.db['professor_pages']
        
        self.documents = []
        self.websites = []
        for prof in self.collection_pages.find():
            # Convert the text array to a single string and add it as a document
            self.documents.append(" ".join(prof.get("website_text")))
            self.websites.append(prof.get("website"))
        
        # Instantiate the vectorizer object
        self.tfidfvectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
        self.document_v = self.tfidfvectorizer.fit_transform(self.documents)
        self.tfidf_tokens = self.tfidfvectorizer.get_feature_names_out()
        self.data_frame = pd.DataFrame(data=self.document_v.toarray(), columns=self.tfidf_tokens)
        self.show()
        self.searchBtn.clicked.connect(self.searchBtnClicked)
        self.searchResult.setOpenExternalLinks(True)
        self.searchResult.linkActivated.connect(self.openLink)
    
    def searchBtnClicked(self):
        text = self.searchBox.text()
        query = []
        query.append(text)
        query_v = self.tfidfvectorizer.transform(query)
        tfidf_tokens = self.tfidfvectorizer.get_feature_names_out()
        query_data_frame = pd.DataFrame(data=query_v.toarray(), columns=tfidf_tokens)

        # Cosine Similarity
        cos_sim = cosine_similarity(query_data_frame, self.data_frame)
        sorted_list_with_index = sorted(enumerate(cos_sim[0]), key=lambda x: x[1], reverse=True)

        search_result_html = ""
        for index, value in sorted_list_with_index[:5]:
            website = self.websites[index]
            search_result_html += f'<a href="{website}">{website}</a><br>'
            print(self.websites[index])
        
        self.searchResult.setText(search_result_html)
    
    def openLink(self, url):
        QDesktopServices.openUrl(QUrl(url))