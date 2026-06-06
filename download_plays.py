import os
import time
import requests

# Gutenberg "1500 series" IDs — the canonical individual-play set produced by
# the PG Shakespeare Team. Each play has a unique, verified ID.
# Source: https://www.gutenberg.org/help/shakespeare.html
PLAYS = [
    ("a_midsummer_nights_dream", 1514),
    ("alls_well_that_ends_well", 1529),
    ("antony_and_cleopatra", 1534),
    ("as_you_like_it", 1523),
    ("the_comedy_of_errors", 1504),
    ("coriolanus", 1535),
    ("cymbeline", 1538),
    ("hamlet", 1524),
    ("henry_iv_part_1", 1516),
    ("henry_iv_part_2", 1518),
    ("henry_v", 1521),
    ("henry_vi_part_1", 1500),
    ("henry_vi_part_2", 1501),
    ("henry_vi_part_3", 1502),
    ("henry_viii", 1541),
    ("julius_caesar", 1522),
    ("king_john", 1511),
    ("king_lear", 1532),
    ("loves_labours_lost", 1510),
    ("macbeth", 1533),
    ("measure_for_measure", 1530),
    ("the_merchant_of_venice", 1515),
    ("the_merry_wives_of_windsor", 1517),
    ("much_ado_about_nothing", 1519),
    ("othello", 1531),
    ("pericles", 1537),
    ("richard_ii", 1512),
    ("richard_iii", 1503),
    ("romeo_and_juliet", 1513),
    ("the_taming_of_the_shrew", 1508),
    ("the_tempest", 1540),
    ("timon_of_athens", 1536),
    ("titus_andronicus", 1507),
    ("troilus_and_cressida", 1528),
    ("twelfth_night", 1526),
    ("the_two_gentlemen_of_verona", 1509),
    ("the_winters_tale", 1539),
]

OUTPUT_DIR = "plays"
BASE_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"


def download_plays():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for play_name, gutenberg_id in PLAYS:
        out_path = os.path.join(OUTPUT_DIR, f"{play_name}.txt")

        if os.path.exists(out_path):
            print(f"Skipping {play_name} (already exists)")
            continue

        url = BASE_URL.format(id=gutenberg_id)
        print(f"Downloading {play_name} from {url} ...")

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"  Saved to {out_path}")
        except requests.RequestException as e:
            print(f"  ERROR downloading {play_name}: {e}")

        time.sleep(1)


if __name__ == "__main__":
    download_plays()
