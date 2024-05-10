from pymongo import MongoClient

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd


def main():
    client = MongoClient()
    db = client['ce_crawler_db']
    collection_pages = db['professor_pages']

    documents = []
    websites = []
    for prof in collection_pages.find():
        # Convert the text array to a single string and add it as a document
        documents.append(" ".join(prof.get("website_text")))
        websites.append(prof.get("website"))

    # Instantiate the vectorizer object
    tfidfvectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
    document_v = tfidfvectorizer.fit_transform(documents)
    tfidf_tokens = tfidfvectorizer.get_feature_names_out()
    data_frame = pd.DataFrame(data=document_v.toarray(), columns=tfidf_tokens)

    # Train on query
    query = []
    print("What is your search?")
    query.append(input())
    query_v = tfidfvectorizer.transform(query)
    tfidf_tokens = tfidfvectorizer.get_feature_names_out()
    query_data_frame = pd.DataFrame(data=query_v.toarray(), columns=tfidf_tokens)

    # Cosine Similarity
    cos_sim = cosine_similarity(query_data_frame, data_frame)
    sorted_list_with_index = sorted(enumerate(cos_sim[0]), key=lambda x: x[1], reverse=True)

    for index, value in sorted_list_with_index:
        print(websites[index])


if __name__ == "__main__":
    main()
