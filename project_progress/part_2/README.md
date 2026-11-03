# Part 2 – Indexing and Evaluation

This folder contains our solution for Part 2 of the IRWA Final Project.

| File | Content |
|---|---|
| `02_indexing_evaluation.ipynb` | Code: inverted index, AND search, TF-IDF ranking and evaluation metrics |
| `custom_query_labels.csv` | Our relevance judgements (0/1) for the five test queries |
| `IRWA-2026-uXXXXXX-uXXXXXX-uXXXXXX-part-2.pdf` | Report (also uploaded to Aula Global) |

## Requirements

- Python 3.9 or later
- Packages: `nltk`, `pandas`, `numpy`, `matplotlib`, `jupyter`

## How to run

1. Clone the repository and go to the Part 2 tag:
   ```bash
   git clone https://github.com/Mousemices/R-part1.git
   cd R-part1
   git checkout IRWA-2026-part-2
   ```
2. Put the data files in the `data/` folder at the repository root (the folder is in `.gitignore` because the dataset is 66 MB):
   ```
   data/fashion_products_dataset.json
   data/validation_labels.csv
   ```
3. Create and activate a virtual environment and install the packages:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install nltk pandas numpy matplotlib jupyter
   ```
4. Start Jupyter **from this folder** (`project_progress/part_2/`), because the notebook finds the data with the relative path `../../data/`:
   ```bash
   cd project_progress/part_2
   jupyter notebook 02_indexing_evaluation.ipynb
   ```
5. Run all the cells in order (*Kernel → Restart & Run All*). The NLTK stop-word list is downloaded automatically the first time.

## What each section of the notebook does

| Section | What it does | Main functions |
|---|---|---|
| 0. Data loading | Loads the dataset and preprocesses title, description and product details (same as Part 1) | `preprocess_text`, `load_and_preprocess` |
| 1.1 Inverted index | Builds `{term: [pid, ...]}` over title + description + product details | `get_terms`, `create_index` |
| 1.2 AND search | Returns the products that contain all the query terms | `search_and` |
| 1.3 Test queries | The five test queries and their number of results | `test_queries` |
| 1.4 TF-IDF ranking | Ranks the AND results by cosine similarity of TF-IDF vectors | `TF`, `IDF`, `TFxIDF`, `query_vector`, `cosine_similarity`, `search_tfidf`, `show_top` |
| 2.1 Metrics | P@K, R@K, AP@K, F1@K, MAP, MRR, NDCG@K | `precision_at_k`, `recall_at_k`, `avg_precision_at_k`, `f1_at_k`, `map_at_k`, `mrr_at_k`, `ndcg_at_k`, `evaluate_query` |
| 2.2 Validation queries | Applies the metrics to `validation_labels.csv` (query 1 and query 2) | |
| 2.3 Test queries evaluation | Applies the metrics to our labels in `custom_query_labels.csv` | |

## Trying other queries and options

- Search and rank any query (top 10 by default):
  ```python
  show_top("women blue denim jeans", k=10)
  ```
- Only the AND matches, without ranking:
  ```python
  search_and("women blue denim jeans", index)
  ```
- Change the cut-off K of the metrics with the `k` argument, e.g. `evaluate_query(y_true, y_score, k=5)`.

## Relevance labels file

`custom_query_labels.csv` has one row per judged product: `query_id`, `query`, `pid`, `rank` (position in our ranking), `title`, `description`, `product_details`, `score` (cosine similarity) and `labels` (1 = relevant, 0 = not relevant).

## Use of AI

AI assistants (ChatGPT and Claude) were used to explain Python functions, debug the evaluation code and review the report. All the code was reviewed and understood by the group.
