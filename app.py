"""Retail Territory Expansion & Sales Analytics Dashboard.
Portfolio project - ALL DATA IS SYNTHETIC and not related to any real company."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Retail Territory Analytics", page_icon="📊", layout="wide")
DATA = Path(__file__).parent / "data"
SCHEMA = {
    "retailers.csv": ["retailer_id", "retailer_name", "area", "distributor_id", "outlet_type",
                      "beat_day", "potential", "monthly_target", "is_active"],
    "distributors.csv": ["distributor_id", "distributor_name", "area"],
    "products.csv": ["sku_id", "sku_name", "category", "mrp"],
    "sales.csv": ["order_id", "date", "retailer_id", "sku_id", "quantity", "net_value"],
    "visits.csv": ["visit_id", "date", "retailer_id", "planned", "visited", "order_taken"],
}
PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"]
CAT_COLORS = {"BLDC Ceiling Fan": "#2563EB", "BLDC Pedestal Fan": "#10B981",
              "Exhaust Fan": "#F59E0B", "Accessories": "#8B5CF6"}
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETTE
px.defaults.labels = {"net_value": "Net sales (₹)", "sales": "Net sales (₹)", "month": "Month", "area": "Area",
                      "category": "Category", "distributor_name": "Distributor", "outlet_type": "Outlet type",
                      "weekday": "Weekday", "potential": "Potential", "achievement_%": "Achievement (%)",
                      "conversion_%": "Conversion (%)", "net_sales": "Net sales (₹)"}
st.markdown("""<style>
.block-container{padding-top:1.2rem;max-width:1400px}
[data-testid="stMetric"]{background:var(--secondary-background-color);border:1px solid rgba(100,116,139,.25);
  border-left:4px solid #2563EB;border-radius:10px;padding:12px 14px}
[data-testid="stMetricLabel"]{font-size:.8rem;opacity:.75}
[data-testid="stMetricValue"]{font-size:1.5rem;font-weight:700}
.banner{background:#EFF6FF;color:#1E3A8A;border-left:4px solid #2563EB;padding:8px 14px;border-radius:6px;font-size:.88rem;margin-bottom:1rem}
.sub{opacity:.7;margin-top:-.8rem;margin-bottom:.8rem}
.stTabs [data-baseweb="tab"]{font-weight:600;padding:10px 14px}
.hero{background:linear-gradient(135deg,#1E3A8A,#2563EB 60%,#06B6D4);padding:22px 26px;border-radius:14px;
  margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
.hero h1{color:#fff !important;font-size:1.7rem;margin:0;padding:0}
.hero p{color:#E0F2FE;margin:4px 0 0}
.pill{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.45);color:#fff;padding:5px 12px;
  border-radius:999px;font-size:.72rem;font-weight:600}
span[data-baseweb="tag"]{background:#2563EB !important;color:#fff !important}
[data-testid="stSidebar"] [data-baseweb="select"] > div{max-height:110px;overflow:auto}
[data-testid="stSidebar"]{border-right:1px solid rgba(100,116,139,.25)}
</style>""", unsafe_allow_html=True)


# ---------- helpers ----------
def inr(x):
    return f"₹{x / 1e5:,.2f} L" if abs(x) >= 1e5 else f"₹{x:,.0f}"


def pct(a, b):
    return float(a) / float(b) * 100 if b else 0.0


def show(fig, h=360):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=45, b=10), template="plotly_white",
                      legend_title_text="", colorway=PALETTE)
    st.plotly_chart(fig, use_container_width=True)


def tbl(df):
    st.dataframe(df, hide_index=True, use_container_width=True)


# ---------- data loading & validation ----------
@st.cache_data
def load_all():
    dfs, errors = {}, []
    for f, cols in SCHEMA.items():
        p = DATA / f
        if not p.exists():
            errors.append(f"Missing file: data/{f} (run `python generate_data.py`)")
            continue
        try:
            df = pd.read_csv(p)
        except Exception as e:  # corrupt / empty file
            errors.append(f"Cannot read data/{f}: {e}")
            continue
        miss = [c for c in cols if c not in df.columns]
        if miss:
            errors.append(f"data/{f} is missing columns: {miss}")
            continue
        dfs[f[:-4]] = df
    return dfs, errors


def clean(d):
    w, d = [], {k: v.copy() for k, v in d.items()}
    for k in ("sales", "visits"):
        d[k]["date"] = pd.to_datetime(d[k]["date"], errors="coerce")
    nums = {"sales": ["quantity", "net_value"], "retailers": ["monthly_target", "is_active"],
            "visits": ["planned", "visited", "order_taken"], "products": ["mrp"]}
    for k, cols in nums.items():
        for c in cols:
            d[k][c] = pd.to_numeric(d[k][c], errors="coerce")
    for k, key in {"retailers": "retailer_id", "distributors": "distributor_id", "products": "sku_id"}.items():
        n = int(d[k].duplicated(key).sum())
        if n:
            w.append(f"{k}: removed {n} duplicate IDs")
            d[k] = d[k].drop_duplicates(key)
    for k in d:
        n = len(d[k])
        d[k] = d[k].dropna(subset=SCHEMA[f"{k}.csv"])
        if len(d[k]) < n:
            w.append(f"{k}: dropped {n - len(d[k])} rows with missing/invalid required values")
    checks = [("sales", "retailer_id", d["retailers"].retailer_id), ("sales", "sku_id", d["products"].sku_id),
              ("visits", "retailer_id", d["retailers"].retailer_id),
              ("retailers", "distributor_id", d["distributors"].distributor_id)]
    for k, col, valid in checks:
        n = len(d[k])
        d[k] = d[k][d[k][col].isin(valid)]
        if len(d[k]) < n:
            w.append(f"{k}: dropped {n - len(d[k])} rows with unknown {col}")
    return d, w


def prorated_targets(start, end, monthly=1.0):
    rows = []
    for p in pd.period_range(start, end, freq="M"):
        ms, me = p.start_time.normalize(), p.end_time.normalize()
        days = (min(me, end) - max(ms, start)).days + 1
        rows.append((p.to_timestamp(), monthly * days / p.days_in_month))
    return pd.DataFrame(rows, columns=["month", "target"])


# ---------- load ----------
st.markdown("""<div class="hero"><div><h1>📊 Retail Territory Expansion &amp; Sales Analytics</h1>
<p>Retailer coverage · Beat planning · SKU availability · Target tracking</p></div>
<span class="pill">SYNTHETIC DEMO DATA · not actual data of Atomberg or any company</span></div>""",
            unsafe_allow_html=True)
raw, errors = load_all()
if errors:
    st.error("Data problems found:\n\n" + "\n".join(f"- {e}" for e in errors))
    st.stop()
data, warns = clean(raw)
if min(len(v) for v in data.values()) == 0:
    st.error("One of the datasets is empty after validation. Check the CSV files.")
    st.stop()

ret = data["retailers"].merge(data["distributors"][["distributor_id", "distributor_name"]], on="distributor_id")
info = ret[["retailer_id", "retailer_name", "area", "distributor_name", "outlet_type", "potential", "beat_day"]]
sales_all = (data["sales"].merge(info, on="retailer_id")
             .merge(data["products"][["sku_id", "sku_name", "category"]], on="sku_id"))
visits_all = data["visits"].merge(info, on="retailer_id")

# ---------- sidebar filters ----------
sb = st.sidebar
sb.header("🎛️ Filters")
dmin, dmax = sales_all.date.min().date(), sales_all.date.max().date()
rng_ = sb.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
if not isinstance(rng_, (tuple, list)) or len(rng_) != 2:
    st.info("Select both a start and an end date.")
    st.stop()
start, end = pd.Timestamp(rng_[0]), pd.Timestamp(rng_[1])
areas = sb.multiselect("Area", sorted(ret.area.unique()), default=sorted(ret.area.unique()))
dist_opts = sorted(ret[ret.area.isin(areas)].distributor_name.unique())
dists = sb.multiselect("Distributor", dist_opts, default=dist_opts)
cat_opts = sorted(data["products"].category.unique())
cats = sb.multiselect("Product category", cat_opts, default=cat_opts)
if warns:
    with sb.expander(f"Data quality notes ({len(warns)})"):
        for w in warns:
            st.write("•", w)

rt = ret[ret.area.isin(areas) & ret.distributor_name.isin(dists)]
rt_act = rt[rt.is_active == 1]
in_rng = lambda df: (df.date >= start) & (df.date <= end) & df.retailer_id.isin(rt.retailer_id)
fsa = sales_all[in_rng(sales_all)]                     # no category filter (targets are not category-based)
fs = fsa[fsa.category.isin(cats)]
fv = visits_all[in_rng(visits_all)]
if fsa.empty or fv.empty or rt_act.empty:
    st.warning("No data for the selected filters. Widen the date range or selections.")
    st.stop()
fv = fv.assign(weekday=fv.date.dt.day_name())
factor = prorated_targets(start, end)["target"].sum()

# ---------- shared aggregates ----------
tot, tot_all = fs.net_value.sum(), fsa.net_value.sum()
target = rt_act.monthly_target.sum() * factor
planned, visited, ordtaken = int(fv.planned.sum()), int(fv.visited.sum()), int(fv.order_taken.sum())
orders = fs.order_id.nunique()

a = rt_act.groupby("area").agg(active=("retailer_id", "count"), mt=("monthly_target", "sum")).reset_index()
a["total_retailers"] = a.area.map(rt.groupby("area").size())
a["ordering"] = a.area.map(fs.groupby("area").retailer_id.nunique()).fillna(0)
a["visited_ret"] = a.area.map(fv[fv.visited == 1].groupby("area").retailer_id.nunique()).fillna(0)
a["sales"] = a.area.map(fs.groupby("area").net_value.sum()).fillna(0)
a["sales_vs_target"] = a.area.map(fsa.groupby("area").net_value.sum()).fillna(0)
a["target"] = a.mt * factor
a["achievement_%"] = (a.sales_vs_target / a.target.replace(0, np.nan) * 100).fillna(0)
a["visit_coverage_%"] = (a.visited_ret / a.active * 100).fillna(0)
a["activation_%"] = (a.ordering / a.active * 100).fillna(0)

# ---------- KPI cards ----------
k = st.columns(6)
k[0].metric("💰 Net sales", inr(tot))
k[1].metric("🎯 Target achievement", f"{pct(tot_all, target):.1f}%", delta=f"{pct(tot_all, target) - 100:+.1f}% vs target")
k[2].metric("🏪 Retailers ordering", f"{int(fs.retailer_id.nunique())}/{len(rt_act)}")
k[3].metric("🚶 Visit compliance", f"{pct(visited, planned):.1f}%")
k[4].metric("🛒 Order conversion", f"{pct(ordtaken, visited):.1f}%")
k[5].metric("🧾 Avg order value", inr(tot / orders if orders else 0))

tabs = st.tabs(["🏠 Overview", "🏪 Retailers & Distributors", "🗺️ Territory", "🚶 Beat & Visits",
                "📦 SKU Availability", "🎯 Targets", "🔁 Conversion", "💡 Insights"])

# ---------- 1. Overview ----------
with tabs[0]:
    m = fs.assign(month=fs.date.dt.to_period("M").dt.to_timestamp()).groupby(["month", "category"], as_index=False).net_value.sum()
    show(px.bar(m, x="month", y="net_value", color="category", title="Monthly net sales by category", color_discrete_map=CAT_COLORS))
    c1, c2 = st.columns(2)
    with c1:
        show(px.bar(a.sort_values("sales"), x="sales", y="area", orientation="h", title="Net sales by area"))
    with c2:
        show(px.pie(fs.groupby("category", as_index=False).net_value.sum(), names="category",
                    values="net_value", hole=.55, title="Category mix", color_discrete_map=CAT_COLORS))

# ---------- 2. Retailers & Distributors ----------
with tabs[1]:
    d = rt_act.groupby("distributor_name").agg(active_retailers=("retailer_id", "count"), mt=("monthly_target", "sum")).reset_index()
    d["ordering"] = d.distributor_name.map(fs.groupby("distributor_name").retailer_id.nunique()).fillna(0).astype(int)
    d["net_sales"] = d.distributor_name.map(fs.groupby("distributor_name").net_value.sum()).fillna(0)
    d["sales_per_active_retailer"] = (d.net_sales / d.active_retailers).round(0)
    d["achievement_%"] = (d.distributor_name.map(fsa.groupby("distributor_name").net_value.sum()).fillna(0)
                          / (d.mt * factor).replace(0, np.nan) * 100).fillna(0).round(1)
    c1, c2 = st.columns(2)
    with c1:
        show(px.bar(d.sort_values("net_sales"), x="net_sales", y="distributor_name", orientation="h",
                    title="Distributor net sales"))
    with c2:
        show(px.bar(d.sort_values("achievement_%"), x="achievement_%", y="distributor_name", orientation="h",
                    title="Distributor target achievement (%)"))
    tbl(d.drop(columns="mt").sort_values("net_sales", ascending=False))
    r = fs.groupby(["retailer_id", "retailer_name", "area", "potential"], as_index=False).agg(
        net_sales=("net_value", "sum"), orders=("order_id", "nunique")).sort_values("net_sales", ascending=False)
    r["cum_share_%"] = (r.net_sales.cumsum() / r.net_sales.sum() * 100).round(1)
    top20 = r.head(max(1, int(len(r) * .2))).net_sales.sum() / r.net_sales.sum() * 100
    st.subheader("Top retailers")
    st.caption(f"Top 20% of ordering retailers contribute {top20:.0f}% of sales (concentration check).")
    tbl(r.head(15))
    o = fs.groupby("outlet_type", as_index=False).net_value.sum()
    show(px.bar(o, x="outlet_type", y="net_value", title="Sales by outlet type"), 300)

# ---------- 3. Territory ----------
with tabs[2]:
    st.caption("Visit coverage = active retailers visited ÷ active retailers. Activation = retailers placing orders ÷ active retailers.")
    long = a.melt(id_vars="area", value_vars=["visit_coverage_%", "activation_%"], var_name="metric", value_name="%")
    show(px.bar(long, x="area", y="%", color="metric", barmode="group", title="Coverage vs activation by area"))
    tbl(a[["area", "total_retailers", "active", "visited_ret", "ordering", "visit_coverage_%",
           "activation_%", "sales"]].round(1))
    ws = rt_act[~rt_act.retailer_id.isin(fs.retailer_id)]
    st.subheader("White-space: active retailers with NO orders in the period")
    ws_s = ws.groupby(["area", "potential"]).size().reset_index(name="retailers")
    show(px.bar(ws_s, x="area", y="retailers", color="potential", title="Dormant retailers by area & potential",
                category_orders={"potential": ["High", "Medium", "Low"]}), 300)
    tbl(ws.assign(p=ws.potential.map({"High": 0, "Medium": 1, "Low": 2})).sort_values(["p", "area"])
        [["retailer_name", "area", "distributor_name", "outlet_type", "potential", "monthly_target"]].head(20))

# ---------- 4. Beat & Visits ----------
with tabs[3]:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    piv = rt_act.pivot_table(index="area", columns="beat_day", values="retailer_id", aggfunc="count", fill_value=0)
    piv = piv.reindex(columns=[x for x in days if x in piv.columns])
    c1, c2 = st.columns(2)
    with c1:
        show(px.imshow(piv, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                       title="Beat load: retailers per area per beat day"))
    with c2:
        wd = fv.groupby("weekday")[["planned", "visited"]].sum().reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]).dropna().reset_index()
        show(px.bar(wd, x="weekday", y=["planned", "visited"], barmode="group", title="Planned vs completed visits"))
    comp = fv.groupby("area")[["planned", "visited"]].sum()
    comp["compliance_%"] = (comp.visited / comp.planned * 100).round(1)
    tbl(comp.reset_index())
    last = visits_all[(visits_all.visited == 1) & (visits_all.date <= end)].groupby("retailer_id").date.max()
    ov = rt_act.assign(last_visit=rt_act.retailer_id.map(last))
    ov["days_since_visit"] = (end - ov.last_visit).dt.days
    ov = ov[(ov.days_since_visit > 30) | ov.last_visit.isna()]
    ov = ov.assign(p=ov.potential.map({"High": 0, "Medium": 1, "Low": 2})).sort_values(["p", "days_since_visit"], ascending=[True, False])
    st.subheader(f"Overdue retailers (not visited in 30+ days): {len(ov)}")
    tbl(ov[["retailer_name", "area", "beat_day", "potential", "last_visit", "days_since_visit"]].head(25))

# ---------- 5. SKU availability ----------
with tabs[4]:
    tgt_av = st.slider("Target availability per SKU (% of active retailers)", 20, 100, 60, 5)
    st.caption("Proxy: a SKU is 'available' at a retailer if it was ordered in the last 90 days before the end date.")
    win = sales_all[(sales_all.date > end - pd.Timedelta(days=90)) & (sales_all.date <= end)
                    & sales_all.retailer_id.isin(rt_act.retailer_id) & sales_all.category.isin(cats)]
    skus = data["products"][data["products"].category.isin(cats)].sku_name.tolist()
    base = rt_act.groupby("area").size()
    have = win.groupby(["area", "sku_name"]).retailer_id.nunique().unstack(fill_value=0)
    mat = have.reindex(index=base.index, columns=skus, fill_value=0).div(base, axis=0) * 100
    show(px.imshow(mat.round(0), text_auto=True, aspect="auto", color_continuous_scale="RdYlGn",
                   title="SKU availability % by area"), 420)
    gap = mat.reset_index().melt(id_vars="area", var_name="SKU", value_name="availability_%")
    gap["retailers_to_add"] = ((tgt_av - gap["availability_%"]).clip(lower=0) / 100 * gap.area.map(base)).round(0).astype(int)
    gap = gap[gap.retailers_to_add > 0].sort_values("retailers_to_add", ascending=False)
    st.subheader("Assortment gap priorities")
    tbl(gap.round(1).head(15))
    cat_av = win.groupby("category").retailer_id.nunique() / max(len(rt_act), 1) * 100
    show(px.bar(cat_av.reset_index(name="%"), x="category", y="%", title="Retailers stocking each category (%)"), 300)

# ---------- 6. Targets ----------
with tabs[5]:
    tm = prorated_targets(start, end, rt_act.monthly_target.sum())
    am = fsa.assign(month=fsa.date.dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).net_value.sum()
    tm = tm.merge(am, on="month", how="left").fillna(0).rename(columns={"net_value": "achievement"})
    tm["achievement_%"] = (tm.achievement / tm.target.replace(0, np.nan) * 100).fillna(0).round(1)
    fig = go.Figure([go.Bar(x=tm.month, y=tm.target, name="Target", marker_color="#CBD5E1"),
                     go.Bar(x=tm.month, y=tm.achievement, name="Achievement", marker_color="#2563EB")])
    fig.update_layout(barmode="group", title="Monthly target vs achievement (all categories)")
    show(fig)
    c1, c2 = st.columns(2)
    with c1:
        show(px.bar(a.sort_values("achievement_%"), x="achievement_%", y="area", orientation="h",
                    color="achievement_%", color_continuous_scale="RdYlGn", title="Achievement % by area"), 320)
    with c2:
        gauge = go.Figure(go.Indicator(mode="gauge+number", value=round(pct(tot_all, target), 1),
                                       number={"suffix": "%"}, title={"text": "Overall achievement"},
                                       gauge={"axis": {"range": [0, 150]}, "bar": {"color": "#2563EB"},
                                              "threshold": {"line": {"color": "red", "width": 3}, "value": 100}}))
        show(gauge, 320)
    st.caption("Targets are synthetic retailer-level monthly targets, pro-rated by days in the selected range.")
    tbl(tm.assign(month=tm.month.dt.strftime("%b %Y")).round(0))

# ---------- 7. Conversion ----------
with tabs[6]:
    c1, c2 = st.columns(2)
    with c1:
        show(go.Figure(go.Funnel(y=["Planned visits", "Completed visits", "Orders taken"],
                                 x=[planned, visited, ordtaken])).update_layout(title="Visit-to-order funnel"), 320)
    with c2:
        cv = fv[fv.visited == 1].groupby("potential").agg(visits=("visit_id", "count"), orders=("order_taken", "sum"))
        cv["conversion_%"] = (cv.orders / cv.visits * 100).round(1)
        show(px.bar(cv.reset_index(), x="potential", y="conversion_%", title="Conversion by retailer potential",
                    category_orders={"potential": ["High", "Medium", "Low"]}), 320)
    for col, title in [("area", "Conversion by area"), ("outlet_type", "Conversion by outlet type")]:
        g = fv[fv.visited == 1].groupby(col).agg(visits=("visit_id", "count"), orders=("order_taken", "sum")).reset_index()
        g["conversion_%"] = (g.orders / g.visits * 100).round(1)
        show(px.bar(g.sort_values("conversion_%"), x=col, y="conversion_%", title=title), 300)
    ls = fs.groupby("order_id").agg(lines=("sku_id", "nunique"), value=("net_value", "sum"))
    st.metric("Avg SKU lines per order", f"{ls.lines.mean():.2f}" if len(ls) else "n/a")

# ---------- 8. Insights ----------
with tabs[7]:
    st.subheader("Data-driven insights (recomputed from current filters)")
    best, worst = a.sort_values("achievement_%").iloc[-1], a.sort_values("achievement_%").iloc[0]
    cvp = fv[fv.visited == 1].groupby("potential").order_taken.mean() * 100
    dormant_high = int((ws.potential == "High").sum())
    top_gap = gap.iloc[0] if len(gap) else None
    st.markdown(f"""
- **Strongest area:** {best.area} at {best['achievement_%']:.0f}% of target; **weakest:** {worst.area} at {worst['achievement_%']:.0f}%.
- **Top-20% retailers** generate about {top20:.0f}% of sales, so revenue is concentrated.
- **Conversion** is {pct(ordtaken, visited):.0f}% overall; by potential: {', '.join(f'{i} {v:.0f}%' for i, v in cvp.items())}.
- **{len(ws)} active retailers** placed no order in the period ({dormant_high} are High potential).
- **{len(ov)} retailers** are overdue for a visit (30+ days).
- {'**Biggest assortment gap:** ' + f"{top_gap.SKU} in {top_gap.area} ({top_gap['availability_%']:.0f}% availability)." if top_gap is not None else 'No assortment gaps vs the target availability.'}
""")
    st.subheader("Actionable recommendations")
    st.markdown(f"""
1. **Reactivate dormant High-potential retailers first** (White-space list); pair each with a distributor follow-up and a starter assortment.
2. **Fix beat discipline in {a.sort_values('visit_coverage_%').iloc[0].area}** (lowest visit coverage); rebalance heavy beat days.
3. **Visit overdue High/Medium retailers** before low-potential ones; use the Overdue list as the weekly call plan.
4. **Close SKU gaps** using the Assortment gap table; push low-availability SKUs through the distributor in the weakest areas.
5. **Raise lines per order** by pitching complementary accessories (regulators, remotes) on every order.
6. **Review targets in {worst.area}**: check whether the gap is demand, distributor supply or coverage before escalating.
""")
    st.caption("These are analytical observations on SYNTHETIC data, not real business results.")

st.divider()
st.caption("Retail Territory Expansion & Sales Analytics · Portfolio project · All data is synthetic.")
