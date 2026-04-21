import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from deep_translator import GoogleTranslator


# ── Input prompts ──────────────────────────────────────────────────────────────

_INPUT_DIR = Path(__file__).parent / "input"
_OUTPUT_DIR = Path(__file__).parent / "output"


def get_user_inputs():
    """Prompt the user for all required paths and the output filename."""
    input_path = _prompt_input_path()
    output_path = _prompt_output_path()
    file_name = _prompt_filename()
    return input_path, output_path, file_name


def _prompt_input_path():
    """List files in ./input and let the user pick by number or type a path."""
    files = sorted(_INPUT_DIR.iterdir()) if _INPUT_DIR.exists() else []
    if files:
        print("Available input files:")
        for i, f in enumerate(files, start=1):
            print(f"  {i}. {f.name}")
    while True:
        raw = input("Input file (number or full path): ").strip()
        if not raw:
            print("  Cannot be empty. Please try again.")
            continue
        if raw.isdigit() and 1 <= int(raw) <= len(files):
            return str(files[int(raw) - 1])
        return raw


def _prompt_output_path():
    raw = input(f'Output directory (Enter for "{_OUTPUT_DIR}"): ').strip()
    return raw if raw else str(_OUTPUT_DIR)



def _prompt_filename(default="final"):
    raw = input(f"Output filename (default: {default}): ").strip()
    return raw if raw else default


def _prompt_book_name(input_path):
    """Suggest a book name extracted from the filename; let the user override it."""
    stem = Path(input_path).stem
    suggested = stem.split(" -- ")[0].strip()
    prefix = "Citas del libro "
    if prefix in suggested:
        suggested = suggested[suggested.index(prefix) + len(prefix):]
    raw = input(f'Book name (Enter to keep "{suggested}"): ').strip()
    return raw if raw else suggested


# ── Load ───────────────────────────────────────────────────────────────────────

def load_dataframe(input_path):
    """Load the pipe-delimited CSV and validate it has at least one column.

    Handles Windows MAX_PATH (260 chars) automatically using the long-path prefix.
    """
    raw = str(Path(input_path).resolve())
    # Windows MAX_PATH workaround: paths over 260 chars need the \\?\ prefix
    if sys.platform == "win32" and len(raw) > 259 and not raw.startswith("\\\\?\\"):
        open_path = "\\\\?\\" + raw
    else:
        open_path = raw

    if not Path(open_path.lstrip("\\\\?\\") if open_path.startswith("\\\\?\\") else open_path).exists():
        # For long paths, Path.exists() itself fails — try opening directly
        try:
            open(open_path).close()
        except FileNotFoundError:
            sys.exit(f"Error: file not found — {input_path}")
        except Exception:
            pass

    try:
        df = pd.read_csv(open_path, delimiter="|")
    except Exception as e:
        sys.exit(f"Error reading CSV: {e}")
    if df.empty or df.shape[1] == 0:
        sys.exit("Error: CSV appears to be empty or could not be parsed.")
    return df


# ── Clean ──────────────────────────────────────────────────────────────────────

def clean_dataframe(df):
    """Remove noise rows, rename the target column, and clean its text."""
    # Drop ReadEra footer rows and noise markers
    df = df.iloc[:-3]
    first_col = df.columns[0]
    df = df[df[first_col] != "*****"]
    df = df[df[first_col] != "--"]
    df = df.rename(columns={first_col: "to_define"})
    df["to_define"] = _clean_text(df["to_define"])
    # Drop rows that became empty after cleaning
    df = df[df["to_define"].str.strip() != ""].reset_index(drop=True)
    return df


def _clean_text(series):
    """Consolidate all string-cleaning operations into one pass."""
    series = series.str.replace(r"-+", " ", regex=True)         # hyphen → space
    series = series.str.replace(r"'s\b", "", regex=True)        # drop possessive 's
    series = series.str.strip('.,!?"\u201c\u201d\u2026()\'\u2018\u2019 ')
    return series.str.strip()


# ── Duplicate annotation ───────────────────────────────────────────────────────

def add_duplicate_counts(df):
    """
    Mark duplicated words with their occurrence count: "word (3)".
    Keeps one copy of each duplicate after annotating.
    """
    dup_counts = (
        df[df.duplicated("to_define", keep=False)]
        .groupby("to_define")
        .size()
        .to_dict()
    )
    df["word"] = df["to_define"].apply(
        lambda w: f"{w} ({dup_counts[w]})" if w in dup_counts else w
    )
    df = df.drop_duplicates(subset="to_define").reset_index(drop=True)
    return df


# ── Enrichment ─────────────────────────────────────────────────────────────────

_TRANSLATION_WORKERS = 15
_DEFINITION_WORKERS = 5


def enrich_dataframe(df, on_translation_progress=None, on_definition_progress=None):
    """Add 'translation' and 'meaning' columns with percentage milestone output.

    on_translation_progress / on_definition_progress: optional callable(pct: int)
    called at each 10% milestone. When None, milestones are printed to stdout (CLI).
    """
    words = df["to_define"].tolist()
    total = len(words)
    milestones = {int(total * p / 10) for p in range(1, 11)}

    secs = round(total * 0.54)
    eta = f"~{secs}s" if secs < 60 else f"~{secs // 60}m {secs % 60}s"
    print(f"{total} words will be processed (estimated time: {eta})")

    # ── Translation: concurrent requests ──────────────────────────────────────
    print("Translating...")
    translations = _run_concurrent(
        words, _translate_one, milestones, total, _TRANSLATION_WORKERS,
        on_progress=on_translation_progress,
    )
    print("  Translation done.")
    df["translation"] = translations

    # ── Definitions: concurrent requests ──────────────────────────────────────
    print("Fetching definitions...")
    meanings = _run_concurrent(
        words, _get_definition, milestones, total, _DEFINITION_WORKERS,
        on_progress=on_definition_progress,
    )
    print("  Definitions done.")
    df["meaning"] = meanings

    return df


def _run_concurrent(words, fn, milestones, total, max_workers, on_progress=None):
    """Run fn(word) concurrently for all words, reporting % milestones.

    on_progress: optional callable(pct: int). When None, prints to stdout.
    """
    results = [None] * len(words)
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn, w): i for i, w in enumerate(words)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
            completed += 1
            if completed in milestones:
                pct = round(completed / total * 100)
                if on_progress:
                    on_progress(pct)
                else:
                    print(f"  {pct}%", flush=True)
    return results


def _translate_one(word):
    try:
        result = GoogleTranslator(source="en", target="es").translate(word)
        return result if result else "[translation error]"
    except Exception:
        return "[translation error]"


def _get_definition(word, retries=4, backoff=1.0):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
        except requests.exceptions.RequestException:
            return "No definition found."

        if response.status_code == 200:
            break
        if response.status_code == 429:
            time.sleep(backoff * (2 ** attempt))  # 1s, 2s, 4s, 8s
            continue
        return "No definition found."  # 404 or other — genuine miss
    else:
        return "No definition found."  # exhausted retries

    try:
        data = response.json()
    except ValueError:
        return "No definition found."

    if not isinstance(data, list) or not data:
        return "No definition found."

    meanings = []
    for item in data:
        for meaning_obj in item.get("meanings", []):
            pos = meaning_obj.get("partOfSpeech", "N/A")
            defs = [
                d["definition"]
                for d in meaning_obj.get("definitions", [])
                if "definition" in d
            ]
            if defs:
                meanings.append({pos: defs})

    return _format_definition(meanings) if meanings else "No definition found."


def _format_definition(meanings):
    lines = []
    for meaning_set in meanings:
        for pos, defs in meaning_set.items():
            lines.append(f"  {pos}:")
            for i, def_text in enumerate(defs, start=1):
                lines.append(f"    {i}. {def_text}")
    return "\n".join(lines)


# ── Assemble & export ──────────────────────────────────────────────────────────

def assemble_output(df, book_name):
    """Build the final two-column dataframe: word | definition."""
    df["definition"] = (
        "ES: " + df["translation"].astype(str)
        + "\n"
        + "EN: " + df["meaning"].astype(str)
        + "\n"
        + f"SOURCE: {book_name}"
    )
    return df[["word", "definition"]]


def export_dataframe(df, output_path, file_name):
    out = Path(output_path) / f"{file_name}.csv"
    try:
        df.to_csv(out, index=False)
    except Exception as e:
        sys.exit(f"Error saving file: {e}")
    print(f"\nDone. Saved to {out}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    input_path, output_path, file_name = get_user_inputs()

    df = load_dataframe(input_path)
    df = clean_dataframe(df)
    df = add_duplicate_counts(df)
    book_name = _prompt_book_name(input_path)
    df = enrich_dataframe(df)
    df = assemble_output(df, book_name)

    export_dataframe(df, output_path, file_name)


if __name__ == "__main__":
    main()
