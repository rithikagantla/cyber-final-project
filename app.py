"""HHS Health Data Breaches: Vulnerable Information Locations (2020 to Nov 10, 2026).

Team: Rithika Gantla, Joudi Elansary, Misha Shariff, Beauty Babatunde, Jennifer Tran
Data: HHS OCR Breach Portal (current + archived records), filtered on Breach Submission Date.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="HHS Breach Locations", layout="wide")

DATA = Path(__file__).parent / "breaches_2020_2026.csv"
LOC_COL = "Location of Breached Information"


@st.cache_data
def load():
    df = pd.read_csv(DATA, parse_dates=["Breach Submission Date"])
    df["Year"] = df["Breach Submission Date"].dt.year
    df["Locations"] = df[LOC_COL].str.split(r",\s*")
    df["Location Group"] = df["Locations"].apply(lambda x: x[0] if len(x) == 1 else "Multiple locations")
    return df


df = load()

st.title("Which information locations drive the largest health data breaches?")
st.caption(
    "HHS OCR Breach Portal, breaches affecting 500+ individuals, submitted Jan 1, 2020 to Nov 10, 2026. "
    "Team: Rithika Gantla, Joudi Elansary, Misha Shariff, Beauty Babatunde, Jennifer Tran."
)

# ---------- Interactive feature 1: dropdown filters ----------
ALL = "All"
c1, c2, c3 = st.columns(3)
state = c1.selectbox("State", [ALL] + sorted(df["State"].dropna().unique()))
year = c2.selectbox("Year", [ALL] + sorted(df["Year"].unique(), reverse=True))
btype = c3.selectbox("Breach type", [ALL] + sorted(df["Type of Breach"].unique()))

f = df
if state != ALL:
    f = f[f["State"] == state]
if year != ALL:
    f = f[f["Year"] == year]
if btype != ALL:
    f = f[f["Type of Breach"] == btype]

if f.empty:
    st.warning("No breaches match these filters.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Breaches", f"{len(f):,}")
k2.metric("Individuals affected", f"{f['Individuals Affected'].sum():,.0f}")
k3.metric("Median breach size", f"{f['Individuals Affected'].median():,.0f}")

# One row per (breach, location) for location-level charts
loc = f.explode("Locations").rename(columns={"Locations": "Location"})

# ---------- Visualization 1: bar chart ----------
st.subheader("1. Individuals affected by information location")
m1, m2 = st.columns([3, 1])
metric = m1.radio("Measure", ["Individuals affected", "Number of breaches"], horizontal=True)
log_bar = m2.checkbox("Log scale", help="Network servers dwarf the rest; log scale shows smaller locations.")
if metric == "Individuals affected":
    bar = loc.groupby(["Location", "Type of Breach"], as_index=False)["Individuals Affected"].sum()
    y = "Individuals Affected"
else:
    bar = loc.groupby(["Location", "Type of Breach"], as_index=False).size().rename(columns={"size": "Breaches"})
    y = "Breaches"
order = bar.groupby("Location")[y].sum().sort_values(ascending=False).index.tolist()
fig1 = px.bar(
    bar, x="Location", y=y, color="Type of Breach",
    category_orders={"Location": order},
    hover_data={y: ":,"},  # Interactive feature 2: hover tooltips
)
fig1.update_layout(xaxis_title=None, legend_title="Breach type", height=450)
if log_bar:
    fig1.update_yaxes(type="log")
st.plotly_chart(fig1, width="stretch")
st.caption("A breach listing several locations counts once under each location.")

# ---------- Visualization 2: pie chart ----------
left, right = st.columns([1, 1.4])
with left:
    st.subheader("2. Share of breaches by location")
    pie = loc["Location"].value_counts().reset_index()
    pie.columns = ["Location", "Breaches"]
    fig2 = px.pie(pie, names="Location", values="Breaches", hole=0.35)
    fig2.update_traces(textposition="inside", textinfo="percent",
                       hovertemplate="%{label}<br>%{value:,} breaches<br>%{percent}<extra></extra>")
    fig2.update_layout(height=450, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig2, width="stretch")

# ---------- Visualization 3: scatter plot ----------
with right:
    st.subheader("3. Every breach: date vs. size")
    fig3 = px.scatter(
        f, x="Breach Submission Date", y="Individuals Affected", color="Location Group",
        log_y=True, opacity=0.65,
        hover_name="Name of Covered Entity",
        hover_data={"State": True, "Type of Breach": True, LOC_COL: True,
                    "Individuals Affected": ":,", "Location Group": False},
    )
    fig3.update_layout(height=450, legend_title="Location", yaxis_title="Individuals affected (log scale)")
    st.plotly_chart(fig3, width="stretch")

with st.expander("Largest breaches in current selection"):
    st.dataframe(
        f.nlargest(15, "Individuals Affected")[
            ["Name of Covered Entity", "State", "Covered Entity Type", "Individuals Affected",
             "Breach Submission Date", "Type of Breach", LOC_COL, "Business Associate Present"]
        ],
        hide_index=True, width="stretch",
    )
