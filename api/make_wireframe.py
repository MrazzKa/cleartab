"""Write web/wireframes/results.html: a static, grayscale, low-fidelity wireframe filled with 5 real results
from GET /search (in-process). Usage: python -m api.make_wireframe [query] [plan] [zip]"""
import html
import sys

from fastapi.testclient import TestClient

from api.main import app
from pipeline.common import ROOT, now_utc


def fmt(x) -> str:
    return "Not published" if x is None else f"${x:,.0f}"


def neg_cell(n) -> str:
    if not n:
        return ""
    k = n["kind"]
    if k == "negotiated rate":
        rng = f"<div class=s>median of {n['rates_count']}, {fmt(n['min'])} to {fmt(n['max'])}</div>" if n["rates_count"] > 1 else ""
        return f"<b>{fmt(n['median'])}</b><div class=s>negotiated rate, fixed dollar amount</div>{rng}"
    if k == "allowed amount estimate":
        return (f"About {fmt(n['median'])}<div class=s>allowed amount estimate ({html.escape(n['methodology'])}), "
                f"typical {fmt(n['p10'])} to {fmt(n['p90'])}</div>")
    if k == "not a dollar amount":
        return f"<div class=s>Rate is {html.escape(n['methodology'])}, not a dollar amount. Ask the hospital.</div>"
    return "<div class=s>Plan not matched: no rate in this file for your plan.</div>"


def main() -> None:
    q, plan, zipc = (sys.argv[1:4] + ["knee mri", "UnitedHealthcare", "85006"][len(sys.argv[1:4]):])
    with TestClient(app) as c:
        d = c.get("/search", params={"q": q, "plan": plan, "zip": zipc}).json()
    res = d["results"][:5]
    top = res[0]
    rows = []
    for i, r in enumerate(res):
        p = r["provenance"]
        rows.append(f"""
  <div class=card>
    <div class=h>{i + 1}. {html.escape(r['hospital'])} {'<span class=tag>Lowest</span>' if i == 0 else ''}</div>
    <div class=s>{html.escape(r['city'])} - {r['distance_miles']} miles (straight line from your ZIP)</div>
    <div class=grid>
      <div><div class=lab>Your plan</div>{neg_cell(r['negotiated'])}</div>
      <div><div class=lab>Cash price</div><b>{fmt(r['cash']['amount'])}</b><div class=s>discounted cash price</div></div>
      <div><div class=lab>List price</div>{fmt(r['gross']['amount'])}<div class=s>gross charge</div></div>
    </div>
    <div class=s>Data: <b>{r['completeness']['label'].title()}</b> ({r['completeness']['score']}/100) -
      <details><summary>Where this number comes from</summary>
      File: <a href="{html.escape(p['source_url'])}">{html.escape(p['source_url'][:70])}...</a><br>
      Downloaded {p['downloaded_at'][:10]}; file dated {p['file_last_updated']}; version {p['file_version']}</details></div>
    <button>Prepare a call</button>
  </div>""")
    neg = top["negotiated"] or {}
    rng = (f"{fmt(neg.get('min'))} - {fmt(neg.get('max'))}" if neg.get("kind") == "negotiated rate"
           else "not published as a dollar amount")
    missing = "".join(f"<li>{html.escape(m['hospital'])} ({html.escape(m['city'] or '')}): {html.escape(m['status'])}</li>"
                      for m in d["not_published"][:6])
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClearTab results wireframe</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 0 auto; max-width: 960px; padding: 16px; color: #222; background: #fff; }}
 .wf {{ border: 3px dashed #777; padding: 8px; text-align: center; font-weight: 700; letter-spacing: .1em; color: #555; }}
 form, .card, .box {{ border: 1px solid #999; border-radius: 6px; padding: 12px; margin: 12px 0; background: #f4f4f4; }}
 input, select, button {{ font-size: 16px; min-height: 44px; margin: 4px 0; width: 100%; box-sizing: border-box; }}
 .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 8px 0; }}
 .lab {{ font-size: 12px; text-transform: uppercase; color: #555; }}
 .s {{ font-size: 13px; color: #555; }} .h {{ font-weight: 700; font-size: 17px; }}
 .tag {{ border: 1px solid #333; padding: 0 6px; font-size: 12px; border-radius: 3px; }}
 pre {{ white-space: pre-wrap; background: #fff; border: 1px solid #999; padding: 8px; font-size: 14px; }}
 @media (max-width: 480px) {{ .grid {{ grid-template-columns: 1fr; }} }}
 @media (min-width: 800px) {{ .layout {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }} }}
</style></head><body>
<div class=wf>WIREFRAME - LOW FIDELITY - GRAYSCALE - NOT THE FINAL DESIGN</div>
<form><label>Procedure<input value="{html.escape(q)}"></label>
<label>Plan<select><option>{html.escape(d['plan'])}</option><option>No insurance (cash price)</option></select></label>
<label>ZIP code<input value="{html.escape(zipc)}" inputmode="numeric"></label><button type=button>Search</button></form>
<div class=layout><main>
<h2>{html.escape(d['procedure']['plain_name'])} <span class=s>(CPT {d['procedure']['code']}) - {d['metro']} area - sorted by lowest price for your plan</span></h2>
<div class=s>Sort: [Lowest price] [Nearest]</div>
{''.join(rows)}
<div class=box><b>Hospitals near you without usable prices</b><ul>{missing}</ul>
<div class=s>This is about the price file only, not about the quality of care.</div></div>
</main><aside>
<div class=box><b>What these numbers mean</b><p>{html.escape(d['explainer'])}</p>
<p class=s>Financial help: [hospital financial assistance link] - [what ClearTab stores: nothing]</p></div>
<div class=box><b>Call summary (opened from result 1)</b><pre>
Calling: {html.escape(top['hospital'])}   {html.escape(top['phone'] or 'phone not found')}
Procedure: {html.escape(d['procedure']['plain_name'])} (CPT {d['procedure']['code']})
Published cash price: {fmt(top['cash']['amount'])}   (file dated {top['provenance']['file_last_updated']})
Published negotiated range for {html.escape(d['plan'])}: {rng}
Questions to ask:
 1. What is the all-in estimate for CPT {d['procedure']['code']}, including every bill I will get?
 2. Is the doctor's (physician) fee included, or billed separately?
 3. Is this cash price available to me, and what do I need to do to get it?
</pre><button>Copy</button> <button>Print</button></div>
</aside></div>
<p class=s>Generated {now_utc()} from GET /search?q={html.escape(q)}&amp;plan={html.escape(plan)}&amp;zip={zipc} on the
local ClearTab database (api/make_wireframe.py). Real published figures; provisional payer mapping.</p>
</body></html>"""
    out = ROOT / "web" / "wireframes" / "results.html"
    out.write_text(page)
    print("wrote", out, len(res), "results")


if __name__ == "__main__":
    main()
