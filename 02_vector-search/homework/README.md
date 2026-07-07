Now we're ready to do the homework.

## Q1. Embedding a query

Embed the following query:

> How does approximate nearest neighbor search work?

The embedder returns a vector of 384 numbers. What's the first value <br>
(`v[0]`)? <br>
(1) -0.31 <br>
(2) -0.02 <br>
(3) 0.12 <br>
(4) 0.44 <br>

--> My Answer: option number 2

## Loading the data

We pull the lesson pages from the course repository, the same way as in
homework 1. We pin to commit `8c1834d` so everyone works with the same
data.

```python
from gitsource import GithubRepositoryDataReader

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

documents = [file.parse() for file in reader.read()]
```

Each document is a dictionary with a `filename` and `content`, and there
are 72 pages.

## Q2. Cosine similarity

The embedder returns normalized vectors, so the dot product between two
of them is their cosine similarity.

Take the page `02-vector-search/lessons/07-sqlitesearch-vector.md`, embed
its `content`, and compute the cosine similarity with the query vector
from Q1. What do you get? <br>
(1) 0.07 <br>
(2) 0.37 <br>
(3) 0.68 <br>
(4) 0.92 <br>

--> My Answer: option number 2 (0.36)

## Q3. Chunking and search by hand

A full page covers several topics, which waters down its embedding.

We chunk the pages the same way as in homework 1:

```python
from gitsource import chunk_documents
chunks = chunk_documents(documents, size=2000, step=1000)
```

We embed every chunk's `content` with `encode_batch`, stack the vectors
into a matrix `X`, and score the Q1 query against all chunks:

```python
scores = X.dot(v)
```

Which file does the highest-scoring chunk belong to (its `filename`)? <br>
(1) `02-vector-search/lessons/03-embeddings-dataset.md` <br>
(2) `02-vector-search/lessons/06-rag-vector.md` <br>
(3) `02-vector-search/lessons/07-sqlitesearch-vector.md` <br>
(4) `02-vector-search/lessons/09-onnx-embedder.md` <br>

--> My Answer: option number 3

## Q4. Vector search with minsearch

We've done vector search by hand, which is good for learning, but it's not
what we do in practice. In practice we use libraries.

Let's use `VectorSearch` from minsearch and run a search for the following
query:

> What metric do we use to evaluate a search engine?

Which file is the `filename` of the first result? <br>
(1) `02-vector-search/lessons/04-vector-search.md` <br>
(2) `04-evaluation/lessons/05-search-metrics.md` <br>
(3) `04-evaluation/lessons/13-llm-as-judge.md` <br>
(4) `05-monitoring/lessons/04-metrics.md` <br>

--> My Answer: option number 2

## Q5. Text search vs vector search

Vector search matches by meaning, keyword search by exact words.

Let's compare them. Index
the same chunks with `Index` from minsearch. Use `content` as a
text field.

Run both searches for this query:

> How do I store vectors in PostgreSQL?

Take the top 5 results from each method. Which file shows up in the
vector results but not in the text results? <br>
(1) `02-vector-search/lessons/01-intro.md` <br>
(2) `02-vector-search/lessons/02-embeddings.md` <br>
(3) `02-vector-search/lessons/08-pgvector.md` <br>
(4) `03-orchestration/lessons/05-rag.md` <br>

--> My Answer: option number 3

## Q6. Hybrid search

Both vector and text search have their strengths and weaknesses. Vector
search matches by meaning, so it finds relevant pages even when they use
words different from the query. But it can miss exact terms like names,
codes, or rare keywords. Text search is the opposite: it nails exact words
but misses paraphrases and synonyms.

We don't have to pick one or the other - we can use both and merge their
results. This approach is called "hybrid search".

Each search produces its own ranked list, so we need a way to combine them
into one. In this homework we use Reciprocal Rank Fusion (RRF). It ignores
the raw scores from each method, which live on different scales and aren't
directly comparable. Instead, it looks only at the position of each
document in each list.

Every document scores by its position (`rank`, starting at 0) in each
list, and we sum the scores across lists with a constant `k = 60`:

```text
RRF(d) = sum over lists of  1 / (k + rank(d))
```

"Sum over lists" means we go through every ranked list and, for each list
where the document appears, add its `1 / (k + rank)` contribution. A
document found by both searches collects a score from each list, while one
found by only a single search collects just one.

The constant `k` controls how much the exact rank matters. A larger `k`
flattens the gap between positions, so the difference between rank 0 and
rank 5 counts for less. A smaller `k` does the opposite: it sharpens that
gap, so being at the top of a list matters much more.

The value 60 comes from the original RRF paper and is the usual default.
You rarely need to tune it. Lower it when only the top results matter.
Raise it to reward documents that appear across many lists, even when they
never quite reach the top.

A document that ranks well in both lists ends up higher than one that's
only strong in a single list.

```python
def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc

    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]
```

Now run the query `"How do I give the model access to tools?"`
with vector and text search and fuse the results with `rrf`:

```python
results = rrf([vector_results, text_results])
```

Which file is ranked first after RRF? <br>
(1) `01-agentic-rag/lessons/01-intro.md` <br>
(2) `01-agentic-rag/lessons/13-function-calling.md` <br>
(3) `01-agentic-rag/lessons/14-agentic-loop.md` <br>
(4) `01-agentic-rag/lessons/16-other-frameworks.md` <br>

--> My Answer: option number 2

Notice that this file isn't first in either search on its own - it wins
because it ranks high in both.
