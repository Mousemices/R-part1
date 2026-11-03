# Part 2 – Indexing and Evaluation

This folder contains our solution for Part 2 of the IRWA Final Project.

| File | Content |
|---|---|
| `02_indexing_evaluation.ipynb` | Code: inverted index, AND search, TF-IDF ranking and evaluation metrics |
| `custom_query_labels.csv` | Our relevance judgements (0/1) for the five test queries |
| `IRWA-2026-u214405-u255290-part-2.pdf` | Report (also uploaded to Aula Global) |

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
| 2.2 Validation queries | Evaluates the search engine based on two test queries by our metrics, based on `validation_labels.csv` | `validate_query` |
| 2.3 Test queries evaluation | Evaluates five test queries using manually assigned relevance labels stored `custom_query_labels.csv` | `evaluate_manual_labels` |
| 2.4 Diagnostics | Evidence for the analysis: validation top-10 with labels, relevant products lost by the AND search, near-duplicates, noisy vocabulary, matched fields, query formulation | `labelled_top_k`, `judged_ranking`, `missed_relevant`, `duplicates_in_top_k`, `term_fields_in_top_k`, `gender_leak`, `near_misses` |

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

`custom_query_labels.csv` has one row per judged product: `query_id`, `query`, `pid`, `rank` (position in our ranking), `title`, `description`, `product_details`, `score` (cosine similarity) and `labels` (manually assigned labels: 1 = relevant, 0 = not relevant).

## How the evaluation works

We first evaluate the search engine using the provided `validation_labels.csv`, then perform our own evaluation with five test queries. For each query, we retrieve up to 20 products using AND search and TF-IDF ranking, manually assign relevance labels (1 = relevant, 0 = not relevant), and store them in `custom_query_labels.csv`. We then calculate P@10 (accuracy of the top results), R@10 (coverage of known relevant products), F1@10 (balance between precision and recall), AP@10 and MAP@10 (ranking quality), RR@10 and MRR@10 (position of the first relevant result), and NDCG@10 (ranking quality with higher importance given to top positions).

All five queries achieved P@10, AP@10, RR@10, and NDCG@10 of 1.0, while R@10 ranged from 0.500 to 0.526. These results indicate high precision, but recall is limited to our manually judged pool rather than the entire dataset. The main limitations of the current system are strict AND matching, which may exclude relevant products, TF-IDF ranking without field-specific weights, and limited handling of synonyms and structured product attributes. Possible improvements include OR-based retrieval, BM25 or field-weighted ranking, query expansion, and separate indexes for attributes such as color, gender, and material.

## Use of AI

AI assistants (ChatGPT and Claude) were used to explain Python functions, debug the evaluation code and review the report. All the code was reviewed and understood by the group.