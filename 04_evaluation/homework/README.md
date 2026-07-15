## Q1. Generating questions
Generating questions for all 72 pages costs money and takes time, so let's
start small and generate questions for just the first 3 pages:

- `01-agentic-rag/lessons/01-intro.md`
- `01-agentic-rag/lessons/02-environment.md`
- `01-agentic-rag/lessons/03-rag.md`

Each call returns the token usage, which most LLM APIs report on the response
object (e.g. `response.usage.input_tokens` / `prompt_tokens`).

What's the average number of input tokens across these 3 calls? <br>
(1) 140 <br>
(2) 1400 <br>
(3) 14000 <br>
(4) 140000 <br>

--> My Answer: option number 2

> These numbers vary between runs, even with the same model, so pick the closest
> option. A different provider or model may land further apart, but the input
> tokens stay in the same order of magnitude - the prompt we send is the same.

## The full ground truth

You don't need to generate the data for the rest of the homework. We already
did it for all 72 pages, using the same approach as in the lessons, and saved
the 360 questions to a file.

Download it:

```bash
PREFIX=https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main
wget ${PREFIX}/cohorts/2026/04-evaluation/ground-truth.csv
```

Load it with pandas into a list of records called `ground_truth`. Each record
has a `question` and the `filename` of the page that should answer it.

## Searching the chunks

We search over the same chunks as in homework 2.

Create them with `chunk_documents`:

```python
from gitsource import chunk_documents

chunks = chunk_documents(documents, size=2000, step=1000)
```

This gives 295 chunks.

Now rebuild the search from homework 2 over these chunks. Build a text index
(`Index`) and a vector index (`VectorSearch`), both keyed on `filename`. Wrap
each one in a function, `text_search` and `vector_search`, that takes a query
and the number of results to return (5 by default).

For hybrid search, reuse the `rrf` function from homework 2:

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

Then define `hybrid_search` on top of it:

```python
def hybrid_search(query, k=60):
    text_results = text_search(query, num_results=10)
    vector_results = vector_search(query, num_results=10)
    return rrf([text_results, vector_results], k=k)
```

## Q2. First result with text search
Take the first question from the ground truth:

```python
q = ground_truth[0]["question"]
```

After running `text_search` for it, what's the `filename` of the first result? <br>
(1) `01-agentic-rag/lessons/01-intro.md` <br>
(2) `01-agentic-rag/lessons/03-rag.md` <br>
(3) `01-agentic-rag/lessons/13-function-calling.md` <br>
(4) `01-agentic-rag/lessons/10-rag-next-steps.md` <br>

--> My Answer: option number 2

## Q3. First result with vector search
After running `vector_search` for the same question, what's the `filename` of the first result? <br>
(1) `01-agentic-rag/lessons/01-intro.md` <br>
(2) `01-agentic-rag/lessons/03-rag.md` <br>
(3) `04-evaluation/lessons/11-evaluation-intro.md` <br>
(4) `04-evaluation/lessons/12-rag-answers.md` <br>

--> My Answer: option number 1

This question was generated from `01-agentic-rag/lessons/01-intro.md`. Notice
that one method finds the right page at the top and the other doesn't. That's
exactly why we measure across the whole dataset instead of trusting one query.

## Evaluation metrics
We evaluate search exactly as in the module, reusing the same functions from the
lecture. We change only the label. Our ground truth uses `filename`, so a result
counts as a hit when a returned chunk's `filename` matches the question's
`filename`, not a document `id`.

As a reminder, these functions do the following:

- `compute_relevance` runs search for a question and returns a list of 0s and 1s
- `hit_rate` is the fraction of questions where the correct page appears in the results
- `mrr` (Mean Reciprocal Rank) also rewards finding the page near the top
- `evaluate` runs a search function over the whole ground truth and returns both metrics

## Q4. Evaluating text search
Evaluate `text_search` on the ground truth data.
What's the Hit Rate? <br>
(1) 0.55 <br>
(2) 0.66 <br>
(3) 0.76 <br>
(4) 0.88 <br>

--> My Answer: option number 3

## Q5. Evaluating vector search
Now evaluate `vector_search` - the part we left for the homework, since the
module only evaluated keyword search.

What's the MRR? <br>
(1) 0.35 <br>
(2) 0.45 <br>
(3) 0.55 <br>
(4) 0.65 <br>

--> My Answer: option number 3

## Q6. Tuning hybrid search
The `k` constant in RRF controls how much the top ranks matter. A smaller `k`
sharpens the gap between positions, so being at the top of a list counts for
more. The RRF paper uses 60 as a default, but the best value depends on the data
- so let's measure it.

Evaluate `hybrid_search` over the full ground truth dataset for `k` values 1,
50, 100, and 200. Compare the MRR values for these runs.

Which `k` gives the best MRR? <br>
(1) 1 <br>
(2) 50 <br>
(3) 100 <br>
(4) 200 <br>

--> My Answer: option number 1

> Several values of `k` may give the same MRR. If there's a tie, pick the
> smallest `k`.