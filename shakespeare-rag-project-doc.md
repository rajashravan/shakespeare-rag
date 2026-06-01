# Shakespeare Oracle — Project Doc
### A RAG-powered app that answers questions about Shakespeare plays

---

## Goal

Build a command-line app that answers non-trivial questions about Shakespeare plays using a RAG pipeline.

Example queries:
- "What are the themes of Hamlet?"
- "What is the mental state of Macbeth right before he kills Duncan?"
- "How does Juliet's relationship with her father evolve throughout the play?"

---

## Tech Stack

| Role | Tool |
|---|---|
| Data source | Project Gutenberg (free, plain text) |
| Chunking | Python regex on ACT/SCENE markers |
| Embedding model | `text-embedding-3-small` (OpenAI) |
| Vector DB | Pinecone (free tier) |
| LLM | `gpt-4o-mini` (OpenAI) |
| Language | Python 3 |

---

## Project Structure

```
shakespeare-rag/
│
├── plays/                  # Raw .txt files downloaded from Gutenberg (one per play)
├── chunks/                 # Chunked scenes as .txt files (one per scene)
│
├── download_plays.py       # Script 1: Downloads all 37 plays from Gutenberg
├── chunk_plays.py          # Script 2: Chunks each play by ACT/SCENE into chunks/
├── embed_and_store.py      # Script 3: Embeds chunks and upserts into Pinecone
├── query.py                # Script 4: Runtime query interface for the user
│
├── requirements.txt        # Python dependencies
└── .env                    # API keys (never commit this)
```

---

## Environment Variables (.env)

```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=shakespeare
```

---

## Script 1: `download_plays.py`

**Goal:** Download all 37 Shakespeare plays from Project Gutenberg and save as plain `.txt` files in the `plays/` folder.

**Details:**
- Use the `requests` library to fetch each play by its Gutenberg URL
- Save each file as `plays/{play_name}.txt` (snake_case, e.g. `hamlet.txt`)
- Gutenberg plain text URLs follow this pattern: `https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt`
- Hardcode a list of `(play_name, gutenberg_id)` tuples for all 37 plays
- Print progress as each play downloads
- Skip download if file already exists (idempotent)

---

## Script 2: `chunk_plays.py`

**Goal:** Split each play into scene-level chunks and save as individual `.txt` files in `chunks/`.

**Details:**
- For each `.txt` file in `plays/`, parse out individual scenes using regex
- A scene boundary is marked by lines matching patterns like:
  - `ACT I`, `ACT II`, etc.
  - `SCENE 1`, `SCENE I`, `Scene 1.`, etc.
- Each chunk should include the ACT and SCENE header as part of its text for context
- Save each chunk as `chunks/{play_name}_act{N}_scene{N}.txt`
- Strip Gutenberg boilerplate (license text at top and bottom of file) before chunking
  - Gutenberg content starts after `*** START OF THE PROJECT GUTENBERG EBOOK`
  - Gutenberg content ends before `*** END OF THE PROJECT GUTENBERG EBOOK`
- Print number of chunks extracted per play
- Skip if chunks already exist for a play (idempotent)

---

## Script 3: `embed_and_store.py`

**Goal:** Read all chunks, embed them using OpenAI, and upsert into Pinecone.

**Details:**
- Initialize Pinecone client and connect to index named `shakespeare`
  - Index dimension: `1536` (matches `text-embedding-3-small` output)
  - Metric: `cosine`
  - Create the index if it doesn't exist
- For each `.txt` file in `chunks/`:
  - Read the chunk text
  - Embed using `text-embedding-3-small` via OpenAI API
  - Upsert into Pinecone with:
    - `id`: the chunk filename (e.g. `hamlet_act3_scene1`)
    - `values`: the embedding vector
    - `metadata`:
      - `play`: play name (e.g. `hamlet`)
      - `act`: act number (e.g. `3`)
      - `scene`: scene number (e.g. `1`)
      - `text`: full chunk text (needed for retrieval at query time)
- Upsert in batches of 100 to avoid rate limits
- Print progress as chunks are embedded and stored

---

## Script 4: `query.py`

**Goal:** Accept a user's natural language question, retrieve relevant scenes, and return a synthesized answer.

**Details:**

**Step 1 — Get user query**
- Accept input via `input()` in a simple loop so users can ask multiple questions

**Step 2 — Embed the query**
- Use `text-embedding-3-small` to embed the user's query string

**Step 3 — Retrieve from Pinecone**
- Query Pinecone for the top 3 most similar vectors
- Extract the `text` field from each result's metadata — this is the raw scene text

**Step 4 — Build the prompt**
- Construct a prompt in this format:

```
You are a Shakespeare expert. Answer the user's question in a thoughtful, 
engaging way using the provided scenes as context. If the scenes don't 
contain enough information, say so honestly.

Relevant scenes:
---
{scene_1_text}
---
{scene_2_text}
---
{scene_3_text}
---

User question: {user_query}
```

**Step 5 — Call the LLM**
- Send the prompt to `gpt-4o-mini` via OpenAI chat completions API
- Print the response

**Step 6 — Loop**
- Ask the user if they want to ask another question
- Exit cleanly on `quit` or `exit`

---

## Requirements.txt

```
openai
pinecone
python-dotenv
requests
```

---

## Running Order

```bash
pip install -r requirements.txt

python download_plays.py       # ~2 mins
python chunk_plays.py          # ~10 seconds
python embed_and_store.py      # ~5 mins (API calls)
python query.py                # runtime — ask away
```

---

## Notes for Claude Code

- All scripts should load API keys from `.env` using `python-dotenv`
- All scripts should be idempotent — safe to re-run without duplicating data
- Use `time.sleep(0.1)` between OpenAI embedding calls to avoid rate limit errors
- Pinecone free tier supports 1 index with up to 100k vectors — 37 plays × ~30 scenes = ~1,100 vectors, well within limits
- The `text` metadata field on each Pinecone vector is how we retrieve the original scene at query time — this is critical
