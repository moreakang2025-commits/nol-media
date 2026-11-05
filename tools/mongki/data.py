"""Price data + calculations (election moves, $10/day backtest). Real data from Yahoo Finance
(stooq as fallback). MONGKI_OFFLINE=1 uses a synthetic random walk so rendering can be tested."""
import datetime as dt, json, math, random, time
from common import OFFLINE, pct_words, money

UA = {"User-Agent": "Mozilla/5.0 (compatible; mongki-money/1.0)"}

def _yahoo(ticker, start):
    import requests
    p1 = int(dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc).timestamp())
    p2 = int(time.time()) + 86400
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={p1}&period2={p2}&interval=1d&events=split"
    r = requests.get(url, headers=UA, timeout=30); r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose") or res["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, adj):
        if c is not None:
            out.append((dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(), float(c)))
    return out

def _stooq(ticker, start):
    import requests, csv, io
    url = f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d"
    r = requests.get(url, headers=UA, timeout=30); r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text)))
    return [(x["Date"], float(x["Close"])) for x in rows if x["Date"] >= start and x.get("Close")]

def _synthetic(ticker, start):
    rnd = random.Random(ticker); d = dt.date.fromisoformat(start); p = 100.0; out = []
    while d <= dt.date.today():
        if d.weekday() < 5:
            p *= math.exp(rnd.gauss(0.0006, 0.03 if ticker != "SPY" else 0.011)); out.append((d.isoformat(), p))
        d += dt.timedelta(days=1)
    return out

def prices(ticker, start="2019-01-01"):
    if OFFLINE:
        return _synthetic(ticker, start)
    for fn in (_yahoo, _stooq):
        try:
            s = fn(ticker, start)
            if len(s) > 20:
                return s
        except Exception as e:
            print(f"[data] {fn.__name__} {ticker} failed: {e}")
    raise RuntimeError(f"no price data for {ticker}")

def _idx_on_or_before(series, day):
    i = None
    for k, (d, _) in enumerate(series):
        if d <= day: i = k
        else: break
    return i

def election_moves(series, day):
    i = _idx_on_or_before(series, day)
    if i is None or i + 1 >= len(series):
        return {"d1": None, "d30": None}
    base = series[i][1]
    d1 = (series[i + 1][1] / base - 1) * 100
    d30 = (series[i + 21][1] / base - 1) * 100 if i + 21 < len(series) else None
    return {"d1": round(d1, 1), "d30": None if d30 is None else round(d30, 1)}

def dca(series, start, daily):
    shares = invested = 0.0; peak = 0.0; dd = 0.0; dd_date = None; curve = []
    for d, c in series:
        if d < start: continue
        shares += daily / c; invested += daily
        v = shares * c; peak = max(peak, v)
        if peak > 0 and (v / peak - 1) < dd:
            dd, dd_date = v / peak - 1, d
        curve.append((d, invested, v))
    v = curve[-1][2]
    return {"invested": invested, "value": v, "ret": (v / invested - 1) * 100, "dd": dd * 100,
            "dd_date": dd_date, "curve": curve[:: max(1, len(curve) // 400)] + [curve[-1]], "asof": curve[-1][0]}

def _nice_date(iso):
    return dt.date.fromisoformat(iso).strftime("%B %-d, %Y") if iso else "an unknown date"

def compute(ep):
    spec = ep["data"]; out = {"prices_asof": None}
    cache = {t: prices(t) for t in spec.get("price_tickers", [])}
    bt = spec.get("backtest")
    if bt:
        main = dca(cache[bt["ticker"]], bt["start"], bt["daily"])
        cmp_ = dca(cache[bt["compare"]], bt["start"], bt["daily"])
        out.update(bt_invested=money(main["invested"]), bt_value=money(main["value"]),
                   bt_return_words=pct_words(main["ret"]).replace("up", "a gain of").replace("down", "a loss of"),
                   bt_dd_words=f"{abs(main['dd']):.0f} percent down", bt_dd_date=_nice_date(main["dd_date"]),
                   cmp_value=money(cmp_["value"]),
                   cmp_return_words=pct_words(cmp_["ret"]).replace("up", "a gain of").replace("down", "a loss of"),
                   _bt=main, _cmp=cmp_, _bt_spec=bt, prices_asof=main["asof"])
    for lump in spec.get("lumps", []):
        ser = cache[lump["ticker"]]; shares = cost = 0.0
        for b in lump["buys"]:
            i = _idx_on_or_before(ser, b["date"]); shares += b["amount"] / ser[i][1]; cost += b["amount"]
        val = shares * ser[-1][1]; k = lump["key"]
        out[f"{k}_value"] = f"about {val / 1e6:,.0f} million dollars"; out[f"{k}_change_words"] = pct_words((val / cost - 1) * 100)
        out[f"_{k}"] = {"cost": cost, "value": val, "shares": shares, "asof": ser[-1][0], "ticker": lump["ticker"]}
    more = {}
    for t in spec.get("dca_more", []):
        r = dca(cache[t], bt["start"], bt["daily"]); more[t] = r
        out[f"{t}_dca_value"] = money(r["value"]); out[f"{t}_dca_words"] = pct_words(r["ret"]).replace("up", "a gain of").replace("down", "a loss of")
    if more:
        out["_dca_more"] = more
        names = {"TSLA": "Tesla", "LCID": "Lucid", "RIVN": "Rivian", "SPY": "the boring S&P 500 fund"}
        allv = {bt["ticker"]: out["_bt"]["value"], **{t: r["value"] for t, r in more.items()}}
        win = max(allv, key=allv.get); out["dca_winner"] = names.get(win, win)
    els = []
    for e in spec.get("elections", []):
        m = election_moves(cache[bt["ticker"] if bt else spec["price_tickers"][0]], e["date"])
        out[f"{e['key']}_1d_words"] = pct_words(m["d1"]); out[f"{e['key']}_30d_words"] = pct_words(m["d30"])
        els.append({**e, **m})
    out["_elections"] = els
    if spec.get("event_day") and bt:
        ser = [x for x in cache[bt["ticker"]] if x[0] >= "2021-01-01"]
        rets = [(ser[i][0], (ser[i][1] / ser[i - 1][1] - 1) * 100) for i in range(1, len(ser))]
        ev = election_moves(cache[bt["ticker"]], spec["event_day"])["d1"]
        if ev is not None:
            worse = sum(1 for _, r in rets if r <= ev)
            out["worse_days"] = f"{worse:,}"; out["worse_share"] = f"{worse / len(rets) * 100:.0f} percent"
            out["trading_days"] = f"{len(rets):,}"
            w = min(rets, key=lambda x: x[1]); out["worst_day"] = _nice_date(w[0]); out["worst_day_words"] = pct_words(w[1])
    if spec.get("event_day"):
        moves = {}
        for t, s in cache.items():
            m = election_moves(s, spec["event_day"]); moves[t] = m["d1"]
        out["_event_moves"] = moves
    return out

def fill_obj(o, vals):
    if isinstance(o, str): return fill(o, vals)
    if isinstance(o, list): return [fill_obj(x, vals) for x in o]
    if isinstance(o, dict): return {k: fill_obj(v, vals) for k, v in o.items()}
    return o

def fill(text, vals):
    class D(dict):
        def __missing__(self, k): return "{" + k + "}"
    return text.format_map(D({k: v for k, v in vals.items() if not k.startswith("_")}))

if __name__ == "__main__":
    import sys
    ep = json.load(open(sys.argv[1]))
    v = compute(ep)
    print(json.dumps({k: x for k, x in v.items() if not k.startswith("_")}, indent=1))
    print("event moves:", v.get("_event_moves")); print("elections:", v.get("_elections"))
