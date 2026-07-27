## Setup

Create a fresh project:

```bash
mkdir llm-zoomcamp-hw5 && cd llm-zoomcamp-hw5
uv init
uv add gitsource minsearch openai python-dotenv
```

We want everyone to start with the same code, so we prepared a starter package.

Download it:

```bash
PREFIX=https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/cohorts/2026/05-monitoring
wget $PREFIX/rag_helper.py
wget $PREFIX/starter.py
```

We keep things simpler and focus only on RAG. However, all the concepts could be directly translated to agents.

Next, you need to put your OpenAI key in a `.env` file:

```
OPENAI_API_KEY=sk-...
```

Like previously, you can use any alternative you want.

The starter loads the 72 course lessons, builds a text-search index,
and wraps it in a `RAGBase` instance you can call right away:

```python
from starter import rag

query = "How does the agentic loop keep calling the model until it stops?"
answer = rag.rag(query)
print(answer)
```

For the LLM, we recommend OpenAI with `gpt-5.4-mini`, but you can use
any model and provider you want.

## OpenTelemetry setup

First, install the OpenTelemetry libraries:

```bash
uv add opentelemetry-api opentelemetry-sdk
```

- `opentelemetry-api` is the interface - the classes and functions you
import in your code (`trace`, `Tracer`, `Span`)
- `opentelemetry-sdk` is the implementation that actually creates and processes spans.

## OpenTelemetry

Before we start, we need to learn a few concepts from OTel - we will
use them in this homework.

- A trace is the end-to-end story of a single request as it moves
  through your system. For us, it's one RAG call.
- A span is one operation within a trace. A trace is made of one
  or more spans, organized as a tree. Each span has a name, a start
  and end time, and a set of attributes. For us we will have one span
  inside the trace, but for agents one trace will have multiple spans.
- Attributes are key-value pairs attached to a span - anything you
  want to record, like the number of tokens used or the cost of a call.

When a span finishes - meaning the code block it wraps completes - the
SDK hands it to a span processor, which forwards it to an exporter.
The exporter decides where the span goes: to the console, to a file,
to a database, or to a remote collector. We will see all of this in
practice in the questions below.

We start with the `ConsoleSpanExporter`, which prints each finished
span to the terminal so we can see what OTel captures:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("llm-zoomcamp")
```

Here is what each line does:

- `TracerProvider()` creates the SDK's central configuration object.
  It owns the span processors and decides how spans are built.
- `SimpleSpanProcessor(ConsoleSpanExporter())` wires a processor that
  forwards every finished span to the console exporter, one at a time.
  "Simple" means synchronous and immediate - good for development.
- `trace.set_tracer_provider(provider)` registers the provider
  globally, so every call to `trace.get_tracer(...)` returns a tracer
  backed by it.
- `trace.get_tracer("llm-zoomcamp")` returns a `Tracer` we use to
  create spans. The string is just a label for the instrumentation
  scope - it identifies which part of the code produced the spans.

Put this block at the top of your script, before you import or use
`starter` - so the tracer provider is ready before any code that
might create spans.

With the tracer in hand, you can wrap any block of code in a span:

```python
with tracer.start_as_current_span("my_operation") as span:
    # your code here
    span.set_attribute("my_key", "my_value")
```

`start_as_current_span` creates a new span and makes it the "current"
span for the duration of the `with` block. Any code inside the block -
including other calls to `start_as_current_span` - becomes a child of
this span. When the block exits, the span ends automatically.

You will use this pattern to instrument the RAG methods in the
questions below.

## Q1. First trace

Wrap the `rag()` method so each call produces a span. The simplest way
is to create a `RAGTraced` subclass of `RAGBase` that wraps `rag()`,
`search()`, and `llm()` each in their own span.

Run this query:

> How does the agentic loop keep calling the model until it stops?

The console exporter prints every finished span as a dictionary.
Count the spans in the console output - each one is a separate
`ReadableSpan` entry. How many spans does the trace produce? <br>
(1) 1 <br>
(2) 3 <br>
(3) 5 <br>
(4) 7 <br>

--> My Answer: option number 2

## Q2. Capturing metrics as span attributes

Spans are not just timing markers - you can attach any information you
want to them with `set_attribute`. We already use spans to record how
long each step takes. Now we'll add the metrics we care about: tokens
and cost.

Read the token usage from the LLM response (the `llm()` method in the
starter already returns the raw response object) and set them as
attributes on the `llm` span:

```python
span.set_attribute("input_tokens", usage.input_tokens)
span.set_attribute("output_tokens", usage.output_tokens)
```

And since we know both input and output tokens, we can also compute
the cost using the code from the previous modules.

Now re-run the query. How many input tokens do we see? <br>
(1) 700 <br>
(2) 7000 <br>
(3) 70000 <br>
(4) 700000 <br>

--> My Answer: option number 2

> These numbers vary between runs. Pick the closest option.

## Q3. Span timing

Each span automatically records its duration. Look at the console output
from Q1 and find the durations for the `search` span and the `llm` span.

For a typical query, roughly how long does the LLM call take? <br>
(1) Under 100ms <br>
(2) 100-500ms <br>
(3) 500-2000ms <br>
(4) Over 2000ms <br>

--> My Answer: option number 4

> The first call can be slower (cold start). Pick the range you see
> most often.

## Q4. Saving traces to SQLite

Right now the spans are printed to the terminal and then gone. We don't
save them.

We want to persist them so we can query them later.

In this homework, we'll use SQLite - it's a more lightweight option than
Postgres, so we don't need to set up any docker containers in this homework.

Our instrumentation is already done, we don't need to change anything there.
But we need to create a custom exporter. Instead of printing the spans,
it will save them to the database.

OTel calls the exporter through the same span processor we already use,
we just swap the destination.

Now we will create a custom exporter that saves each finished span to a
SQLite database. The exporter extends `SpanExporter`. It has the following methods:

- `export` method that receives a list of `ReadableSpan` objects
- `shutdown` and `force_flush` methods

Let's implement it:

```python
import sqlite3
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class SQLiteSpanExporter(SpanExporter):

    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
        """)
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (
                    span.name,
                    span.start_time,
                    span.end_time,
                    attrs.get("input_tokens"),
                    attrs.get("output_tokens"),
                    attrs.get("cost"),
                ),
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self):
        return True
```

Replace the console exporter with this new exporter:

```python
provider.add_span_processor(
    SimpleSpanProcessor(SQLiteSpanExporter("traces.db"))
)
```

Re-run the query from Q1. Which span names appear in the `spans` table? <br>
(1) Only `rag` <br>
(2) `rag` and `llm` <br>
(3) `rag`, `search`, and `llm` <br>
(4) `search`, `llm`, and `judge` <br>

--> My Answer: option number 3

## Q5. Querying trace data

The traces are now in SQLite. Run one more query through the traced
RAG, then query the database.

The `rag` span wraps everything, so its duration includes both
`search` and `llm`. To see where time actually goes, exclude the
`rag` span and compare the children.

Using SQL (or pandas), compute the total duration for each span name
excluding `rag`. Which span type takes the most total time? <br>
(1) `search` <br>
(2) `llm` <br>
(3) They're all about the same <br>

--> My Answer: option number 2

## Q6. Token stability across runs

Load the SQLite data with pandas. One thing a dashboard can tell you
is how stable your system is. If the same query always produces the
same number of input tokens, the context your RAG retrieves is
consistent. If it varies a lot, something in the search may be
unstable.

Run the same query from Q1 three more times (so you have 4 RAG calls
total in the database). Then compute the input tokens for each `llm`
span.

How much do the input tokens vary across these 4 runs? <br>
(1) They're identical <br>
(2) Within 10% of each other <br>
(3) Within 50% of each other <br>
(4) They vary more than 50% <br>

--> My Answer: option number 2
