#!/usr/bin/env python3
"""Market Pulse - Ultimate Investor Intelligence Platform"""
import os,sys
from datetime import datetime,timedelta

INDICES={"^GSPC":"S&P 500","^IXIC":"NASDAQ","^DJI":"DOW 30","^GSPTSE":"TSX","^RUT":"Russell 2000",
"^VIX":"VIX","BTC-USD":"Bitcoin","ETH-USD":"Ethereum","CL=F":"Crude Oil","GC=F":"Gold",
"SI=F":"Silver","HG=F":"Copper","NG=F":"Nat Gas","^TNX":"10Y Yield","^IRX":"3M Yield",
"DX-Y.NYB":"US Dollar","EURUSD=X":"EUR/USD","CADUSD=X":"CAD/USD","JPY=X":"USD/JPY","GBPUSD=X":"GBP/USD"}

WATCHLIST={"NVDA":"NVIDIA","AMD":"AMD","TSM":"TSMC","ASML":"ASML","AXON":"Axon",
"AAPL":"Apple","MSFT":"Microsoft","GOOGL":"Google","AMZN":"Amazon","META":"Meta",
"TSLA":"Tesla","AVGO":"Broadcom","ARM":"ARM Holdings","PLTR":"Palantir","SMCI":"Super Micro"}

SECTORS={"XLK":"Technology","XLF":"Financials","XLE":"Energy","XLV":"Healthcare",
"XLY":"Consumer Disc","XLP":"Consumer Staples","XLI":"Industrials","XLB":"Materials",
"XLRE":"Real Estate","XLU":"Utilities","XLC":"Communications"}

MOVERS=["NVDA","TSLA","AMD","AAPL","MSFT","GOOGL","AMZN","META","AVGO","ARM",
"PLTR","SMCI","TSM","ASML","AXON","CRM","NFLX","COIN","MARA","RIOT",
"SOFI","NU","SQ","SHOP","SNOW","MDB","NET","DDOG","ZS","CRWD",
"PANW","ABNB","UBER","LYFT","RIVN","LCID","NIO","LI","XPEV","BABA",
"JD","PDD","SE","MELI","DIS","WMT","COST","JPM","GS","V",
"MA","BRK-B","UNH","LLY","NVO","ORCL","ADBE","NOW","INTU","MU",
"QCOM","INTC","TXN","BA","CAT","XOM","CVX","PFE","JNJ","KO",
"PEP","PG","HD","LOW","TGT","SBUX","MCD","PYPL","ROKU","SNAP"]

NEWS_QUERIES={"Fed & Interest Rates":"Federal Reserve OR interest rates OR inflation OR CPI OR FOMC",
"Earnings Season":"earnings report OR earnings beat OR earnings miss OR revenue growth",
"IPOs & M&A":"IPO OR merger acquisition OR M&A OR SPAC OR buyback",
"Trade & Tariffs":"Trump tariff OR trade war OR sanctions OR import duties",
"AI & Technology":"Jensen Huang OR NVIDIA AI OR artificial intelligence OR OpenAI",
"Crypto & Digital Assets":"Bitcoin OR Ethereum OR crypto regulation OR cryptocurrency",
"Social Media Buzz":"viral stock OR meme stock OR WallStreetBets OR trending finance"}

SPORTS_QUERIES={"Soccer":"soccer OR Premier League OR Champions League OR MLS OR FIFA",
"Basketball":"NBA OR basketball scores OR NBA playoffs OR NBA finals",
"Football":"NFL OR football scores OR CFL OR Super Bowl",
"Hockey":"NHL OR hockey scores OR Stanley Cup OR NHL playoffs",
"Baseball":"MLB OR baseball scores OR World Series OR home run"}

def fetch_stock_data(tickers):
    try:
        import yfinance as yf
        data={}
        raw=yf.download(" ".join(tickers),period="22d",group_by="ticker",progress=False,threads=True)
        for t in tickers:
            try:
                h=raw[t] if len(tickers)>1 and t in raw.columns.get_level_values(0) else (raw if len(tickers)==1 else None)
                if h is not None:
                    h=h.dropna()
                    if len(h)>=2:
                        c=float(h["Close"].iloc[-1]);p=float(h["Close"].iloc[-2])
                        p5=float(h["Close"].iloc[-5]) if len(h)>=5 else p
                        p20=float(h["Close"].iloc[0]) if len(h)>=15 else p5
                        v=float(h["Volume"].iloc[-1]) if "Volume" in h.columns else 0
                        va=float(h["Volume"].iloc[-5:].mean()) if "Volume" in h.columns and len(h)>=5 else max(v,1)
                        data[t]={"price":c,"change":c-p,"change_pct":(c-p)/p*100,
                            "mom5":(c/p5-1)*100 if p5>0 else 0,"mom20":(c/p20-1)*100 if p20>0 else 0,
                            "volume":v,"vol_avg":va,"vol_ratio":v/va if va>0 else 1,
                            "high":float(h["High"].iloc[-1]),"low":float(h["Low"].iloc[-1]),"open":float(h["Open"].iloc[-1])}
            except: continue
        return data
    except Exception as e:
        print(f"ERROR: {e}");return {}

def fetch_news(query,page_size=5):
    key=os.getenv("NEWSAPI_KEY","")
    if not key: return []
    try:
        import requests
        r=requests.get("https://newsapi.org/v2/everything",params={"apiKey":key,"q":query,"language":"en",
            "sortBy":"publishedAt","pageSize":page_size,
            "from":(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")},timeout=10).json()
        if r.get("status")=="ok":
            return [{"title":a.get("title",""),"description":a.get("description","") or "","url":a.get("url",""),
                "source":a.get("source",{}).get("name",""),"published":a.get("publishedAt","")}
                for a in r.get("articles",[]) if a.get("title")!="[Removed]"]
        return []
    except: return []

# ===== ANALYSIS =====

def get_sentiment(vix):
    if vix is None: return "N/A","#888","No data","neutral",50
    if vix<12: return "Extreme Greed","#00ff00","Markets euphoric. VIX below 12 = extreme complacency. Smart money sells into euphoria. Trim extended positions, buy protective puts.","extreme_greed",95
    if vix<17: return "Greed","#66ff66","Low vol favors momentum. Trend-following works. Stay long quality, tighten stops. Options cheap \u2014 buy protection.","greed",75
    if vix<20: return "Neutral","#ffff00","Balanced conditions. Stock-picking matters more than macro. Focus on earnings quality and catalysts.","neutral",50
    if vix<25: return "Fear","#ff6600","Elevated anxiety. Institutions hedging. Overreactions create selective buying ops in quality names.","fear",30
    if vix<30: return "High Fear","#ff3300","Significant stress. Buying quality at VIX 25-30 historically produces above-avg 12-month returns.","high_fear",15
    return "Extreme Fear","#ff0000","Panic selling. VIX >30 = rare extremes, historically major bottoms. Be greedy when others fearful.","extreme_fear",5

def analyze_stock(t,d):
    L=[];pct=d.get("change_pct",0);m5=d.get("mom5",0);m20=d.get("mom20",0);vr=d.get("vol_ratio",1)
    if abs(pct)>5: L.append(("Explosive rally" if pct>0 else "Severe selloff")+f" of {abs(pct):.1f}% \u2014 outlier move.")
    elif abs(pct)>3: L.append(("Surging " if pct>0 else "Plunging ")+f"{abs(pct):.1f}% \u2014 significant.")
    elif abs(pct)>1: L.append(("Up " if pct>0 else "Down ")+f"{abs(pct):.1f}%.")
    else: L.append(f"Flat ({pct:+.1f}%).")
    if vr>2: L.append(f"Vol {vr:.1f}x avg \u2014 institutional flow.")
    elif vr>1.3: L.append(f"Above-avg vol ({vr:.1f}x).")
    elif vr<0.5: L.append("Thin volume.")
    if m5>3 and m20>8: L.append(f"Strong uptrend: +{m5:.1f}% (5D), +{m20:.1f}% (20D).")
    elif m5<-3 and m20<-5: L.append(f"Downtrend: {m5:.1f}% (5D), {m20:.1f}% (20D).")
    elif m5>0 and m20<0: L.append("Bounce in downtrend.")
    elif m5<0 and m20>0: L.append("Pullback in uptrend \u2014 potential entry.")
    return " ".join(L)

def get_signal(d):
    s=d.get("mom20",0)*0.4+d.get("mom5",0)*0.35+d.get("change_pct",0)*0.25
    if s>4 and d.get("mom5",0)>0: return "BULLISH","#00ff88"
    if s<-4 and d.get("mom5",0)<0: return "BEARISH","#ff4444"
    if s>1: return "LEAN BULL","#66ff66"
    if s<-1: return "LEAN BEAR","#ff6600"
    return "NEUTRAL","#ffff00"

def classify_stocks(data):
    lo,md,hi=[],[],[]
    for t,d in data.items():
        m20=d.get("mom20",0);m5=d.get("mom5",0);pct=d.get("change_pct",0);vr=d.get("vol_ratio",1)
        sc=m20*0.4+m5*0.3+pct*0.3
        if m20>8 and m5>2:
            hi.append((t,d,"BUY" if vr>1.1 else "WATCH",sc,f"+{m20:.0f}% (20D). {'Vol confirms.' if vr>1.2 else 'Needs vol.'}"))
        elif m20>2:
            md.append((t,d,"BUY" if m5>0 else "HOLD",sc,f"+{m20:.0f}% trend. {'ST positive.' if m5>0 else 'Minor dip.'}"))
        elif m20>-3:
            lo.append((t,d,"HOLD" if m5>-1 else "WATCH",sc,f"Range-bound {m20:+.0f}%."))
        else:
            lo.append((t,d,"AVOID",sc,f"Downtrend {m20:+.0f}%. High risk."))
    hi.sort(key=lambda x:x[3],reverse=True);md.sort(key=lambda x:x[3],reverse=True);lo.sort(key=lambda x:x[3],reverse=True)
    return lo[:12],md[:12],hi[:12]

def analyze_market(idx,mov):
    A=[];nas=idx.get("^IXIC",{}).get("change_pct",0);dow=idx.get("^DJI",{}).get("change_pct",0)
    vix=idx.get("^VIX",{}).get("price");yld=idx.get("^TNX",{}).get("price")
    btc=idx.get("BTC-USD",{}).get("change_pct",0);oil=idx.get("CL=F",{}).get("change_pct",0)
    gold=idx.get("GC=F",{}).get("change_pct",0)
    ups=sum(1 for d in mov.values() if d.get("change_pct",0)>0);tot=len(mov)
    br=ups/tot*100 if tot>0 else 50
    if br>70: A.append(f"<b>Breadth:</b> {br:.0f}% advancing ({ups}/{tot}). Broad rally. Institutions buying across sectors.")
    elif br>55: A.append(f"<b>Breadth:</b> {br:.0f}% advancing. Healthy, selective participation.")
    elif br>45: A.append(f"<b>Breadth:</b> {br:.0f}%. Undecided. Await catalyst.")
    else: A.append(f"<b>Breadth:</b> {br:.0f}% \u2014 widespread selling. Defensive positioning.")
    if nas>dow+0.5: A.append("<b>Rotation:</b> Tech leading \u2014 risk-on, AI themes driving flows.")
    elif dow>nas+0.5: A.append("<b>Rotation:</b> Value leading \u2014 rate expectations or cyclical optimism.")
    if vix:
        if vix<15: A.append(f"<b>VIX:</b> {vix:.1f} \u2014 calm. Options cheap. Historically precedes vol spikes.")
        elif vix<22: A.append(f"<b>VIX:</b> {vix:.1f} \u2014 normal range.")
        else: A.append(f"<b>VIX:</b> {vix:.1f} \u2014 elevated fear. Quality dip-buying zone.")
    if yld:
        if yld>4.5: A.append(f"<b>Yields:</b> 10Y {yld:.2f}% \u2014 restrictive. Growth valuations pressured.")
        elif yld>3.5: A.append(f"<b>Yields:</b> 10Y {yld:.2f}% \u2014 moderate.")
        else: A.append(f"<b>Yields:</b> 10Y {yld:.2f}% \u2014 accommodative. Growth favored.")
    if abs(btc)>4: A.append(f"<b>Crypto:</b> BTC {'up' if btc>0 else 'down'} {abs(btc):.1f}%. Leads risk sentiment 24-48hrs.")
    if abs(oil)>2: A.append(f"<b>Oil:</b> {'Up' if oil>0 else 'Down'} {abs(oil):.1f}%. {'Inflation risk.' if oil>0 else 'Demand fears.'}")
    if abs(gold)>1: A.append(f"<b>Gold:</b> {'Up' if gold>0 else 'Down'} {abs(gold):.1f}%. {'Safety bid.' if gold>0 else 'Risk-on.'}")
    return A

def analyze_news_item(a):
    t=a.get("title","").lower();d=a.get("description","") or ""
    s=(d[:220]+"...") if len(d)>220 else d
    if any(w in t for w in ["fed","fomc","rate","inflation","cpi"]): s+=" Rate decisions reprice every asset class simultaneously."
    elif any(w in t for w in ["earnings","revenue","profit","beat","miss"]): s+=" Watch guidance and margin trends over headline numbers."
    elif any(w in t for w in ["tariff","trade war","sanction"]): s+=" Trade policy reshapes supply chains and margin outlook."
    elif any(w in t for w in ["ipo","merger","acquisition","m&a"]): s+=" M&A signals confidence. Premiums reveal hidden value."
    elif any(w in t for w in ["nvidia","jensen","ai ","openai","chip"]): s+=" AI capex is the dominant spending cycle. Semis and cloud benefit."
    elif any(w in t for w in ["bitcoin","crypto","ethereum"]): s+=" Crypto reflects liquidity and risk appetite. Regulation is key."
    elif any(w in t for w in ["trump","election","congress"]): s+=" Political shifts create sector winners and losers."
    elif any(w in t for w in ["oil","opec","crude"]): s+=" Energy prices impact inflation, spending, and margins."
    else: s+=" Monitor for impact on earnings, rates, and sentiment."
    return s

# ===== CSS =====

CSS="""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:'Inter',system-ui,sans-serif;line-height:1.6}
nav{position:sticky;top:0;z-index:100;background:rgba(10,10,15,0.92);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border-bottom:1px solid rgba(0,255,136,0.08);padding:0 20px}
nav .c{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:56px;flex-wrap:wrap}
nav .logo{font-size:18px;font-weight:800;color:#00ff88;text-decoration:none;letter-spacing:0.5px}
nav .lk{display:flex;gap:2px;flex-wrap:wrap}
nav .lk a{color:#6b6b8a;text-decoration:none;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:600;transition:all 0.25s}
nav .lk a:hover,nav .lk a.on{color:#00ff88;background:rgba(0,255,136,0.08)}
.pg{max-width:1400px;margin:0 auto;padding:24px 20px}
.hdr{text-align:center;padding:48px 24px 40px;margin-bottom:32px;background:linear-gradient(135deg,#0f0f1a,#1a1a3e,#0f2440);border-radius:20px;border:1px solid rgba(0,255,136,0.08);position:relative;overflow:hidden}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00ff88,#4da6ff,#00ff88,transparent)}
.hdr h1{font-size:36px;font-weight:900;background:linear-gradient(135deg,#00ff88,#4da6ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}
.hdr p{color:#6b6b8a;font-size:14px}
.grid{display:grid;gap:16px;margin-bottom:28px}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.g4{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.cd{background:rgba(18,18,28,0.8);border-radius:14px;padding:20px;border:1px solid rgba(255,255,255,0.04);transition:all 0.3s;backdrop-filter:blur(10px)}
.cd:hover{border-color:rgba(0,255,136,0.15);transform:translateY(-1px);box-shadow:0 8px 32px rgba(0,0,0,0.3)}
.cd h3{color:#00ff88;font-size:13px;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:14px;font-weight:700}
.ic{text-align:center;padding:18px 12px}
.ic .nm{font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1.5px;font-weight:600}
.ic .pr{font-size:24px;font-weight:800;margin:8px 0 4px;font-family:'JetBrains Mono',monospace}
.ic .ch{font-size:13px;font-weight:700;font-family:'JetBrains Mono',monospace}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:12px 8px;color:#4a4a6a;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:700;border-bottom:2px solid rgba(255,255,255,0.04)}
td{padding:12px 8px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:13px}
tr:hover{background:rgba(0,255,136,0.02)}
.r{text-align:right}.mono{font-family:'JetBrains Mono',monospace}
.sig{display:inline-block;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700;letter-spacing:0.5px}
.sig-b{background:rgba(0,255,136,0.12);color:#00ff88}.sig-h{background:rgba(255,255,0,0.1);color:#ffff00}
.sig-w{background:rgba(77,166,255,0.1);color:#4da6ff}.sig-a{background:rgba(255,68,68,0.1);color:#ff4444}
.sig-lb{background:rgba(102,255,102,0.08);color:#66ff66}.sig-lbr{background:rgba(255,102,0,0.08);color:#ff6600}
.sig-n{background:rgba(255,255,0,0.06);color:#ffff00}
.grn{color:#00ff88}.red{color:#ff4444}.gry{color:#6b6b8a}.blu{color:#4da6ff}
.ab{background:rgba(10,10,20,0.6);border-radius:10px;padding:18px;margin:10px 0;border-left:3px solid #4da6ff;font-size:13px;line-height:1.8;color:#aaaac0}
.ni{padding:18px 0;border-bottom:1px solid rgba(255,255,255,0.03)}.ni:last-child{border-bottom:none}
.ni h4{font-size:15px;font-weight:600;margin-bottom:6px}.ni h4 a{color:#e0e0e0;text-decoration:none;transition:color 0.2s}.ni h4 a:hover{color:#4da6ff}
.ni .an{color:#9999b0;font-size:13px;line-height:1.8;margin:8px 0}
.ni .mt{color:#4a4a6a;font-size:11px}.ni .rm{color:#4da6ff;font-size:12px;text-decoration:none;font-weight:600}.ni .rm:hover{text-decoration:underline}
.gauge{height:8px;border-radius:4px;background:linear-gradient(90deg,#ff0000,#ff6600,#ffff00,#66ff66,#00ff00);position:relative;margin:12px 0}
.gauge .dot{width:14px;height:14px;background:#fff;border-radius:50%;position:absolute;top:-3px;box-shadow:0 0 10px rgba(255,255,255,0.6);transition:left 0.5s}
.sb{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700}
.sb-soc{background:rgba(0,255,136,0.1);color:#00ff88}.sb-bsk{background:rgba(255,102,0,0.1);color:#ff6600}
.sb-ftb{background:rgba(77,166,255,0.1);color:#4da6ff}.sb-hky{background:rgba(255,68,68,0.1);color:#ff4444}.sb-bsb{background:rgba(255,255,0,0.1);color:#ffff00}
.hm{text-align:center;padding:16px 10px;border-radius:12px;min-height:90px;display:flex;flex-direction:column;justify-content:center;transition:transform 0.2s}
.hm:hover{transform:scale(1.03)}
.hm .sn{font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;opacity:0.8}
.hm .sv{font-size:22px;font-weight:800;font-family:'JetBrains Mono',monospace;margin:4px 0}
.lnk{color:#4da6ff;text-decoration:none;font-weight:600;font-size:14px;transition:color 0.2s}.lnk:hover{color:#00ff88}
.st{font-size:20px;font-weight:700;margin-bottom:18px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.05);color:#e0e0e0}
.st em{font-style:normal;color:#00ff88}
footer{text-align:center;padding:40px 20px;color:#3a3a5a;font-size:11px;border-top:1px solid rgba(255,255,255,0.03)}
@media(max-width:768px){.g4{grid-template-columns:repeat(2,1fr)}.hdr h1{font-size:24px}nav .lk a{padding:6px 8px;font-size:11px}}
"""

# ===== HELPERS =====

def nav_html(act):
    pages=[("index.html","Dashboard","dash"),("stocks.html","Stocks","stocks"),("market-news.html","Market News","news"),
           ("global-macro.html","Global Macro","macro"),("sectors.html","Sectors","sectors"),("sports.html","Sports","sports")]
    lk="".join(['<a href="'+u+'" class="'+("on" if k==act else "")+'">'+n+'</a>' for u,n,k in pages])
    return '<nav><div class="c"><a href="index.html" class="logo">📊 MARKET PULSE</a><div class="lk">'+lk+'</div></div></nav>'

def ftr():
    return '<footer><p>Updated '+datetime.now().strftime("%B %d, %Y %I:%M %p UTC")+'</p><p>Data: Yahoo Finance &amp; NewsAPI | Not financial advice.</p><p>Powered by Python &amp; GitHub Actions</p></footer>'

def wrap(title,act,body):
    return '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>'+title+'</title><style>'+CSS+'</style></head><body>'+nav_html(act)+'<div class="pg">'+body+'</div>'+ftr()+'</body></html>'

def fc(p):
    if p is None: return '<span class="gry">N/A</span>'
    c="grn" if p>=0 else "red"
    a="\u25B2" if p>=0 else "\u25BC"
    return '<span class="'+c+' mono" style="font-weight:700">'+a+f" {p:+.2f}%</span>"

def fp(p):
    if p is None: return "N/A"
    if p>9999: return f"{p:,.0f}"
    if p>100: return f"{p:,.1f}"
    if p>1: return f"{p:,.2f}"
    return f"{p:,.4f}"

def fv(v):
    if not v: return "N/A"
    if v>=1e9: return f"{v/1e9:.1f}B"
    if v>=1e6: return f"{v/1e6:.1f}M"
    if v>=1e3: return f"{v/1e3:.0f}K"
    return str(int(v))

def sb(s):
    m={"BUY":"sig-b","HOLD":"sig-h","WATCH":"sig-w","AVOID":"sig-a","BULLISH":"sig-b","BEARISH":"sig-a","NEUTRAL":"sig-n","LEAN BULL":"sig-lb","LEAN BEAR":"sig-lbr"}
    return '<span class="sig '+m.get(s,"sig-n")+'">'+s+'</span>'

# ===== PAGE BUILDERS =====

def build_dash(idx,vix):
    sn,sc,sa,sk,ss=get_sentiment(vix)
    cards=""
    for t,n in INDICES.items():
        d=idx.get(t,{});p=d.get("price");pct=d.get("change_pct")
        bg="rgba(0,255,136,0.04)" if (pct or 0)>=0 else "rgba(255,68,68,0.04)"
        col="#00ff88" if (pct or 0)>=0 else "#ff4444"
        cards+='<div class="cd ic" style="background:'+bg+'"><div class="nm">'+n+'</div><div class="pr" style="color:'+col+'">'+fp(p)+'</div><div class="ch">'+fc(pct)+'</div></div>'
    emoji="\U0001F7E2" if sk in ("extreme_greed","greed") else "\U0001F7E1" if sk=="neutral" else "\U0001F534"
    body='<div class="hdr"><h1>\U0001F4CA MARKET PULSE</h1><p>'+datetime.now().strftime("%A, %B %d, %Y")+'</p></div>'
    body+='<div class="cd" style="border-left:4px solid '+sc+';margin-bottom:28px;padding:28px"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
    body+='<div><p class="gry" style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;font-weight:700">Market Sentiment</p>'
    body+='<h2 style="color:'+sc+';font-size:32px;font-weight:900;margin:6px 0">'+sn+'</h2>'
    body+='<p class="gry">VIX: <span class="mono" style="color:'+sc+'">'+fp(vix)+'</span></p></div>'
    body+='<div style="font-size:56px">'+emoji+'</div></div>'
    body+='<div class="gauge" style="margin-top:16px"><div class="dot" style="left:'+str(ss)+'%"></div></div>'
    body+='<div class="ab" style="margin-top:16px">'+sa+'</div></div>'
    body+='<div class="st">\U0001F3DB\uFE0F <em>Markets</em> &amp; Commodities</div><div class="grid g4">'+cards+'</div>'
    body+='<div class="grid g3">'
    for title,desc,href in [("\U0001F4C8 Stock Dashboard","Watchlist, movers, growth signals, behavior analysis.","stocks.html"),("\U0001F4F0 Market News","Fed, earnings, IPOs, trade, AI \u2014 analyzed.","market-news.html"),("\U0001F30D Global Macro","Commodities, currencies, central banks, geopolitics.","global-macro.html"),("\U0001F3AF Sector Map","S&P 500 sector heatmap and rotation.","sectors.html"),("\u26BD Sports","Soccer, basketball, football, hockey, baseball.","sports.html")]:
        body+='<div class="cd" style="border-left:3px solid #00ff88"><h3>'+title+'</h3><p class="gry" style="font-size:13px">'+desc+'</p><br><a href="'+href+'" class="lnk">Open \u2192</a></div>'
    body+='</div>'
    return wrap("Dashboard","dash",body)

def build_stocks(wl,md):
    wr=""
    for t,n in sorted(WATCHLIST.items(),key=lambda x:wl.get(x[0],{}).get("change_pct",0),reverse=True):
        d=wl.get(t,{});sig,_=get_signal(d);an=analyze_stock(t,d)
        wr+='<tr><td><b>'+n+'</b><br><span class="gry" style="font-size:11px">'+t+'</span></td>'
        wr+='<td class="r mono">$'+fp(d.get("price"))+'</td><td class="r">'+fc(d.get("change_pct"))+'</td>'
        wr+='<td class="r gry mono">'+f'{d.get("mom5",0):+.1f}%</td><td class="r gry mono">'+f'{d.get("mom20",0):+.1f}%</td>'
        wr+='<td class="r gry mono">'+fv(d.get("volume"))+'</td><td>'+sb(sig)+'</td>'
        wr+='<td style="font-size:12px;color:#999;max-width:280px">'+an+'</td></tr>'
    sm=sorted(md.items(),key=lambda x:x[1].get("change_pct",0),reverse=True)
    gr="".join(['<tr><td><b>'+t+'</b></td><td class="r mono">$'+fp(d.get("price"))+'</td><td class="r">'+fc(d.get("change_pct"))+'</td><td class="r gry mono">'+fv(d.get("volume"))+'</td><td class="r gry mono">'+f'{d.get("vol_ratio",1):.1f}x</td></tr>' for t,d in sm[:10]])
    lr="".join(['<tr><td><b>'+t+'</b></td><td class="r mono">$'+fp(d.get("price"))+'</td><td class="r">'+fc(d.get("change_pct"))+'</td><td class="r gry mono">'+fv(d.get("volume"))+'</td><td class="r gry mono">'+f'{d.get("vol_ratio",1):.1f}x</td></tr>' for t,d in sm[-10:][::-1]])
    lo,me,hi=classify_stocks(md)
    def tier(items):
        return "".join(['<tr><td><b>'+t+'</b></td><td class="r mono">$'+fp(d.get("price"))+'</td><td class="r">'+fc(d.get("change_pct"))+'</td><td class="r gry mono">'+f'{d.get("mom5",0):+.1f}%</td><td class="r gry mono">'+f'{d.get("mom20",0):+.1f}%</td><td>'+sb(sig)+'</td><td class="gry" style="font-size:12px">'+note+'</td></tr>' for t,d,sig,sc,note in items])
    beh=analyze_market({},md)
    bh="".join(['<div class="ab">'+b+'</div>' for b in beh])
    body='<div class="hdr"><h1>\U0001F4C8 Stock Dashboard</h1><p>Watchlist, movers, signals &amp; recommendations</p></div>'
    body+='<div class="st">\U0001F440 Your <em>Watchlist</em></div><div class="cd"><div style="overflow-x:auto"><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Today</th><th class="r">5D</th><th class="r">20D</th><th class="r">Volume</th><th>Signal</th><th>Analysis</th></tr>'+wr+'</table></div></div>'
    body+='<div class="grid g2" style="margin-top:24px"><div class="cd"><h3 style="color:#00ff88">\U0001F680 Top 10 Gainers</h3><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Change</th><th class="r">Vol</th><th class="r">Ratio</th></tr>'+gr+'</table></div>'
    body+='<div class="cd"><h3 style="color:#ff4444">\U0001F4C9 Top 10 Losers</h3><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Change</th><th class="r">Vol</th><th class="r">Ratio</th></tr>'+lr+'</table></div></div>'
    body+='<div class="st" style="margin-top:24px">\U0001F3AF Growth <em>Recommendations</em></div><p class="gry" style="font-size:12px;margin-bottom:16px">Momentum + volume analysis. Not financial advice.</p>'
    body+='<div class="cd" style="margin-bottom:16px;border-left:3px solid #ff4444"><h3 style="color:#ff4444">\U0001F525 HIGH GROWTH</h3><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Today</th><th class="r">5D</th><th class="r">20D</th><th>Signal</th><th>Note</th></tr>'+tier(hi)+'</table></div>'
    body+='<div class="cd" style="margin-bottom:16px;border-left:3px solid #ffff00"><h3 style="color:#ffff00">\U0001F4CA MEDIUM GROWTH</h3><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Today</th><th class="r">5D</th><th class="r">20D</th><th>Signal</th><th>Note</th></tr>'+tier(me)+'</table></div>'
    body+='<div class="cd" style="margin-bottom:16px;border-left:3px solid #4da6ff"><h3 style="color:#4da6ff">\U0001F6E1\uFE0F LOW GROWTH / VALUE</h3><table><tr><th>Stock</th><th class="r">Price</th><th class="r">Today</th><th class="r">5D</th><th class="r">20D</th><th>Signal</th><th>Note</th></tr>'+tier(lo)+'</table></div>'
    body+='<div class="st" style="margin-top:24px">\U0001F9E0 Investor <em>Behavior</em></div>'+bh
    return wrap("Stocks","stocks",body)

def build_news(all_news):
    icons={"Fed & Interest Rates":"\U0001F3E6","Earnings Season":"\U0001F4B0","IPOs & M&A":"\U0001F91D","Trade & Tariffs":"\U0001F6A2","AI & Technology":"\U0001F916","Crypto & Digital Assets":"\u20BF","Social Media Buzz":"\U0001F4F1"}
    secs=""
    for cat,articles in all_news.items():
        items=""
        for a in articles[:5]:
            an=analyze_news_item(a)
            items+='<div class="ni"><h4><a href="'+a["url"]+'" target="_blank">'+a["title"]+'</a></h4>'
            items+='<div class="an">'+an+'</div>'
            items+='<div class="mt">'+a["source"]+' &bull; '+a.get("published","")[:10]+' &middot; <a href="'+a["url"]+'" target="_blank" class="rm">Read full story \u2192</a></div></div>'
        if not items: items='<p class="gry">No articles found.</p>'
        secs+='<div class="cd" style="margin-bottom:20px"><h3>'+icons.get(cat,"")+' '+cat+'</h3>'+items+'</div>'
    return wrap("Market News","news",'<div class="hdr"><h1>\U0001F4F0 Market-Moving News</h1><p>Every headline analyzed for investor impact</p></div>'+secs)

def build_macro(gnews,idx):
    def cc(name,emoji,d,analysis):
        pct=d.get("change_pct",0);bg="rgba(0,255,136,0.04)" if pct>=0 else "rgba(255,68,68,0.04)"
        col="#00ff88" if pct>=0 else "#ff4444"
        return '<div class="cd" style="background:'+bg+'"><h3>'+emoji+' '+name+'</h3><div style="font-size:28px;font-weight:800;margin:10px 0;font-family:JetBrains Mono,monospace;color:'+col+'">'+fp(d.get("price"))+'</div><div style="margin-bottom:12px">'+fc(pct)+'</div><div class="ab">'+analysis+'</div></div>'
    oil=idx.get("CL=F",{});gold=idx.get("GC=F",{});btc=idx.get("BTC-USD",{});dxy=idx.get("DX-Y.NYB",{});yld=idx.get("^TNX",{})
    oa="Oil "+("rising" if (oil.get("change_pct") or 0)>0 else "falling")+". "+("Supply concerns. Energy stocks benefit, inflation builds." if (oil.get("change_pct") or 0)>0 else "Demand fears. Airlines benefit, signals cooling.")
    ga="Gold "+("bid" if (gold.get("change_pct") or 0)>0 else "offered")+". "+("Safe-haven demand rising." if (gold.get("change_pct") or 0)>0 else "Risk appetite returning.")
    ba="Bitcoin "+("pumping" if (btc.get("change_pct") or 0)>0 else "dumping")+". "+("Risk-on. Equities likely follow 24-48h." if (btc.get("change_pct") or 0)>0 else "Risk-off warning.")
    da="Dollar "+("strong" if (dxy.get("change_pct") or 0)>0 else "weak")+". "+("Headwind for multinationals." if (dxy.get("change_pct") or 0)>0 else "Tailwind for commodities.")
    ya="10Y at "+fp(yld.get("price"))+"%. "+("Rising = tightening. Growth pressured." if (yld.get("change_pct") or 0)>0 else "Falling = easing. Growth stocks rally.")
    ni=""
    for a in gnews[:8]:
        an=analyze_news_item(a)
        ni+='<div class="ni"><h4><a href="'+a["url"]+'" target="_blank">'+a["title"]+'</a></h4><div class="an">'+an+'</div><div class="mt">'+a["source"]+' &middot; <a href="'+a["url"]+'" target="_blank" class="rm">Read more \u2192</a></div></div>'
    body='<div class="hdr"><h1>\U0001F30D Global Macro</h1><p>Macro forces shaping markets today</p></div>'
    body+='<div class="st">\U0001F4E6 <em>Commodities</em> &amp; Crypto</div><div class="grid g2">'+cc("Crude Oil","\U0001F6E2\uFE0F",oil,oa)+cc("Gold","\U0001F947",gold,ga)+cc("Bitcoin","\u20BF",btc,ba)+cc("US Dollar","\U0001F4B5",dxy,da)+'</div>'
    body+='<div class="st">\U0001F3E6 <em>Central Bank</em> Watch</div><div class="cd"><div class="ab">'+ya+'</div></div>'
    body+='<div class="st" style="margin-top:24px">\U0001F310 <em>Geopolitical</em> Headlines</div><div class="cd">'+(ni if ni else '<p class="gry">No news available.</p>')+'</div>'
    return wrap("Global Macro","macro",body)

def build_sectors(sd):
    cells=""
    for t,n in SECTORS.items():
        d=sd.get(t,{});pct=d.get("change_pct",0)
        if pct>1.5: bg="rgba(0,255,136,0.2)";tc="#00ff88"
        elif pct>0.5: bg="rgba(0,255,136,0.1)";tc="#66ff66"
        elif pct>-0.5: bg="rgba(255,255,0,0.06)";tc="#ffff00"
        elif pct>-1.5: bg="rgba(255,68,68,0.1)";tc="#ff6600"
        else: bg="rgba(255,68,68,0.2)";tc="#ff4444"
        cells+='<div class="hm" style="background:'+bg+'"><div class="sn" style="color:'+tc+'">'+n+'</div><div class="sv" style="color:'+tc+'">'+f'{pct:+.2f}%</div><div class="gry" style="font-size:11px">'+t+'</div></div>'
    srt=sorted(sd.items(),key=lambda x:x[1].get("change_pct",0),reverse=True)
    top3=", ".join([SECTORS.get(t,t)+f" ({d.get('change_pct',0):+.1f}%)" for t,d in srt[:3]])
    bot3=", ".join([SECTORS.get(t,t)+f" ({d.get('change_pct',0):+.1f}%)" for t,d in srt[-3:]])
    tbl="".join(['<tr><td><b>'+SECTORS.get(t,t)+'</b></td><td class="r">'+fc(d.get("change_pct"))+'</td><td class="r gry mono">'+f'{d.get("mom5",0):+.1f}%</td><td class="r gry mono">'+f'{d.get("mom20",0):+.1f}%</td></tr>' for t,d in srt])
    body='<div class="hdr"><h1>\U0001F3AF Sector Map</h1><p>S&amp;P 500 sector performance heatmap</p></div>'
    body+='<div class="st">\U0001F5FA\uFE0F Sector <em>Heatmap</em></div><div class="grid g4" style="margin-bottom:16px">'+cells+'</div>'
    body+='<div class="ab"><b>Leading:</b> '+top3+'. <b>Lagging:</b> '+bot3+'.</div>'
    body+='<div class="st" style="margin-top:28px">\U0001F4CA Sector <em>Comparison</em></div><div class="cd"><table><tr><th>Sector</th><th class="r">Today</th><th class="r">5D</th><th class="r">20D</th></tr>'+tbl+'</table></div>'
    return wrap("Sectors","sectors",body)

def build_sports(sn):
    emojis={"Soccer":"\u26BD","Basketball":"\U0001F3C0","Football":"\U0001F3C8","Hockey":"\U0001F3D2","Baseball":"\u26BE"}
    badges={"Soccer":"sb-soc","Basketball":"sb-bsk","Football":"sb-ftb","Hockey":"sb-hky","Baseball":"sb-bsb"}
    secs=""
    for sport,articles in sn.items():
        items=""
        for a in articles[:6]:
            items+='<div class="ni"><h4><a href="'+a["url"]+'" target="_blank">'+a["title"]+'</a></h4><div class="mt">'+a["source"]+' &bull; '+a.get("published","")[:10]+' &middot; <a href="'+a["url"]+'" target="_blank" class="rm">Full story \u2192</a></div></div>'
        if not items: items='<p class="gry">No headlines.</p>'
        secs+='<div class="cd" style="margin-bottom:16px"><span class="sb '+badges.get(sport,"")+'">'+emojis.get(sport,"")+' '+sport+'</span>'+items+'</div>'
    return wrap("Sports","sports",'<div class="hdr"><h1>\u26BD Sports Center</h1><p>Scores &amp; headlines across all major leagues</p></div>'+secs)

# ===== MAIN =====

def main():
    print("="*60+"\n\U0001F4CA MARKET PULSE \u2014 Generating...\n"+"="*60)
    print("[1/6] Market indices...")
    idx=fetch_stock_data(list(INDICES.keys()));print(f"  {len(idx)} indices")
    print("[2/6] Stocks...")
    wl=fetch_stock_data(list(WATCHLIST.keys()));md=fetch_stock_data(MOVERS);print(f"  {len(wl)} watchlist, {len(md)} movers")
    print("[3/6] Sectors...")
    sd=fetch_stock_data(list(SECTORS.keys()));print(f"  {len(sd)} sectors")
    print("[4/6] Market news...")
    an={}
    for cat,q in NEWS_QUERIES.items():
        an[cat]=fetch_news(q,5);print(f"  {cat}: {len(an[cat])}")
    print("[5/6] Global & sports...")
    gn=fetch_news("geopolitics OR oil prices OR China economy OR G7 OR NATO OR Bank of Canada",8)
    sn={}
    for sport,q in SPORTS_QUERIES.items():
        sn[sport]=fetch_news(q,6);print(f"  {sport}: {len(sn[sport])}")
    print("[6/6] Building pages...")
    vix=idx.get("^VIX",{}).get("price")
    pages={"index.html":build_dash(idx,vix),"stocks.html":build_stocks(wl,md),
           "market-news.html":build_news(an),"global-macro.html":build_macro(gn,idx),
           "sectors.html":build_sectors(sd),"sports.html":build_sports(sn)}
    for fn,html in pages.items():
        with open(fn,"w",encoding="utf-8") as out: out.write(html)
        print(f"  {fn} ({len(html):,} chars)")
    with open("newsletter.html","w",encoding="utf-8") as out: out.write(pages["index.html"])
    print("\nDone!")

if __name__=="__main__":
    main()
