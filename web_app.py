import os
from json import JSONEncoder
import time
from uuid import uuid4

import httpagentparser  # for getting the user agent as json
from flask import Flask, render_template, session
from flask import request, abort

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine
from myapp.generation.rag import RAGGenerator
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env


# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***


# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = os.getenv("SECRET_KEY")
# open browser dev tool to see the cookies
app.session_cookie_name = os.getenv("SESSION_COOKIE_NAME")
# instantiate our in memory persistence
analytics_data = AnalyticsData()
# instantiate RAG generator
rag_generator = RAGGenerator()

# load documents corpus into memory.
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
file_path = path + "/" + os.getenv("DATA_FILE_PATH")
corpus = load_corpus(file_path)
# Log first element of corpus to verify it loaded correctly:
print("\nCorpus is loaded... \n First element:\n", list(corpus.values())[0])

# instantiate our search engine (it builds the inverted index once, now that the corpus is loaded)
search_engine = SearchEngine(corpus)


@app.before_request
def track_request():

    excluded_paths = {
        "/stats",
        "/dashboard",
        "/plot_number_of_views",
        "/track_return"
    }

    if (
        request.path.startswith("/static/")
        or request.path in excluded_paths
    ):
        return

    if "analytics_session_id" not in session:
        session["analytics_session_id"] = str(uuid4())

    session_id = session["analytics_session_id"]

    user_agent = request.headers.get("User-Agent", "")

    agent = httpagentparser.detect(user_agent)

    browser = agent.get(
        "browser", {}
    ).get("name", "Unknown")

    os_name = agent.get(
        "os", {}
    ).get("name", "Unknown")

    user_agent_lower = user_agent.lower()

    device = (
        "Mobile"
        if any(
            term in user_agent_lower
            for term in [
                "mobile", "android", "iphone", "ipad"
            ]
        )
        else "Desktop"
    )

    analytics_data.register_session(
        session_id,
        browser,
        os_name,
        device
    )

    analytics_data.save_request(
        session_id,
        request.method,
        request.path
    )

# Home URL "/"
@app.route('/')
def index():
    print("starting home url /...")

    # flask server creates a session by persisting a cookie in the user's browser.
    # the 'session' object keeps data between multiple requests. Example:
    session['some_var'] = "Some value that is kept in session"

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    print(session)
    return render_template('index.html', page_title="Welcome")


@app.route('/search', methods=['POST'])
def search():

    search_query = request.form['search-query']

    session['last_search_query'] = search_query

    session_id = session["analytics_session_id"]

    search_id = analytics_data.save_query_terms(
        search_query,
        session_id
    )

    start_time = time.perf_counter()

    results = search_engine.search(
        search_query,
        search_id,
        corpus
    )

    retrieval_time = (
        time.perf_counter() - start_time
    ) * 1000

    analytics_data.save_search_results(
        search_id,
        results,
        retrieval_time
    )

    rag_response = rag_generator.generate_response(
        search_query,
        results
    )

    print("RAG response:", rag_response)

    found_count = len(results)

    session['last_found_count'] = found_count

    return render_template(
        'results.html',
        results_list=results,
        page_title="Results",
        found_counter=found_count,
        rag_response=rag_response,
        search_id=search_id
    )


@app.route('/doc_details', methods=['GET'])
def doc_details():

    clicked_doc_id = request.args.get("pid")

    search_id = request.args.get(
        "search_id",
        type=int
    )

    product = corpus.get(clicked_doc_id)

    if product is None:
        abort(404)

    click_id = analytics_data.save_click(
        session["analytics_session_id"],
        search_id,
        clicked_doc_id
    )

    return render_template(
        "doc_details.html",
        page_title=product.title,
        product=product,
        click_id=click_id,
        search_id=search_id
    )


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example. ### Replace with yourdashboard ###
    :return:
    """

    docs = []
    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[doc_id]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(pid=row.pid, title=row.title, description=row.description, url=row.url, count=count)
        docs.append(doc)
    
    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template('stats.html', clicks_data=docs)


@app.route('/dashboard')
def dashboard():

    summary = analytics_data.get_summary()

    top_products = sorted(
        analytics_data.fact_clicks.items(),
        key=lambda item: item[1],
        reverse=True
    )[:10]

    product_views = [
        (
            corpus[pid].title,
            count
        )
        for pid, count in top_products
        if pid in corpus
    ]

    chart_data = {
        "queries": analytics_data.get_top_queries(),
        "terms": analytics_data.get_top_terms(),
        "ranks": analytics_data.get_clicks_by_rank(),
        "hours": analytics_data.get_searches_by_hour(),
        "browsers": analytics_data.get_browsers(),
        "operating_systems": analytics_data.get_operating_systems(),
        "devices": analytics_data.get_devices(),
        "products": product_views
    }

    return render_template(
        "dashboard.html",
        page_title="Analytics Dashboard",
        summary=summary,
        chart_data=chart_data
    )


# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route('/plot_number_of_views', methods=['GET'])
def plot_number_of_views():
    return analytics_data.plot_number_of_views()

@app.route('/track_return', methods=['POST'])
def track_return():

    data = request.get_json(silent=True) or {}

    click_id = data.get("click_id")

    session_id = session.get("analytics_session_id")

    if not isinstance(click_id, int):
        return "", 400

    if session_id is None:
        return "", 400

    analytics_data.save_dwell_time(
        click_id,
        session_id
    )

    return "", 204


if __name__ == "__main__":
    app.run(port=8088, host="127.0.0.1", threaded=False, debug=os.getenv("DEBUG"))
