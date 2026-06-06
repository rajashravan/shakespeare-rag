import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
TOP_K = 3

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX_NAME"])

SYSTEM_PROMPT = (
    "You are a Shakespeare expert. Answer the user's question in a thoughtful, "
    "engaging way using the provided scenes as context. If the scenes don't "
    "contain enough information, say so honestly."
)


def embed_query(text):
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=[text])
    return response.data[0].embedding


def retrieve(vector, k=TOP_K):
    result = index.query(vector=vector, top_k=k, include_metadata=True)
    return [match["metadata"]["text"] for match in result["matches"]]


def build_messages(query, scenes):
    scene_block = "\n---\n".join(scenes)
    user_content = (
        f"Relevant scenes:\n---\n{scene_block}\n---\n\n" # prompt engineering!
        f"User question: {query}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def generate(messages):
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def answer_question(query):
    vector = embed_query(query)
    scenes = retrieve(vector)
    messages = build_messages(query, scenes)
    return generate(messages)


def main():
    print("Shakespeare Oracle. Ask a question (or 'quit' / 'exit' to leave).\n")
    while True:
        query = input("> ").strip()
        if query.lower() in ("quit", "exit"):
            print("Farewell.")
            break
        if not query:
            continue
        answer = answer_question(query)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
