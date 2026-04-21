from pathlib import Path

import pandas as pd
import streamlit as st

from clean_automation import (
    clean_dataframe,
    add_duplicate_counts,
    enrich_dataframe,
    assemble_output,
)

st.set_page_config(page_title="Vocabulary → AnkiDroid", layout="centered")
st.title("Vocabulary → AnkiDroid")
st.caption("Transforms ReadEra exports into AnkiDroid-compatible decks.")

# ── Upload ─────────────────────────────────────────────────────────────────────

uploaded = st.file_uploader("Upload ReadEra export", type=["txt", "csv"])

if not uploaded:
    st.stop()

# ── Settings ───────────────────────────────────────────────────────────────────

stem = Path(uploaded.name).stem
suggested = stem.split(" -- ")[0].strip()
if "Citas del libro " in suggested:
    suggested = suggested[suggested.index("Citas del libro ") + len("Citas del libro "):]

col1, col2 = st.columns(2)
book_name   = col1.text_input("Book name", value=suggested)
output_name = col2.text_input("Output filename", value=suggested)

# ── Process ────────────────────────────────────────────────────────────────────

if not st.button("Process", type="primary"):
    st.stop()

try:
    df = pd.read_csv(uploaded, delimiter="|")
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

df = clean_dataframe(df)
df = add_duplicate_counts(df)
total = len(df)

secs = round(total * 0.54)
eta = f"~{secs}s" if secs < 60 else f"~{secs // 60}m {secs % 60}s"
st.info(f"{total} words will be processed (estimated time: {eta})")

t_bar = st.progress(0, text="Translating... 0%")
d_bar = st.progress(0, text="Fetching definitions... 0%")

df = enrich_dataframe(
    df,
    on_translation_progress=lambda pct: t_bar.progress(pct / 100, text=f"Translating... {pct}%"),
    on_definition_progress=lambda pct: d_bar.progress(pct / 100, text=f"Fetching definitions... {pct}%"),
)

df = assemble_output(df, book_name)

# ── Download ───────────────────────────────────────────────────────────────────

st.success(f"Done! {len(df)} words processed.")
st.download_button(
    label="Download CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"{output_name}.csv",
    mime="text/csv",
)
