# 📊 Retail Territory Expansion & Sales Analytics Dashboard

> **⚠️ Synthetic data notice:** Every dataset in this repository is **artificially generated** by `generate_data.py`.
> It is **not** actual data of Atomberg or any other company, and no real business results are claimed.
> This is an independent learning/portfolio project for an *Area Sales Officer – Trainee* style role.

## 1. Problem statement
An Area Sales Officer (ASO) manages retailers through distributors, plans beats, and must hit targets across many outlets and SKUs. Typical daily questions:
- Which areas, distributors and retailers drive sales, and which are behind target?
- Which active retailers are dormant or overdue for a visit?
- Where are SKUs missing from retailer shelves (assortment gaps)?
- Are visits converting into orders?

This dashboard answers these questions from five CSV files using Python, Pandas, Plotly and Streamlit.

## 2. Features
| # | Feature | Where |
|---|---------|-------|
| 1 | KPI cards (sales, achievement, active retailers, visit compliance, conversion, AOV) | Top of page |
| 2 | Retailer & distributor performance, top retailers, concentration check | *Retailers & Distributors* |
| 3 | Area coverage vs activation, dormant "white-space" retailers | *Territory Expansion* |
| 4 | Beat load heatmap, planned vs completed visits, overdue retailer list | *Beat & Visits* |
| 5 | SKU availability heatmap and gap priorities (adjustable target %) | *SKU Availability* |
| 6 | Target vs achievement (monthly, area, gauge) | *Target vs Achievement* |
| 7 | Visit-to-order funnel, conversion by potential / area / outlet type | *Conversion* |
| 8 | Filters: date, area, distributor, product category | Sidebar |
| 9 | Data validation and clear error messages | Startup |
| 10 | Auto-generated insights and recommendations | *Insights* |

## 3. Project structure
```
retail-territory-dashboard/
├── app.py                 # Streamlit dashboard
├── generate_data.py       # Reproducible synthetic data generator (seed=42)
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── retailers.csv      # 140 synthetic retailers (area, beat day, potential, target)
│   ├── distributors.csv   # 7 synthetic distributors
│   ├── products.csv       # 12 generic fan SKUs in 4 categories
│   ├── sales.csv          # order lines, Apr-Sep 2026
│   └── visits.csv         # planned/completed visits and order outcome
└── screenshots/           # add your own dashboard screenshots here
```

## 4. Methodology
- **Data generation:** retailers are assigned an area, distributor, outlet type, beat day and potential (High/Medium/Low). Visits follow beat plans (High weekly, Medium fortnightly, Low every 4 weeks) with area-specific completion rates. A completed visit may convert to an order (probability depends on potential and a summer seasonality factor); orders create SKU-level sales lines. Area-SKU affinities create deliberate assortment gaps to analyse.
- **Validation (`clean()` in `app.py`):** checks missing files/columns, duplicate IDs, null or non-numeric values, invalid dates and orphan keys (unknown retailer/SKU/distributor). Issues are shown in the sidebar; fatal problems stop the app with a clear message.
- **KPI definitions**
  - *Target achievement* = net sales (all categories) ÷ pro-rated sum of active retailers' monthly targets.
  - *Visit compliance* = completed visits ÷ planned visits.
  - *Order conversion* = visits with an order ÷ completed visits.
  - *Visit coverage* = active retailers visited ÷ active retailers. *Activation* = retailers ordering ÷ active retailers.
  - *SKU availability* = share of active retailers that ordered the SKU in the 90 days before the end date.
  - *Assortment gap* = retailers needed to reach the chosen target availability %.

## 5. Installation & run
```bash
git clone https://github.com/<your-username>/retail-territory-dashboard.git
cd retail-territory-dashboard
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generate_data.py          # optional: regenerates the CSVs in data/
streamlit run app.py
```
Open http://localhost:8501. Requires Python 3.9+.

## 6. Results
This project produces **dashboards and rule-based insights, not business results**. Open the *Insights* tab to see observations recomputed from the filtered synthetic data. Add screenshots of each tab to `screenshots/` and reference them here:

`![Overview](screenshots/overview.png)`

## 7. Example recommendations the dashboard supports
1. Reactivate dormant High-potential retailers first.
2. Use the overdue list as the weekly beat call plan.
3. Close SKU gaps in the lowest-availability areas through distributors.
4. Increase SKU lines per order with complementary accessories.
5. Investigate weak target achievement (demand vs supply vs coverage) before escalating.

## 8. Assumptions & limitations
- All data is synthetic; patterns reflect generator rules, not real markets. Insights illustrate method only.
- SKU "availability" is a proxy from order history, not a physical shelf audit.
- Retailer-level monthly targets are invented and pro-rated by days; category-level targets are not modelled.
- Sales are net of distributor margin by a simple fixed factor; no returns, credit notes, stock-outs or competitor data.
- Visits are only the planned beat visits; unplanned visits, GPS and time-of-day are not modelled.
- Single six-month window; no forecasting or statistical significance testing.
- Not formally unit-tested; validated via a smoke test of the data pipeline.

## 9. Possible extensions
Forecasting, retailer segmentation (RFM), map view with coordinates, Excel export, automated tests with `pytest`.

## License
MIT - for portfolio and educational use.
