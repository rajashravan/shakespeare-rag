# Shakespeare Oracle 🎭

_Designed by me. Written with Claude's help._

A command-line RAG (Retrieval-Augmented Generation) app that answers non-trivial
questions about Shakespeare's plays — grounded in the actual text, not the
model's fuzzy memory of it.

```
> What is the mental state of Macbeth right before he kills Duncan?

Right before Macbeth kills Duncan (Act II, Scene I), he is in a state of intense
psychological turmoil — famously hallucinating a dagger ("a fatal vision") that
leads him toward the deed...
```

## How it works

The app retrieves the most relevant scenes for your question and feeds them to an
LLM as context, so answers quote the real text instead of paraphrasing from memory.

```
download → chunk → embed → store → retrieve → generate
```

1. **Download** all 37 plays from Project Gutenberg as plain text.
2. **Chunk** each play into scene-level pieces (split on `ACT`/`SCENE` markers).
3. **Embed** each chunk into a vector with OpenAI `text-embedding-3-small`.
4. **Store** the vectors (plus the scene text) in a Pinecone index.
5. At query time: **embed** the question, **retrieve** the top-3 most similar
   scenes, and **generate** an answer with `gpt-4o-mini`.

## Tech stack

| Role            | Tool                              |
|-----------------|-----------------------------------|
| Data source     | Project Gutenberg                 |
| Embedding model | `text-embedding-3-small` (OpenAI) |
| Vector DB       | Pinecone (free tier)              |
| LLM             | `gpt-4o-mini` (OpenAI)            |

## Setup

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=shakespeare
```

## Usage

Run the pipeline in order:

```bash
venv/bin/python download_plays.py     # downloads 37 plays  -> plays/
venv/bin/python chunk_plays.py        # chunks by scene     -> chunks/
venv/bin/python embed_and_store.py    # embeds + upserts to Pinecone
venv/bin/python query.py              # ask questions, interactively
```

Each script is idempotent — safe to re-run. The downloader and chunker skip work
that's already done; `embed_and_store.py` creates the Pinecone index if needed.

If you change the chunking logic, clear the stale vectors first:

```bash
venv/bin/python clear_index.py        # deletes the Pinecone index
```

## Scripts

| File                  | What it does                                          |
|-----------------------|-------------------------------------------------------|
| `download_plays.py`   | Fetches the 37 plays from Project Gutenberg           |
| `chunk_plays.py`      | Splits each play into scene chunks                    |
| `embed_and_store.py`  | Embeds chunks and upserts them into Pinecone          |
| `query.py`            | Interactive query loop (retrieve + generate)          |
| `clear_index.py`      | Deletes the Pinecone index (for a clean re-ingest)    |

## Notes

- 37 plays produce ~746 scene chunks — well within Pinecone's free tier.
- Scenes longer than the embedding model's 8192-token limit (only the two
  longest scenes in the canon) are automatically sub-split.
- Pipeline produces grounded answers: it quotes real lines rather than
  hallucinating them.
