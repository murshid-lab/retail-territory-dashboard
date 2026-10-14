"""Generate SYNTHETIC sample data for the dashboard. Not real company data.
Run: python generate_data.py   (deterministic, seed=42)"""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)

AREAS = {"Pune East": "Pune", "Pune West": "Pune", "Nashik": "Nashik",
         "Nagpur": "Nagpur", "Kolhapur": "Kolhapur", "Aurangabad": "Aurangabad"}
DIST_AREAS = ["Pune East", "Pune West", "Pune West", "Nashik", "Nagpur", "Kolhapur", "Aurangabad"]
names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta"]
dist = pd.DataFrame({"distributor_id": [f"D{i+1:02d}" for i in range(7)],
                     "distributor_name": [f"Synthetic Distributor {n}" for n in names],
                     "area": DIST_AREAS, "city": [AREAS[a] for a in DIST_AREAS],
                     "credit_days": rng.choice([15, 21, 30], 7)})
dist.to_csv(OUT / "distributors.csv", index=False)

prod = pd.DataFrame([
    ("SKU01", "BLDC Ceiling Fan 1200mm - Model A", "BLDC Ceiling Fan", 3900),
    ("SKU02", "BLDC Ceiling Fan 1200mm - Model B", "BLDC Ceiling Fan", 4600),
    ("SKU03", "BLDC Ceiling Fan 1400mm - Model C", "BLDC Ceiling Fan", 5200),
    ("SKU04", "BLDC Ceiling Fan Premium - Model D", "BLDC Ceiling Fan", 6400),
    ("SKU05", "BLDC Pedestal Fan - Model E", "BLDC Pedestal Fan", 5600),
    ("SKU06", "BLDC Table Fan - Model F", "BLDC Pedestal Fan", 4300),
    ("SKU07", "BLDC Wall Fan - Model G", "BLDC Pedestal Fan", 4800),
    ("SKU08", "Exhaust Fan 150mm - Model H", "Exhaust Fan", 2300),
    ("SKU09", "Exhaust Fan 200mm - Model I", "Exhaust Fan", 2800),
    ("SKU10", "Remote Control - Model J", "Accessories", 450),
    ("SKU11", "Fan Regulator - Model K", "Accessories", 650),
    ("SKU12", "Fan Light Kit - Model L", "Accessories", 900),
], columns=["sku_id", "sku_name", "category", "mrp"])
prod.to_csv(OUT / "products.csv", index=False)

N = 140
area_list = rng.choice(list(AREAS), N, p=[.22, .22, .16, .16, .12, .12])
rows = []
for i, a in enumerate(area_list):
    d = rng.choice(dist.loc[dist.area == a, "distributor_id"])
    pot = rng.choice(["High", "Medium", "Low"], p=[.2, .45, .35])
    tgt = {"High": (90000, 140000), "Medium": (45000, 80000), "Low": (15000, 35000)}[pot]
    rows.append((f"R{i+1:03d}", f"Synthetic Retailer {i+1:03d}", a, d,
                 rng.choice(["Electrical", "Hardware", "Appliance Store", "Modern Trade"], p=[.4, .25, .25, .1]),
                 rng.choice(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]), pot,
                 int(rng.integers(*tgt) // 1000 * 1000), int(rng.random() > .08),
                 str((pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(rng.integers(0, 1100)))).date())))
ret = pd.DataFrame(rows, columns=["retailer_id", "retailer_name", "area", "distributor_id", "outlet_type",
                                  "beat_day", "potential", "monthly_target", "is_active", "onboarded_date"])
ret.to_csv(OUT / "retailers.csv", index=False)

DOW = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5}
FREQ = {"High": 1, "Medium": 2, "Low": 4}                      # visit every N weeks
VISIT_P = {a: p for a, p in zip(AREAS, [.92, .88, .85, .80, .78, .83])}
SEASON = {4: 1.15, 5: 1.25, 6: 1.0, 7: .85, 8: .85, 9: .9}
ORDER_P = {"High": .55, "Medium": .40, "Low": .25}
pop = np.array([.14, .12, .09, .05, .07, .06, .04, .13, .10, .08, .07, .05])
aff = {(a, s): rng.uniform(.3, 1.2) for a in AREAS for s in prod.sku_id}   # area-SKU affinity -> creates gaps
mondays = pd.date_range("2026-03-30", "2026-09-28", freq="W-MON")
visits, sales, oid = [], [], 0
for _, r in ret[ret.is_active == 1].iterrows():
    for w, m in enumerate(mondays):
        if w % FREQ[r.potential] != 0: continue
        day = m + pd.Timedelta(days=DOW[r.beat_day])
        if not (pd.Timestamp("2026-04-01") <= day <= pd.Timestamp("2026-09-30")): continue
        vis = int(rng.random() < VISIT_P[r.area])
        ordr = int(vis and rng.random() < min(ORDER_P[r.potential] * SEASON[day.month], .9))
        visits.append((f"V{len(visits)+1:05d}", day.date(), r.retailer_id, 1, vis, ordr,
                       int(rng.integers(15, 46)) if vis else 0))
        if ordr:
            oid += 1
            w_ = pop * np.array([aff[(r.area, s)] for s in prod.sku_id]); w_ /= w_.sum()
            for s in rng.choice(prod.sku_id, int(rng.integers(1, 4)), replace=False, p=w_):
                mrp = prod.set_index("sku_id").loc[s, "mrp"]
                qty = int(rng.integers(1, 7)); price = round(mrp * 0.78 * rng.uniform(.95, 1), 2)
                sales.append((f"O{oid:05d}", day.date(), r.retailer_id, s, qty, price, round(qty * price, 2)))
pd.DataFrame(visits, columns=["visit_id", "date", "retailer_id", "planned", "visited", "order_taken",
                              "visit_duration_min"]).to_csv(OUT / "visits.csv", index=False)
pd.DataFrame(sales, columns=["order_id", "date", "retailer_id", "sku_id", "quantity", "unit_price",
                             "net_value"]).to_csv(OUT / "sales.csv", index=False)
print("Synthetic data written to", OUT)
