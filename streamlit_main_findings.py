
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Main Findings Dashboard", layout="wide")

st.title("Main Findings Dashboard")
st.caption("A concise, presentation-ready dashboard showing only the key results from the case study (Sections 8–10).")

# -----------------------------
# Data (default: OWID CO₂)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_default():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    return pd.read_csv(url)

use_default = st.toggle("Use default OWID dataset", value=True, help="Turn off to upload your own CSV.")
file = None if use_default else st.file_uploader("Upload CSV with columns at least: country, year, co2, co2_per_capita, population (optional)", type=["csv"])

if use_default:
    try:
        co2 = load_default()
    except Exception as e:
        st.error(f"Could not load default dataset: {e}")
        st.stop()
else:
    if file is None:
        st.info("Upload a CSV to continue.")
        st.stop()
    co2 = pd.read_csv(file)

# basic clean
for col in ["country","year","co2","co2_per_capita"]:
    if col not in co2.columns:
        st.error(f"Missing required column: {col}")
        st.stop()
co2 = co2.dropna(subset=["country","year"]).copy()
co2["year"] = co2["year"].astype(int)

# filters (limited to keep it 'findings-only')
min_year, max_year = int(co2["year"].min()), int(co2["year"].max())
default_focus = "United States" if "United States" in set(co2["country"]) else co2["country"].iloc[0]
year_for_rank = st.slider("Select ranking year (used in Sections 8 & 9 visualizations)", min_value=min_year, max_value=max_year, value=min(2014, max_year))

# Tabs correspond to key findings sections only
tab8, tab9, tab10 = st.tabs(["Section 8: Top Emitters", "Section 9: Trends (Highlight)", "Section 10: Per-capita Rankings"])

# -----------------------------
# Section 8 — Top Emitters (Absolute CO2)
# -----------------------------
with tab8:
    st.subheader(f"Top 10 CO₂ Emitters — {year_for_rank}")
    d = co2[co2["year"] == year_for_rank].copy()
    d = d[~d["country"].str.contains("World|International", case=False, na=False)]
    if "iso_code" in d.columns:
        d = d[~d["iso_code"].isin(["OWID_WRL","OWID_KOS"])]
    d = d.dropna(subset=["co2"])
    top = d.nlargest(10, "co2")[["country","co2"]]

    col1, col2 = st.columns([2,1])
    with col1:
        fig = plt.figure()
        plt.barh(top["country"][::-1], top["co2"][::-1])
        plt.xlabel("CO₂ (million tonnes)")
        plt.ylabel("Country")
        plt.title(f"Top 10 Emitters — {year_for_rank}")
        st.pyplot(fig, clear_figure=True)
    with col2:
        st.metric("World CO₂ (Mt)", value=f"{d['co2'].sum():,.0f}")
        st.metric("Median CO₂ (Mt)", value=f"{d['co2'].median():,.0f}")
        st.dataframe(top.rename(columns={"country":"Country","co2":"CO₂ (Mt)"}).style.format({"CO₂ (Mt)":"{:.0f}"}), use_container_width=True)

    st.markdown("""
    **Section 8 — Key Takeaways (edit this text):**
    - Emissions are concentrated among a small set of countries.
    - Rankings by absolute CO₂ differ from per‑capita rankings (see Section 10).
    - Note any notable outliers or changes vs. previous years.
    """)

# -----------------------------
# Section 9 — Trends Over Time (Highlight a country)
# -----------------------------
with tab9:
    st.subheader("CO₂ Emissions Over Time — Highlighted Country")
    focus_country = st.selectbox("Highlighted country", sorted(co2["country"].unique()), index=sorted(co2["country"].unique()).index(default_focus) if default_focus in set(co2["country"]) else 0)
    # choose comparison set: top 7 emitters in the selected ranking year
    pool = co2[co2["year"] == year_for_rank].nlargest(8, "co2")["country"].tolist()
    comps = [c for c in pool if c != focus_country][:5]
    st.caption(f"Comparing {focus_country} to: {', '.join(comps) if comps else '—'}")
    yr_min, yr_max = st.slider("Show years", min_value=min_year, max_value=max_year, value=(max(min_year, 1950), max_year))

    dd = co2[(co2["year"] >= yr_min) & (co2["year"] <= yr_max)].copy()
    subset = dd[dd["country"].isin([focus_country] + comps)]
    fig = plt.figure()
    for c in subset["country"].unique():
        s = subset[subset["country"] == c].sort_values("year")
        if c == focus_country:
            plt.plot(s["year"], s["co2"], linewidth=3)
        else:
            plt.plot(s["year"], s["co2"], linewidth=1)
    plt.xlabel("Year")
    plt.ylabel("CO₂ (million tonnes)")
    plt.title(f"CO₂ over Time — Highlight: {focus_country}")
    st.pyplot(fig, clear_figure=True)

    st.markdown("""
    **Section 9 — Key Takeaways (edit this text):**
    - Describe long‑run trend (e.g., steady increase/decrease, structural break).
    - Compare the highlighted country vs. peers: earlier peak? faster growth?
    - Note policy or economic events that align with inflection points.
    """)

# -----------------------------
# Section 10 — Per‑capita Rankings
# -----------------------------
with tab10:
    st.subheader(f"Top 10 by CO₂ per Capita — {year_for_rank}")
    d2 = co2[co2["year"] == year_for_rank].copy()
    if "population" in d2.columns:
        d2 = d2[d2["population"] > 1e6]  # avoid micro‑states dominating
    d2 = d2.dropna(subset=["co2_per_capita"])
    top_pc = d2.nlargest(10, "co2_per_capita")[["country","co2_per_capita"]]
    col1, col2 = st.columns([2,1])
    with col1:
        fig = plt.figure()
        plt.barh(top_pc["country"][::-1], top_pc["co2_per_capita"][::-1])
        plt.xlabel("Tonnes per person")
        plt.ylabel("Country")
        plt.title(f"Top 10 — Per Capita CO₂ — {year_for_rank}")
        st.pyplot(fig, clear_figure=True)
    with col2:
        st.dataframe(top_pc.rename(columns={"country":"Country","co2_per_capita":"Tonnes per person"}).style.format({"Tonnes per person":"{:.2f}"}), use_container_width=True)

    st.markdown("""
    **Section 10 — Key Takeaways (edit this text):**
    - Per‑capita leaders often differ from absolute emitters.
    - Highlights equity considerations for policy design.
    - Mention where your focus country ranks per‑capita vs. absolute.
    """)

st.divider()
st.markdown("""
**Notes for submission**  
- This dashboard only includes the main findings (Sections 8–10).  
- The full methodology, wrangling, and additional figures remain in the `.ipynb`.  
- Remember to include this app's public URL and the GitHub link to this `.py` in your bCourses submission.
""")
