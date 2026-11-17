# HHS Health Data Breaches: Vulnerable Information Locations

Team: Rithika Gantla, Joudi Elansary, Misha Shariff, Beauty Babatunde, Jennifer Tran

**Research question:** Which locations of breached information (email, network servers, laptops, paper records, etc.) are associated with the largest reported breaches?

**Data:** HHS OCR Breach Portal, current + archived records, breaches submitted Jan 1, 2020 to Nov 10, 2026 (5,016 records). `breaches_2020_2026.csv`.

## Features
- Dropdown filters: state, year, breach type (all charts update)
- Hover tooltips on every bar, slice, and point

## Visualizations
1. Bar chart: individuals affected (or breach count) by information location, split by breach type
2. Pie chart: share of breaches by information location
3. Scatter plot: every breach by submission date vs. individuals affected (log scale), colored by location

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push this folder to GitHub, then on share.streamlit.io choose New app, pick the repo, and set the main file to `app.py`.
