import math
import re
from collections import Counter, defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download("stopwords", quiet=True)
stop_words = set(stopwords.words("english"))
stemmer = PorterStemmer()

# Compound words whose first part is a single letter: "t-shirt", "t shirt" and "tshirt" all become "tshirt"
COMPOUNDS = [("t", "shirt"), ("v", "neck"), ("o", "neck"), ("u", "neck"), ("a", "line"), ("x", "large")]
COMPOUND_PATTERN = re.compile(r"\b(" + "|".join(rf"{a}[\s-]?{b}" for a, b in COMPOUNDS) + r")")

# Weights of our score (Part 3)
W_TITLE, W_DETAILS, W_DESCRIPTION = 8.0, 0.5, 0.2   # importance of each field
W_TEXT, W_RATING = 0.8, 0.2                        # text relevance vs product rating
OUT_OF_STOCK_FACTOR = 0.5                          # out-of-stock products are pushed down, not removed


# Same preprocessing as Parts 2 and 3: lowercase, compounds, alphanumeric tokens, stopword removal, Porter stemming
def preprocess_text(text):
    if not text:
        return []
    text = COMPOUND_PATTERN.sub(lambda m: re.sub(r"[\s-]", "", m.group()), text.lower())
    tokens = re.findall(r"[a-z0-9]+", text)
    return [stemmer.stem(t) for t in tokens if t not in stop_words]


# In the Document object product_details is already a dict {key: value}
def product_details_to_text(product_details):
    if not product_details:
        return ""
    return " ".join(f"{k} {v}" for k, v in product_details.items() if v is not None)


class OurScoreSearch:
    """Inverted index, AND search and our score (Part 3).
    Everything that does not depend on the query is computed once, when the object is created."""

    def __init__(self, corpus):
        self.corpus = corpus
        self.index = defaultdict(list)
        self.title_terms, self.details_terms, self.description_terms = {}, {}, {}
        self.title_brand = {}
        collection_counts = Counter()

        for pid, doc in corpus.items():
            title = preprocess_text(doc.title)
            description = preprocess_text(doc.description)
            details = preprocess_text(product_details_to_text(doc.product_details))

            # terms of each field as sets: each field counts a term only once (presence)
            self.title_terms[pid] = set(title)
            self.details_terms[pid] = set(details)
            self.description_terms[pid] = set(description)
            # key for the duplicates: same title and same brand
            self.title_brand[pid] = (tuple(title), doc.brand)

            # inverted index: term -> list of pids that contain the term
            terms = title + description + details
            collection_counts.update(terms)
            for term in set(terms):
                self.index[term].append(pid)

        # weight of every term: log(total terms of the collection / occurrences of the term in the collection)
        total_terms = sum(collection_counts.values())
        self.term_weight = {term: math.log(total_terms / count) for term, count in collection_counts.items()}

        # mean rating of the collection, used for the products without rating
        ratings = [doc.average_rating for doc in corpus.values() if doc.average_rating is not None]
        self.mean_rating = sum(ratings) / len(ratings)

    # AND search: set of pids that contain ALL the query terms
    def search_and(self, query_terms):
        if not query_terms:
            return set()
        # intersect the postings lists from the shortest to the longest; stop if it becomes empty
        postings = sorted((set(self.index.get(term, [])) for term in query_terms), key=len)
        docs = postings[0]
        for posting in postings[1:]:
            docs &= posting
            if not docs:
                break
        return docs

    # Field-weighted text score: sum over the query terms of term weight * field presence
    def text_score(self, query_terms, pid):
        score = 0.0
        for term in query_terms:
            field_tf = (W_TITLE * (term in self.title_terms[pid])
                        + W_DETAILS * (term in self.details_terms[pid])
                        + W_DESCRIPTION * (term in self.description_terms[pid]))
            score += self.term_weight.get(term, 0.0) * field_tf
        return score

    # AND search + our score: list of (pid, score) sorted by descending score, one product per (title, brand)
    def search(self, query):
        query_terms = set(preprocess_text(query))
        candidates = sorted(self.search_and(query_terms))   # sorted by pid so ties always keep the same order
        if not candidates:
            return []

        # text score of every candidate, divided by the best one of the query -> [0, 1]
        text = {pid: self.text_score(query_terms, pid) for pid in candidates}
        max_text = max(text.values()) or 1.0

        scores = []
        for pid in candidates:
            doc = self.corpus[pid]
            rating = doc.average_rating if doc.average_rating is not None else self.mean_rating
            # weighted sum of text and rating, then the stock penalty
            score = W_TEXT * text[pid] / max_text + W_RATING * rating / 5
            if doc.out_of_stock:
                score *= OUT_OF_STOCK_FACTOR
            scores.append((pid, score))
        scores.sort(key=lambda item: item[1], reverse=True)

        # duplicates: keep only the best product of each (title, brand)
        seen = set()
        unique_scores = []
        for pid, score in scores:
            if self.title_brand[pid] not in seen:
                seen.add(self.title_brand[pid])
                unique_scores.append((pid, score))
        return unique_scores
