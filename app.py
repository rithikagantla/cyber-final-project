"""Healthcare Cyber Risk Dashboard: Vulnerable Information Locations

Research question (Team 3): Which locations of breached information, such as email,
network servers, laptops, or paper records, are associated with the largest reported breaches?

Team: Rithika Gantla, Joudi Elansary, Misha Shariff, Beauty Babatunde, Jennifer Tran
Data: HHS OCR Breach Portal, current + archived records as of Nov 10, 2026, restricted to
Breach Submission Dates from Jan 1, 2020 through Nov 10, 2026 (Breaches_2020_2026 tab of
hhs_breaches.xlsx, saved here as breaches_2020_2026.csv).
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vulnerable Information Locations", page_icon="🔒", layout="wide")

DATA = Path(__file__).parent / "breaches_2020_2026.csv"
LOC_COL = "Location of Breached Information"
IND = "Individuals Affected"

# Fixed colors so a location looks the same in every chart
LOC_COLORS = {
    "Network Server": "#1F4E79",
    "Email": "#E07A2F",
    "Electronic Medical Record": "#2A9D8F",
    "Paper/Films": "#8E5EA2",
    "Desktop Computer": "#C44E52",
    "Laptop": "#E9C46A",
    "Other Portable Electronic Device": "#6C8EBF",
    "Other": "#9AA0A6",
    "Multiple locations": "#4D4D4D",
}
TYPE_COLORS = {
    "Hacking/IT Incident": "#1F4E79",
    "Unauthorized Access/Disclosure": "#E07A2F",
    "Theft": "#C44E52",
    "Loss": "#8E5EA2",
    "Improper Disposal": "#2A9D8F",
}


@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["Breach Submission Date"])
    df["Year"] = df["Breach Submission Date"].dt.year
    df["Locations"] = df[LOC_COL].str.split(r",\s*").apply(lambda xs: [x.strip() for x in xs])
    df["Location Group"] = df["Locations"].apply(lambda x: x[0] if len(x) == 1 else "Multiple locations")
    return df


def explode_locations(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per (breach, location). A breach listing 2 locations counts under each."""
    return frame.explode("Locations").rename(columns={"Locations": "Location"})


def fmt(n: float) -> str:
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:,.0f}"


df = load()
ALL_LOCS = sorted({l for ls in df["Locations"] for l in ls})
ALL_TYPES = sorted(df["Type of Breach"].unique())

# ======================= SIDEBAR: INTERACTIVE FILTERS =======================
st.sidebar.header("Filters")
st.sidebar.caption("Every chart, metric and table updates when you change these.")

y_min, y_max = int(df["Year"].min()), int(df["Year"].max())
years = st.sidebar.slider("Submission year range", y_min, y_max, (y_min, y_max))

states = st.sidebar.multiselect("State(s)", sorted(df["State"].dropna().unique()), placeholder="All states")
types = st.sidebar.multiselect("Breach type(s)", ALL_TYPES, placeholder="All breach types")
locs = st.sidebar.multiselect("Information location(s)", ALL_LOCS, placeholder="All locations")
min_size = st.sidebar.select_slider(
    "Minimum breach size (individuals affected)",
    options=[500, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000],
    value=500,
    format_func=lambda v: f"{v:,}",
    help="HHS only posts breaches of 500+ individuals. Raise this to focus on large breaches.",
)

f = df[df["Year"].between(*years) & (df[IND] >= min_size)]
if states:
    f = f[f["State"].isin(states)]
if types:
    f = f[f["Type of Breach"].isin(types)]
if locs:
    f = f[f["Locations"].apply(lambda ls: any(l in locs for l in ls))]

st.sidebar.divider()
st.sidebar.caption(
    "Source: HHS OCR Breach Portal (current + archived), breaches submitted "
    "Jan 1, 2020 to Nov 10, 2026. Team: Rithika Gantla, Joudi Elansary, Misha Shariff, "
    "Beauty Babatunde, Jennifer Tran."
)

# ======================= HEADER =======================
st.title("Vulnerable Information Locations in Healthcare Breaches")
st.markdown(
    "**Research question:** Which locations of breached information, such as email, network servers, "
    "laptops, or paper records, are associated with the largest reported breaches?"
)

if f.empty:
    st.warning("No breaches match these filters. Widen the year range or clear a filter.")
    st.stop()

loc = explode_locations(f)
if locs:
    loc = loc[loc["Location"].isin(locs)]

top_loc = loc.groupby("Location")[IND].sum().idxmax()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Breaches", f"{len(f):,}")
k2.metric("Individuals affected", fmt(f[IND].sum()))
k3.metric("Median breach size", f"{f[IND].median():,.0f}")
k4.markdown(f"<div style='font-size:0.875rem'>Top location by individuals</div>"
                f"<div style='font-size:1.6rem;line-height:1.3;padding-top:0.3rem'>{top_loc}</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Impact by location", "🔥 Location × breach type", "⚖️ Compare locations", "📋 Breach records", "🧭 Findings & actions"]
)

# ======================= TAB 1: CORE VISUALIZATIONS =======================
with tab1:
    # ---- Visualization 1: bar chart ----
    st.subheader("Which locations account for the most affected individuals?")
    c1, c2 = st.columns([3, 1])
    measure = c1.radio(
        "Measure", ["Individuals affected", "Number of breaches", "Median breach size"], horizontal=True
    )
    log_y = c2.checkbox("Log scale", help="Network servers dwarf every other location; log scale shows the rest.")

    if measure == "Median breach size":
        bar = loc.groupby("Location", as_index=False)[IND].median().rename(columns={IND: "Median individuals"})
        ycol, color, cmap = "Median individuals", "Location", LOC_COLORS
    elif measure == "Number of breaches":
        bar = loc.groupby(["Location", "Type of Breach"], as_index=False).size().rename(columns={"size": "Breaches"})
        ycol, color, cmap = "Breaches", "Type of Breach", TYPE_COLORS
    else:
        bar = loc.groupby(["Location", "Type of Breach"], as_index=False)[IND].sum()
        ycol, color, cmap = IND, "Type of Breach", TYPE_COLORS
    order = bar.groupby("Location")[ycol].sum().sort_values(ascending=False).index.tolist()
    fig1 = px.bar(
        bar, x="Location", y=ycol, color=color, color_discrete_map=cmap,
        category_orders={"Location": order}, hover_data={ycol: ":,"},
    )
    fig1.update_layout(xaxis_title=None, legend_title=None, height=460, showlegend=color != "Location",
                       legend=dict(orientation="h", y=1.08))
    if log_y:
        fig1.update_yaxes(type="log")
    st.plotly_chart(fig1, width="stretch")
    st.caption("Breaches that list several locations count once under each location they list.")

    left, right = st.columns([1, 1.4])
    # ---- Visualization 2: pie chart ----
    with left:
        st.subheader("How often is each location breached?")
        pie = loc["Location"].value_counts().reset_index()
        pie.columns = ["Location", "Breaches"]
        fig2 = px.pie(pie, names="Location", values="Breaches", hole=0.4,
                      color="Location", color_discrete_map=LOC_COLORS)
        fig2.update_traces(textposition="inside", textinfo="percent",
                           hovertemplate="%{label}<br>%{value:,} breaches<br>%{percent}<extra></extra>")
        fig2.update_layout(height=470, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig2, width="stretch")

    # ---- Visualization 3: scatter plot ----
    with right:
        st.subheader("Where do the largest individual breaches sit?")
        fig3 = px.scatter(
            f, x="Breach Submission Date", y=IND, color="Location Group",
            color_discrete_map=LOC_COLORS, log_y=True, opacity=0.6,
            hover_name="Name of Covered Entity",
            hover_data={"State": True, "Type of Breach": True, LOC_COL: True, IND: ":,", "Location Group": False},
        )
        fig3.update_traces(marker=dict(size=7))
        fig3.update_layout(height=470, legend_title=None, yaxis_title="Individuals affected (log scale)",
                           xaxis_title=None, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig3, width="stretch")

# ======================= TAB 2: HEATMAP + TREND =======================
with tab2:
    # ---- Visualization 4: heatmap of location × breach type ----
    st.subheader("Location × breach type")
    hm_measure = st.radio(
        "Cell value", ["Individuals affected", "Number of breaches", "Median breach size"],
        horizontal=True, key="hm",
    )
    agg = {"Individuals affected": "sum", "Number of breaches": "size", "Median breach size": "median"}[hm_measure]
    grid = loc.pivot_table(index="Location", columns="Type of Breach", values=IND, aggfunc=agg, fill_value=0)
    grid = grid.loc[grid.sum(axis=1).sort_values(ascending=False).index]
    fig4 = px.imshow(
        grid, color_continuous_scale="Blues", aspect="auto",
        labels=dict(color=hm_measure, x="Breach type", y="Information location"),
    )
    cell_text = grid.map(lambda v: "" if v == 0 else (f"{v:,.0f}" if hm_measure == "Number of breaches" else fmt(v)))
    fig4.update_traces(text=cell_text.values, texttemplate="%{text}",
                       hovertemplate="%{y}<br>%{x}<br>%{z:,.0f}<extra></extra>")
    fig4.update_layout(height=470)
    st.plotly_chart(fig4, width="stretch")
    st.caption("Darker cells mark the location and breach-type combinations behind the most harm.")

    # ---- Visualization 5: trend by location ----
    st.subheader("How has each location trended over time?")
    tr_measure = st.radio("Measure", ["Number of breaches", "Individuals affected"], horizontal=True, key="tr")
    if tr_measure == "Number of breaches":
        tr = loc.groupby(["Year", "Location"], as_index=False).size().rename(columns={"size": "Value"})
    else:
        tr = loc.groupby(["Year", "Location"], as_index=False)[IND].sum().rename(columns={IND: "Value"})
    fig5 = px.line(tr, x="Year", y="Value", color="Location", markers=True, color_discrete_map=LOC_COLORS)
    fig5.update_layout(height=420, yaxis_title=tr_measure, legend_title=None, xaxis=dict(dtick=1))
    st.plotly_chart(fig5, width="stretch")
    if years[1] == 2026:
        st.caption("2026 runs only through Nov 10, so its totals are partial.")

# ======================= TAB 3: COMPARISON TOOL =======================
with tab3:
    st.subheader("Compare two information locations side by side")
    a_col, b_col = st.columns(2)
    avail = loc["Location"].value_counts().index.tolist()
    loc_a = a_col.selectbox("Location A", avail, index=0)
    loc_b = b_col.selectbox("Location B", avail, index=min(1, len(avail) - 1))

    def summary(name: str) -> dict:
        s = loc[loc["Location"] == name]
        return {
            "Breaches": len(s),
            "Individuals affected": s[IND].sum(),
            "Median breach size": s[IND].median(),
            "Largest breach": s[IND].max(),
            "Breaches of 1M+": int((s[IND] >= 1_000_000).sum()),
            "% hacking/IT": (s["Type of Breach"] == "Hacking/IT Incident").mean(),
            "% with business associate": (s["Business Associate Present"] == "Yes").mean(),
        }

    sa, sb = summary(loc_a), summary(loc_b)
    for col, name, s in ((a_col, loc_a, sa), (b_col, loc_b, sb)):
        m1, m2, m3 = col.columns(3)
        m1.metric("Breaches", f"{s['Breaches']:,}")
        m2.metric("Individuals", fmt(s["Individuals affected"]))
        m3.metric("Median size", f"{s['Median breach size']:,.0f}")

    table = pd.DataFrame({loc_a: sa, loc_b: sb})
    shown = table.copy().astype(object)
    for r in shown.index:
        if r.startswith("%"):
            shown.loc[r] = [f"{v:.0%}" for v in table.loc[r]]
        else:
            shown.loc[r] = [f"{v:,.0f}" for v in table.loc[r]]
    st.dataframe(shown, width="stretch")

    mix = loc[loc["Location"].isin([loc_a, loc_b])]
    mix = mix.groupby(["Location", "Type of Breach"], as_index=False).size()
    mix["Share"] = mix["size"] / mix.groupby("Location")["size"].transform("sum")
    fig6 = px.bar(mix, x="Share", y="Location", color="Type of Breach", orientation="h",
                  color_discrete_map=TYPE_COLORS, hover_data={"size": ":,", "Share": ":.0%"},
                  category_orders={"Location": [loc_a, loc_b]})
    fig6.update_layout(height=260, xaxis_tickformat=".0%", xaxis_title="Share of breaches by type",
                       yaxis_title=None, legend_title=None, legend=dict(orientation="h", y=-0.4))
    st.plotly_chart(fig6, width="stretch")

    box = loc[loc["Location"].isin([loc_a, loc_b])]
    fig7 = px.box(box, x="Location", y=IND, color="Location", color_discrete_map=LOC_COLORS, log_y=True,
                  points="outliers", hover_name="Name of Covered Entity",
                  category_orders={"Location": [loc_a, loc_b]})
    fig7.update_layout(height=420, showlegend=False, xaxis_title=None,
                       yaxis_title="Individuals affected per breach (log scale)")
    st.plotly_chart(fig7, width="stretch")

# ======================= TAB 4: SORTABLE TABLE + DOWNLOAD =======================
with tab4:
    st.subheader("Breach records in the current selection")
    q = st.text_input("Search covered entity name", placeholder="e.g., Change Healthcare")
    rec = f.copy()
    if q:
        rec = rec[rec["Name of Covered Entity"].str.contains(q, case=False, na=False)]
    cols = ["Name of Covered Entity", "State", "Covered Entity Type", IND, "Breach Submission Date",
            "Type of Breach", LOC_COL, "Business Associate Present"]
    rec = rec[cols].sort_values(IND, ascending=False)
    st.caption(f"{len(rec):,} records. Click any column header to sort.")
    st.dataframe(
        rec, hide_index=True, width="stretch", height=480,
        column_config={
            IND: st.column_config.NumberColumn(format="localized"),
            "Breach Submission Date": st.column_config.DateColumn(format="MMM D, YYYY"),
        },
    )
    st.download_button(
        "⬇️ Download these records as CSV",
        rec.to_csv(index=False).encode("utf-8"),
        file_name="hhs_breaches_filtered.csv",
        mime="text/csv",
    )

# ======================= TAB 5: FINDINGS (computed from the full dataset) =======================
with tab5:
    full = explode_locations(df)
    tot = df[IND].sum()
    ns = df["Locations"].apply(lambda ls: "Network Server" in ls)
    em = df["Locations"].apply(lambda ls: "Email" in ls)
    hack = df["Type of Breach"] == "Hacking/IT Incident"
    ba = df["Business Associate Present"] == "Yes"
    top10 = df.nlargest(10, IND)
    hack_by_year = df.groupby("Year")["Type of Breach"].apply(lambda s: (s == "Hacking/IT Incident").mean())

    st.caption("Calculated from all 5,016 breaches (2020 to Nov 10, 2026). These numbers ignore the sidebar filters.")
    st.subheader("Risk interpretation: three findings")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.metric("Network servers' share of individuals affected", f"{df.loc[ns, IND].sum() / tot:.0%}")
        st.caption(f"Network servers appear in {ns.mean():.0%} of breaches.")
        st.markdown(
            f"**1. Network servers drive the scale of harm.** Median server breach: "
            f"{full.loc[full['Location'] == 'Network Server', IND].median():,.0f} people vs. "
            f"{full.loc[full['Location'] == 'Email', IND].median():,.0f} for email. Email is frequent "
            f"({em.mean():.0%} of breaches) but small ({df.loc[em, IND].sum() / tot:.0%} of individuals)."
        )
    with f2:
        st.metric("Hacking/IT share of breaches", f"{hack_by_year.iloc[0]:.0%} → {hack_by_year.iloc[-1]:.0%}")
        st.caption(f"From {hack_by_year.index[0]} to {hack_by_year.index[-1]}.")
        st.markdown(
            f"**2. Hacking is how server data gets out.** Hacking/IT incidents are {hack.mean():.0%} of breaches "
            f"and {df.loc[hack, IND].sum() / tot:.0%} of individuals affected, and their share keeps rising."
        )
    with f3:
        st.metric("Largest 10 breaches involving a business associate",
                  f"{(top10['Business Associate Present'] == 'Yes').sum()} of 10")
        st.caption("Ranked by individuals affected.")
        st.markdown(
            f"**3. Vendors concentrate the risk.** A business associate is involved in {ba.mean():.0%} of breaches "
            f"but {df.loc[ba, IND].sum() / tot:.0%} of individuals affected. Nearly all of the largest are "
            "network-server hacks."
        )

    st.subheader("Risk treatment: three recommended controls")
    st.markdown(
        """
| Control | What it involves | Finding it addresses |
|---|---|---|
| **Harden network servers** | Patch and scan for vulnerabilities, segment networks, encrypt data at rest, require MFA for remote access | 1: servers hold most exposed records |
| **Detect and recover from intrusions** | Endpoint detection with 24/7 monitoring, offline backups, a tested incident response plan, phishing training (email is the 2nd most common location) | 2: hacking is the dominant and growing threat |
| **Manage vendor (business associate) risk** | Security terms in business associate agreements, yearly assessments (SOC 2 or HITRUST), share only the data vendors need | 3: vendor breaches reach the most people |
"""
    )

    st.subheader("Limitations: what this dataset cannot establish")
    st.markdown(
        """
- **Breaches under 500 people** are not posted on the portal, so small breaches (often paper or laptops) are missing.
- **The point of entry:** many breaches list several locations, so we cannot tell which one an attacker used first.
- **Root cause, cost or prevention:** no data on attack method, losses or controls in place, so we cannot prove a control would have stopped a breach.
- **Risk per record held:** we do not know how much data each location stores, so a large total is not a higher breach rate.
- **Final, exact counts:** entities self-report estimates that can change, and current records are still under investigation.
- **Timing and outliers:** we filter on submission date, not breach date; 2026 is partial; Change Healthcare alone (192.7M) is about 22% of all individuals affected. Individuals affected counts records, so one person can be counted more than once.
"""
    )
