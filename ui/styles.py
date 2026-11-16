from config import NAVY, TEAL, BG

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Material+Symbols+Rounded');
html,body,[class*="css"],.stApp{font-family:'Plus Jakarta Sans',sans-serif}
#MainMenu,header,footer{visibility:hidden}
.stApp{background:$BG}
.block-container{padding:1.4rem 2.2rem;max-width:1300px}
section[data-testid=stSidebar]{background:$NAVY}
section[data-testid=stSidebar] *{color:#fff}
.ms{font-family:'Material Symbols Rounded';font-size:26px;vertical-align:middle;font-weight:400}
.stButton>button{background:$TEAL;color:#fff;border:0;border-radius:8px;font-weight:600;padding:.45rem 1rem}
.stButton>button:hover{background:#14544A;color:#fff}
section[data-testid=stSidebar] .stButton>button{background:transparent;justify-content:flex-start;width:100%;font-weight:500}
section[data-testid=stSidebar] .stButton>button:hover{background:rgba(255,255,255,.1)}
[class*="st-key-card"],.st-key-loginwrap{background:#fff;border-radius:14px;padding:1.1rem 1.3rem;box-shadow:0 2px 12px rgba(15,42,61,.07)}
.st-key-loginwrap{padding:0;overflow:hidden}
.kpi{background:#fff;border-radius:14px;padding:16px;display:flex;gap:14px;align-items:center;box-shadow:0 2px 12px rgba(15,42,61,.07)}
.kpi .ic{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.kpi small{color:#5b6b78;font-size:13px}.kpi b{font-size:26px;display:block}
.pill{padding:3px 12px;border-radius:99px;font-size:12px;font-weight:600}
.High{background:#FDE3E1;color:#D9342B}.Medium{background:#FFE9CF;color:#D97A00}.Low{background:#DDF3E6;color:#2E8B57}
.av{display:inline-flex;width:32px;height:32px;border-radius:50%;background:#C9E3DE;color:$TEAL;font-weight:700;align-items:center;justify-content:center;margin-right:10px;font-size:12px}
.th{color:#1c2b36;font-weight:700;font-size:12px;border-bottom:1px solid #e6eef0;padding-bottom:8px}
.tl{border-left:2px solid $TEAL;margin-left:8px;padding-left:22px}
.tl .it{position:relative;margin-bottom:12px;font-size:13px;color:#1c2b36}
.tl .it:before{content:"";position:absolute;left:-29px;top:6px;width:10px;height:10px;border-radius:50%;background:$TEAL}
.badge{background:$TEAL;color:#fff;border-radius:99px;padding:1px 10px;font-size:11px;margin-left:8px}
.ok{background:#DCF1EC;border-radius:10px;padding:12px;text-align:center;color:#14544A;font-weight:600}
.chk{display:flex;gap:10px;margin:12px 0;font-size:14px;color:#1c2b36}.chk .ms{color:#2E9E7F}
h1.t{font-size:26px;font-weight:800;color:#12222d;margin:0}
"""
for k, v in {"$NAVY": NAVY, "$TEAL": TEAL, "$BG": BG}.items():
    CSS = CSS.replace(k, v)
