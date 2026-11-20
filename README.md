# Vulnerable Information Locations in Healthcare Breaches

**Team 3:** Rithika Gantla, Joudi Elansary, Misha Shariff, Beauty Babatunde, Jennifer Tran

**Research question:** Which locations of breached information, such as email, network servers, laptops, or paper records, are associated with the largest reported breaches?

**Data:** HHS OCR Breach Portal, current + archived records as of Nov 10, 2026, restricted to Breach Submission Dates from Jan 1, 2020 through Nov 10, 2026 (5,016 breaches). `breaches_2020_2026.csv` is the `Breaches_2020_2026` tab of `hhs_breaches.xlsx` (web descriptions removed).

## Interactive features
1. **Sidebar filters:** year range slider, state, breach type, information location, and minimum breach size; every chart, metric and table updates.
2. **Hover tooltips** on every chart (Plotly).
3. **Comparison tool:** pick two information locations and compare them side by side.
4. **Sortable, searchable records table** with a **CSV download** of the filtered records.
5. **Chart toggles:** switch measures (individuals affected, breach count, median size) and log scale.

## Visualizations
1. Bar chart: individuals affected (or breaches, or median size) by information location, split by breach type
2. Pie chart: share of breaches by information location
3. Scatter plot: every breach by submission date vs. individuals affected (log scale), colored by location
4. Heatmap: information location × breach type
5. Line chart: breaches or individuals affected per location by year
6. Comparison charts: breach-type mix and breach-size distribution (box plot) for two locations

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
On share.streamlit.io: Create app → this repo → branch `main` → main file `app.py`.
