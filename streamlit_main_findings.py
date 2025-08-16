
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Main Findings Dashboard", layout="wide")

st.title("Main Findings Dashboard-China and the Global Rise of CO₂ Emissions")
st.caption("A concise, presentation-ready dashboard showing only the key results from the case study .")

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
default_focus = "China" if "China" in set(co2["country"]) else co2["country"].iloc[0]


# Tabs correspond to key findings sections only
tab8, tab9, tab10 = st.tabs(
    ["Top Emitters", "CO₂ Emissions — China Highlighted", "Per-capita Rankings"]
)

# -----------------------------
# Top Emitters (Absolute CO2)
# -----------------------------
with tab8:
    year_for_rank = st.slider("Select ranking year", min_value=min_year, max_value=max_year, value=min(2014, max_year))
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
    **Key Takeaways:**
    - In early years (1800s–1900s), CO₂ emissions were dominated by Europe, North America, and other high-income regions, while China’s contribution was very small.
    - By the mid-20th century, the U.S. was still a leading emitter, but China began to rise gradually.
    - After the late 20th century and especially post-2000, China’s emissions accelerated sharply, overtaking the U.S. and becoming the largest absolute emitter in the world.
    - This shift highlights China’s rapid industrialization and reliance on coal, making it the central driver of recent global CO₂ growth.
    """)
# -----------------------------
# Trends Over Time
# -----------------------------
with tab9:
    st.subheader("CO₂ Emissions Over Time — China")
    focus_country = st.selectbox("China", sorted(co2["country"].unique()), index=sorted(co2["country"].unique()).index(default_focus) if default_focus in set(co2["country"]) else 0)
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
    **Key Takeaways:**
    - Historical Leaders: From the 18th to mid-20th century, CO₂ emissions were dominated by Europe and North America, with China barely visible.
    - Rapid Growth: Starting in the late 20th century, China’s emissions rose sharply — a steep curve compared to other countries — reflecting fast industrialization and coal dependence.
    - China Overtakes: By the 2000s, China surpassed the U.S. and became the largest global emitter, while U.S. and European emissions stabilized or declined.
    - Global Impact: China’s emissions trajectory is now the main driver of worldwide CO₂ growth, making it central to future climate outcomes.
    """)
# -----------------------------
# Per-capita CO₂ Rankings
# -----------------------------
with tab10:
    st.subheader("Top 10 CO₂ per Capita")
    year_pc = st.slider(
        "Select year for per-capita ranking",
        min_value=min_year, max_value=max_year, value=max_year,
        key="year_pc_slider"
    )

    d_pc = co2[co2["year"] == year_pc].copy()
    # remove aggregates and tiny populations
    if "iso_code" in d_pc.columns:
        d_pc = d_pc[~d_pc["iso_code"].isin(["OWID_WRL","OWID_KOS"])]
    d_pc = d_pc[~d_pc["country"].str.contains("World|International", case=False, na=False)]
    if "population" in d_pc.columns:
        d_pc = d_pc[d_pc["population"] > 1_000_000]

    d_pc = d_pc.dropna(subset=["co2_per_capita"])
    top_pc = d_pc.nlargest(10, "co2_per_capita")[["country", "co2_per_capita"]]

    c1, c2 = st.columns([2,1])
    with c1:
        fig = plt.figure()
        plt.barh(top_pc["country"][::-1], top_pc["co2_per_capita"][::-1])
        plt.xlabel("Tonnes per person")
        plt.ylabel("Country")
        plt.title(f"Top 10 per-capita — {year_pc}")
        st.pyplot(fig, clear_figure=True)
    with c2:
        st.dataframe(
            top_pc.rename(columns={"country":"Country","co2_per_capita":"Tonnes/person"})
                  .style.format({"Tonnes/person":"{:.2f}"}),
            use_container_width=True
        )

    st.markdown("""
**Key Takeaways:**
- China ranks **lower per-capita** than its absolute total due to population size.
- Small, high-income or oil-exporting countries often top per-capita rankings.
- Highlights the **equity** angle: totals vs per-person emissions.
""")


