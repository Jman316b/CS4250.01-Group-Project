from PyQt5.QtWidgets import QMainWindow, QPushButton
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
        self.profName = []
        self.profEmail = []
        for prof in self.collection_pages.find():
            # Convert the text array to a single string and add it as a document
            self.documents.append(" ".join(prof.get("website_text")))
            self.websites.append(prof.get("website"))
            self.profName.append(prof.get("name"))
            self.profEmail.append(prof.get("email"))

        # Instantiate the vectorizer object
        self.tfidfvectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
        self.document_v = self.tfidfvectorizer.fit_transform(self.documents)
        self.tfidf_tokens = self.tfidfvectorizer.get_feature_names_out()
        self.data_frame = pd.DataFrame(data=self.document_v.toarray(), columns=self.tfidf_tokens)
        self.show()
        self.widget.hide()
        self.searchBtn.clicked.connect(self.searchBtnClicked)
        
        self.btn1.clicked.connect(lambda: self.btnClicked(0))
        self.btn2.clicked.connect(lambda: self.btnClicked(1))
        self.btn3.clicked.connect(lambda: self.btnClicked(2))
        self.btn4.clicked.connect(lambda: self.btnClicked(3))
        self.btn5.clicked.connect(lambda: self.btnClicked(4))
        
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
        self.sorted_list_with_index = sorted(enumerate(cos_sim[0]), key=lambda x: x[1], reverse=True)

        search_result_html = ""
        for index, value in self.sorted_list_with_index[:5]:
            website = self.websites[index]
            profName = self.profName[index]
            profEmail = self.profEmail[index]
            
            search_result_html += f'Name: {profName}<br>'
            search_result_html += f'Email: {profEmail}, Website: </p>'
            search_result_html += f'<a href="{website}">{website}</a><br><br>'
        
        self.searchResult.setText(search_result_html)
        self.widget.show()
        self.btn1.setStyleSheet("font-size: 18pt;\n"
                                    "border-style: solid;\n"
                                    "border-width: 1px;\n"
                                    "border-color: black;\n"
                                    "border-radius: 5px;\n"
                                    "background-color: lightblue;\n"
                                    "color: rgb(0, 85, 0);")
    
    def btnClicked(self, btn_index):
        search_result_html = ""
        start_index = btn_index * 5
        end_index = start_index + 5

        for index, value in self.sorted_list_with_index[start_index:end_index]:
            website = self.websites[index]
            profName = self.profName[index]
            profEmail = self.profEmail[index]
            
            search_result_html += f'Name: {profName}<br>'
            search_result_html += f'Email: {profEmail}, Website: </p>'
            search_result_html += f'<a href="{website}">{website}</a><br><br>'
        
        self.searchResult.setText(search_result_html)

        for btn in [self.btn1, self.btn2, self.btn3, self.btn4, self.btn5]:
            btn.setStyleSheet("font-size: 18pt;\n"
                                "border-style: solid;\n"
                                "border-width: 1px;\n"
                                "border-color: black;\n"
                                "border-radius: 5px;\n"
                                "background-color: rgb(255, 255, 255);\n"
                                "color: rgb(0, 85, 0);")

        sender_btn = self.sender()
        if isinstance(sender_btn, QPushButton):
            sender_btn.setStyleSheet("font-size: 18pt;\n"
                                        "border-style: solid;\n"
                                        "border-width: 1px;\n"
                                        "border-color: black;\n"
                                        "border-radius: 5px;\n"
                                        "background-color: lightblue;\n"
                                        "color: rgb(0, 85, 0);")

    def openLink(self, url):
        QDesktopServices.openUrl(QUrl(url))