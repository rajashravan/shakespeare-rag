---
name: rebuild-index
description: Rebuild the Shakespeare RAG pipeline — download plays, chunk by
  scene, embed, and upsert into Pinecone. Use when plays, chunking logic, the
  embedding model, or the index need to be (re)built or refreshed from scratch.
---

# Rebuild the Shakespeare RAG index

This project is a linear ingest pipeline:

```
download_plays.py → chunk_plays.py → embed_and_store.py → (query.py)
```

All scripts run with the project venv: `venv/bin/python <script>`.
They require a `.env` file (see `.env.example`) with `OPENAI_API_KEY`,
`PINECONE_API_KEY`, and `PINECONE_INDEX_NAME`.

## Key idempotency facts (these decide which steps to run)

- `download_plays.py` **skips any play already in `plays/`.**
- `chunk_plays.py` **skips any play that already has chunks in `chunks/`.**
  → Changing chunking logic does NOT regenerate chunks unless you delete
    the stale `chunks/` first.
- `clear_index.py` **deletes the entire Pinecone index** (not individual vectors).
- `embed_and_store.py` **recreates the index if missing** (dim=1536, cosine,
  serverless aws/us-east-1) and waits for it to be ready — no separate poll needed.

Because the vectors' dimension is fixed at 1536 (`text-embedding-3-small`),
switching embedding models means the old index is incompatible → it must be
cleared and recreated.

## Choose the scenario, then run those steps

### A. First-time build (empty repo)
```bash
venv/bin/python download_plays.py     # -> plays/   (37 plays)
venv/bin/python chunk_plays.py        # -> chunks/  (~746 chunks)
venv/bin/python embed_and_store.py    # creates index, embeds, upserts
```

### B. Chunking logic changed (re-chunk + re-embed)
The skip-if-exists guards mean you must clear both stale outputs first:
```bash
rm -rf chunks/*                       # force chunker to regenerate
venv/bin/python clear_index.py        # drop stale vectors
venv/bin/python chunk_plays.py        # re-chunk from plays/
venv/bin/python embed_and_store.py    # recreate index + re-embed
```
(No need to re-download — `plays/` is unchanged.)

### C. Embedding model changed
Edit `EMBED_MODEL` / `EMBED_DIM` in `embed_and_store.py` (and `EMBED_MODEL`
in `query.py` to match), then:
```bash
venv/bin/python clear_index.py        # old dim is incompatible
venv/bin/python embed_and_store.py    # recreate index at new dim + re-embed
```

### D. Just re-embed existing chunks (e.g. stale/partial upsert)
```bash
venv/bin/python clear_index.py
venv/bin/python embed_and_store.py
```

## Verify the rebuild

- Chunk count should be ~746: `ls chunks | wc -l`
- Sanity-check retrieval end-to-end:
  ```bash
  echo "What is Macbeth's state of mind before he kills Duncan?" | venv/bin/python query.py
  ```
  A grounded answer that cites Act II material means the index is populated.

## Notes / gotchas

- The downloader sleeps 1s between plays (polite to Gutenberg); a full download
  takes ~40s.
- Only the two longest scenes in the canon exceed the 8192-token embedding
  limit; the chunker auto-sub-splits them into `..._partN.txt` files.
- If `clear_index.py` prints "does not exist", that's fine — nothing to delete.
