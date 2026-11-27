import json
from datetime import datetime
from collections import Counter

import altair as alt
import pandas as pd


class AnalyticsData:

    def __init__(self):
        self.sessions = {}
        self.requests = []
        self.searches = {}
        self.clicks = {}

        self.fact_clicks = {}

        self.next_search_id = 1
        self.next_click_id = 1

    @staticmethod
    def now():
        return datetime.now()

    def register_session(
        self, session_id, browser, os_name, device
    ):
        now = self.now()

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "browser": browser,
                "os": os_name,
                "device": device,
                "first_visit": now,
                "last_visit": now
            }
        else:
            self.sessions[session_id]["last_visit"] = now

    def save_request(self, session_id, method, path):
        self.requests.append({
            "session_id": session_id,
            "method": method,
            "path": path,
            "timestamp": self.now()
        })

    def save_query_terms(self, terms, session_id=None):
        search_id = self.next_search_id
        self.next_search_id += 1

        query_terms = terms.lower().split()

        self.searches[search_id] = {
            "search_id": search_id,
            "session_id": session_id,
            "query": terms,
            "terms": query_terms,
            "number_of_terms": len(query_terms),
            "timestamp": self.now(),
            "result_count": None,
            "retrieval_time": None,
            "result_ranks": {}
        }

        return search_id

    def save_search_results(
        self, search_id, results, retrieval_time
    ):
        if search_id not in self.searches:
            return

        search = self.searches[search_id]

        search["result_count"] = len(results)
        search["retrieval_time"] = retrieval_time

        search["result_ranks"] = {
            result.pid: rank
            for rank, result in enumerate(results, start=1)
        }

    def save_click(self, session_id, search_id, pid):
        search = self.searches.get(search_id)

        if search is None:
            return None

        if search["session_id"] != session_id:
            return None

        rank = search["result_ranks"].get(pid)

        if rank is None:
            return None

        click_id = self.next_click_id
        self.next_click_id += 1

        self.clicks[click_id] = {
            "click_id": click_id,
            "session_id": session_id,
            "search_id": search_id,
            "pid": pid,
            "rank": rank,
            "timestamp": self.now(),
            "dwell_time": None
        }

        self.fact_clicks[pid] = (
            self.fact_clicks.get(pid, 0) + 1
        )

        return click_id

    def save_dwell_time(self, click_id, session_id):
        click = self.clicks.get(click_id)

        if click is None:
            return

        if click["session_id"] != session_id:
            return

        if click["dwell_time"] is not None:
            return

        dwell_time = (
            self.now() - click["timestamp"]
        ).total_seconds()

        click["dwell_time"] = round(dwell_time, 2)

    def get_summary(self):
        searches = [
            search
            for search in self.searches.values()
            if search["result_count"] is not None
        ]

        clicks = list(self.clicks.values())

        total_searches = len(searches)
        total_clicks = len(clicks)

        clicked_searches = len({
            click["search_id"] for click in clicks
        })

        zero_results = sum(
            search["result_count"] == 0
            for search in searches
        )

        dwell_times = [
            click["dwell_time"]
            for click in clicks
            if click["dwell_time"] is not None
        ]

        def average(values):
            return round(
                sum(values) / len(values), 2
            ) if values else 0

        return {
            "total_sessions": len(self.sessions),
            "total_requests": len(self.requests),
            "total_searches": total_searches,
            "total_clicks": total_clicks,

            "ctr": round(
                100 * clicked_searches / total_searches, 2
            ) if total_searches else 0,

            "zero_result_rate": round(
                100 * zero_results / total_searches, 2
            ) if total_searches else 0,

            "avg_query_length": average([
                search["number_of_terms"]
                for search in searches
            ]),

            "avg_results": average([
                search["result_count"]
                for search in searches
            ]),

            "avg_clicked_rank": average([
                click["rank"]
                for click in clicks
            ]),

            "avg_retrieval_time": average([
                search["retrieval_time"]
                for search in searches
                if search["retrieval_time"] is not None
            ]),

            "avg_dwell_time": average(dwell_times),

            "measured_dwell_times": len(dwell_times)
        }

    # -------------------------
    # CHART DATA
    # -------------------------

    def get_top_queries(self):
        counter = Counter(
            search["query"].lower().strip()
            for search in self.searches.values()
        )

        return counter.most_common(10)

    def get_top_terms(self):
        counter = Counter(
            term
            for search in self.searches.values()
            for term in search["terms"]
        )

        return counter.most_common(10)

    def get_clicks_by_rank(self):
        counter = Counter(
            click["rank"]
            for click in self.clicks.values()
        )

        return sorted(counter.items())

    def get_searches_by_hour(self):
        counter = Counter(
            search["timestamp"].hour
            for search in self.searches.values()
        )

        return [
            (hour, counter.get(hour, 0))
            for hour in range(24)
        ]

    def get_browsers(self):
        counter = Counter(
            session["browser"]
            for session in self.sessions.values()
        )

        return counter.most_common()

    def get_operating_systems(self):
        counter = Counter(
            session["os"]
            for session in self.sessions.values()
        )

        return counter.most_common()

    def get_devices(self):
        counter = Counter(
            session["device"]
            for session in self.sessions.values()
        )

        return counter.most_common()

    # -------------------------
    # EXISTING DOCUMENT CHART
    # -------------------------

    def plot_number_of_views(self):
        data = [
            {
                "Document ID": pid,
                "Number of Views": count
            }
            for pid, count in self.fact_clicks.items()
        ]

        df = pd.DataFrame(
            data,
            columns=["Document ID", "Number of Views"]
        )

        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Document ID:N", sort="-y"),
            y="Number of Views:Q"
        ).properties(
            title="Number of Views per Document"
        )

        return chart.to_html()


class ClickedDoc:

    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        return json.dumps(self.to_json())