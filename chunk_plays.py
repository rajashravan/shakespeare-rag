import os
import re

import tiktoken

PLAYS_DIR = "plays"
CHUNKS_DIR = "chunks"

# cl100k_base is the tokenizer used by text-embedding-3-small/large.
ENCODER = tiktoken.get_encoding("cl100k_base")
# Embedding model hard limit is 8192 tokens; leave headroom for the header
# we prepend to every (sub-)chunk plus a safety margin.
TOKEN_BUDGET = 8000


def count_tokens(text):
    return len(ENCODER.encode(text))

GUTENBERG_START = "*** START OF THE PROJECT GUTENBERG EBOOK"
GUTENBERG_END = "*** END OF THE PROJECT GUTENBERG EBOOK"

SCENE_PATTERN = re.compile(
    r'^(ACT\s+[IVX]+|SCENE\s+[IVX]+\.)',
    re.MULTILINE | re.IGNORECASE
)


def strip_boilerplate(text):
    start = text.find(GUTENBERG_START)
    end = text.find(GUTENBERG_END)
    if start == -1 or end == -1:
        return text
    start = text.index('\n', start) + 1
    return text[start:end].strip()


def roman_to_int(s):
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    s = s.upper()
    total = 0
    for i, ch in enumerate(s):
        val = values.get(ch, 0)
        next_val = values.get(s[i + 1], 0) if i + 1 < len(s) else 0
        total += -val if val < next_val else val
    return total


def chunk_play(text, play_name):
    text = strip_boilerplate(text)
    parts = SCENE_PATTERN.split(text)

    chunks = []
    current_act = None
    current_act_header = None
    current_scene = None
    current_header = None
    current_body_parts = []

    def flush_chunk():
        if current_header and current_body_parts:
            body = ''.join(current_body_parts).strip()
            if body:
                prefix = (current_act_header + '\n' + current_header) if current_act_header and not current_header.upper().startswith('ACT') else current_header
                chunks.append((current_act, current_scene, prefix, body))

    i = 0
    while i < len(parts):
        part = parts[i]
        header_match = SCENE_PATTERN.match(part.strip()) if part.strip() else None

        if header_match:
            token = part.strip().upper()
            if token.startswith('ACT'):
                flush_chunk()
                current_act = roman_to_int(token.split()[1])
                current_act_header = part.strip()
                current_scene = None
                current_header = part.strip()
                current_body_parts = []
            elif token.startswith('SCENE'):
                flush_chunk()
                scene_num_str = re.split(r'[\s\.]+', token)[1]
                current_scene = roman_to_int(scene_num_str)
                current_header = part.strip()
                current_body_parts = []
        else:
            current_body_parts.append(part)

        i += 1

    flush_chunk()
    return chunks


def split_into_parts(prefix, body, budget=TOKEN_BUDGET):
    """Greedily pack paragraphs into parts so each (prefix + part) fits in budget.

    Returns a list of full content strings, each beginning with the header
    prefix. Most scenes fit and yield a single part; over-long scenes yield
    several.
    """
    full = prefix + '\n' + body
    if count_tokens(full) <= budget:
        return [full]

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()]
    prefix_tokens = count_tokens(prefix + '\n')

    parts = []
    current = []
    current_tokens = prefix_tokens
    for para in paragraphs:
        para_tokens = count_tokens(para + '\n\n')
        if current and current_tokens + para_tokens > budget:
            parts.append('\n\n'.join(current))
            current = []
            current_tokens = prefix_tokens
        current.append(para)
        current_tokens += para_tokens
    if current:
        parts.append('\n\n'.join(current))

    return [prefix + '\n' + p for p in parts]


def chunk_plays():
    os.makedirs(CHUNKS_DIR, exist_ok=True)

    for filename in os.listdir(PLAYS_DIR):
        if not filename.endswith('.txt'):
            continue

        play_name = filename[:-4]
        existing = [f for f in os.listdir(CHUNKS_DIR) if f.startswith(play_name + '_act')]
        if existing:
            print(f"Skipping {play_name} (chunks already exist)")
            continue

        play_path = os.path.join(PLAYS_DIR, filename)
        with open(play_path, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks = chunk_play(text, play_name)

        written = 0
        for act, scene, prefix, body in chunks:
            if act is None or scene is None:
                continue
            parts = split_into_parts(prefix, body)
            for idx, content in enumerate(parts):
                if len(parts) == 1:
                    out_name = f"{play_name}_act{act}_scene{scene}.txt"
                else:
                    out_name = f"{play_name}_act{act}_scene{scene}_part{idx + 1}.txt"
                out_path = os.path.join(CHUNKS_DIR, out_name)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                written += 1
            if len(parts) > 1:
                print(f"  {play_name} act{act} scene{scene}: split into {len(parts)} parts")

        print(f"{play_name}: {written} chunks written")


if __name__ == "__main__":
    chunk_plays()
