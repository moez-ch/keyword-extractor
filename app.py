import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Company Keyword Extractor", page_icon="🔍", layout="centered")

st.title("🔍 Company Keyword Extractor")
st.markdown("Upload a large Excel file, filter by keywords and state, download the results.")
st.caption("by Moez")

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload Excel file (.xlsx or .xls)", type=["xlsx", "xls"])

# ── Filters ───────────────────────────────────────────────────────────────────
col_kw, col_st = st.columns(2)

with col_kw:
    st.markdown("**Keywords**")
    keywords_raw = st.text_input(
        "Keywords",
        placeholder="e.g. cement, concrete, çimento",
        label_visibility="collapsed",
    )

with col_st:
    st.markdown("**Search in column**")
    if uploaded_file:
        preview = pd.read_excel(uploaded_file, nrows=0, dtype=str)
        uploaded_file.seek(0)
        col_options = ["— All columns —"] + list(preview.columns)
    else:
        col_options = ["— All columns —"]
    selected_col = st.selectbox("Column", col_options, label_visibility="collapsed")

# ── Output filename ───────────────────────────────────────────────────────────
output_name = st.text_input("Output file name", value="filtered_companies.xlsx")
if not output_name.endswith(".xlsx"):
    output_name += ".xlsx"

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse(raw):
    return [k.strip() for k in raw.split(",") if k.strip()]

def make_mask(df, terms):
    pattern = "|".join(terms)
    return df.apply(
        lambda col: col.astype(str).str.contains(pattern, case=False, na=False, regex=True)
    ).any(axis=1)

keywords = parse(keywords_raw)
can_run  = uploaded_file and keywords

# ── Run ───────────────────────────────────────────────────────────────────────
if st.button("Extract", type="primary", disabled=not can_run):
    with st.spinner("Loading file..."):
        df = pd.read_excel(uploaded_file, dtype=str)

    st.info(f"Loaded **{len(df):,} rows** × {len(df.columns)} columns")

    with st.spinner("Filtering..."):
        if selected_col and selected_col != "— All columns —":
            mask = df[selected_col].astype(str).str.contains(
                "|".join(keywords), case=False, na=False, regex=True
            )
        else:
            mask = make_mask(df, keywords)
        filtered = df[mask].copy()

    if filtered.empty:
        st.warning("No matches found. Try different keywords or state.")
    else:
        st.success(f"Found **{len(filtered):,} matching rows**")
        st.dataframe(filtered.head(50), use_container_width=True)
        if len(filtered) > 50:
            st.caption(f"Showing first 50 of {len(filtered):,} rows. Full data is in the downloaded file.")

        buffer = io.BytesIO()
        filtered.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download Results",
            data=buffer,
            file_name=output_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
