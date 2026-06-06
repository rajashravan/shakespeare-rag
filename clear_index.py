import os

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]


def clear_index():
    existing = [idx["name"] for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Index '{INDEX_NAME}' does not exist. Nothing to delete.")
        return

    print(f"Deleting index '{INDEX_NAME}' ...")
    pc.delete_index(INDEX_NAME)
    print("Deleted. Re-run embed_and_store.py to recreate it.")


if __name__ == "__main__":
    clear_index()
