import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Company Keyword Extractor", page_icon="🔍", layout="centered")

st.title("🔍 Company Keyword Extractor")
st.markdown("Upload a large Excel file, enter keywords, and download the filtered results.")
st.caption("by Moez")

# ── File upload ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload Excel file (.xlsx or .xls)", type=["xlsx", "xls"])

# ── Session state init ───────────────────────────────────────────────────────
if "group_ids" not in st.session_state:
    st.session_state.group_ids = [0]
    st.session_state.next_id = 1

def add_group():
    new_id = st.session_state.next_id
    st.session_state.next_id += 1
    st.session_state.group_ids.append(new_id)

def remove_group(gid):
    st.session_state.group_ids.remove(gid)

# ── Keywords UI ───────────────────────────────────────────────────────────────
st.markdown("**Keywords**")

for pos, gid in enumerate(st.session_state.group_ids):
    if pos > 0:
        # AND / OR selector centered between groups
        _, c_op, _ = st.columns([2, 2, 2])
        with c_op:
            st.selectbox(
                "operator",
                ["AND", "OR"],
                key=f"op_{gid}",
                label_visibility="collapsed",
            )

        c_in, c_rm = st.columns([8, 1])
        with c_in:
            st.text_input(
                f"group {pos + 1}",
                placeholder="e.g. istanbul, İstanbul",
                key=f"grp_{gid}",
                label_visibility="collapsed",
            )
        with c_rm:
            st.button("✕", key=f"rm_{gid}", on_click=remove_group, args=(gid,))
    else:
        st.text_input(
            "Keywords",
            placeholder="e.g. cement, concrete, çimento",
            key=f"grp_{gid}",
            label_visibility="collapsed",
        )

st.button("＋ Add keyword group", on_click=add_group)

# ── Output filename ──────────────────────────────────────────────────────────
output_name = st.text_input("Output file name", value="filtered_companies.xlsx")
if not output_name.endswith(".xlsx"):
    output_name += ".xlsx"

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_keywords(gid):
    val = st.session_state.get(f"grp_{gid}", "")
    return [k.strip() for k in val.split(",") if k.strip()]

def make_mask(df, keywords):
    pattern = "|".join(keywords)
    return df.apply(
        lambda col: col.astype(str).str.contains(pattern, case=False, na=False, regex=True)
    ).any(axis=1)

has_keywords = any(get_keywords(gid) for gid in st.session_state.group_ids)

# ── Run ──────────────────────────────────────────────────────────────────────
if st.button("Extract", type="primary", disabled=not (uploaded_file and has_keywords)):
    non_empty = [(gid, get_keywords(gid)) for gid in st.session_state.group_ids if get_keywords(gid)]

    with st.spinner("Loading file..."):
        df = pd.read_excel(uploaded_file, dtype=str)

    st.info(f"Loaded **{len(df):,} rows** × {len(df.columns)} columns")

    with st.spinner("Filtering..."):
        mask = make_mask(df, non_empty[0][1])
        for gid, kws in non_empty[1:]:
            op = st.session_state.get(f"op_{gid}", "AND")
            m = make_mask(df, kws)
            mask = (mask & m) if op == "AND" else (mask | m)
        filtered = df[mask].copy()

    if filtered.empty:
        st.warning("No matches found. Try different keywords.")
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
