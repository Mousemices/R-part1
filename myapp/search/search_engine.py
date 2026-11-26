from myapp.search.algorithms import OurScoreSearch
from myapp.search.objects import Document


class SearchEngine:
    """Class that implements the search engine logic"""

    def __init__(self, corpus):
        # inverted index and everything our score needs, built once when the app starts
        print("Building the inverted index...")
        self.searcher = OurScoreSearch(corpus)
        print("Index ready")

    def search(self, search_query, search_id, corpus):
        print("Search query:", search_query)

        # AND search + our score (Part 3)
        results = []
        for pid, score in self.searcher.search(search_query):
            doc = corpus[pid]
            results.append(Document(pid=doc.pid, title=doc.title, description=doc.description,
                                    url="doc_details?pid={}&search_id={}".format(doc.pid, search_id), ranking=score))
        return results
