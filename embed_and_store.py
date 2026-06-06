import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

CHUNKS_DIR = "chunks"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 100

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]


def get_index():
    existing = [idx["name"] for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating index '{INDEX_NAME}' ...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


def parse_filename(filename):
    # e.g. hamlet_act3_scene1.txt -> ("hamlet", 3, 1)
    name = filename[:-4]
    match = re.match(r"(.+)_act(\d+)_scene(\d+)", name)
    if not match:
        return None
    play, act, scene = match.groups()
    return play, int(act), int(scene)


def embed_batch(texts):
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_and_store():
    index = get_index()

    files = sorted(f for f in os.listdir(CHUNKS_DIR) if f.endswith(".txt"))
    print(f"Found {len(files)} chunks")

    batch = []
    for filename in files:
        parsed = parse_filename(filename)
        if not parsed:
            print(f"  Skipping unparseable filename: {filename}")
            continue
        play, act, scene = parsed

        with open(os.path.join(CHUNKS_DIR, filename), "r", encoding="utf-8") as f:
            text = f.read()

        batch.append({
            "id": filename[:-4],
            "text": text,
            "play": play,
            "act": act,
            "scene": scene,
        })

        if len(batch) >= BATCH_SIZE:
            flush_batch(index, batch)
            batch = []
            time.sleep(0.1)

    if batch:
        flush_batch(index, batch)

    print("Done.")


def to_vector(item, embedding):
    return {
        "id": item["id"],
        "values": embedding,
        "metadata": {
            "play": item["play"],
            "act": item["act"],
            "scene": item["scene"],
            "text": item["text"],
        },
    }


def flush_batch(index, batch):
    embeddings = embed_batch([item["text"] for item in batch])
    vectors = [to_vector(item, emb) for item, emb in zip(batch, embeddings)]
    index.upsert(vectors=vectors)
    print(f"  Upserted {len(vectors)} vectors")


if __name__ == "__main__":
    embed_and_store()
