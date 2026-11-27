from urllib.parse import urlencode
from myapp.search.algorithms import OurScoreSearch
from myapp.search.objects import ResultItem


class SearchEngine:
    """Class that implements the search engine logic"""

    def __init__(self, corpus):
        print("Building the inverted index...")
        self.searcher = OurScoreSearch(corpus)
        print("Index ready")

    def search(self, search_query, search_id, corpus):
        print("Search query:", search_query)

        results = []

        ranked_products = self.searcher.search(search_query)

        for rank, (pid, score) in enumerate(
            ranked_products,
            start=1
        ):
            doc = corpus[pid]

            params = urlencode({
                "pid": pid,
                "search_id": search_id,
                "rank": rank
            })

            result = ResultItem(
                **doc.model_dump(),
                ranking=score,
                rank=rank,
                search_id=search_id,
                details_url=f"/doc_details?{params}"
            )

            results.append(result)

        return results