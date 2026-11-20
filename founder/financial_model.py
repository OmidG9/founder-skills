#!/usr/bin/env python3
"""مدل مالی سناریومحور آتیوار — استاندارد پایتون، بدون شبکه.

سه سناریو (پایه / استرس / شدید) را ماه‌به‌ماه برای ۳۶ ماه شبیه‌سازی می‌کند:
جذب ناخالص از بودجه بازاریابی و CAC، ریزش ماهانه، درآمد بر پایه حساب فعال،
هزینه ثابت پله‌ای، سهم درآمد قبل از مجوز، و ترانش‌های سرمایه.

    python financial_model.py
    python financial_model.py --out founder/financial-model.md --csv founder/financial-model.csv
"""

import argparse
import csv
import os

MONTHS = 36


def series(value, months=MONTHS):
    if isinstance(value, (int, float)):
        return [float(value)] * months
    out = [float(v) for v in value]
    if len(out) < months:
        out += [out[-1]] * (months - len(out))
    return out[:months]


# ── سناریوها ────────────────────────────────────────────────────────────────────
# همه مبالغ به تومان. marketing و fixed ماهانه‌اند.
SCENARIOS = {
    "base": {
        "label": "پایه (پلن دک)",
        "cac": 10_000,
        "churn": 0.05,
        "arpu": 14_000,
        "variable_pct": 0.15,
        "marketing": [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2,
                      0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2,
                      0.2, 0.2, 0.2, 0.2, 0.2, 0.2] + [0.2] * 12,
        "marketing_unit": "میلیارد تومان در ماه",
        "fixed": [2.58] * 12 + [3.2] * 12 + [4.0] * 12,
        "license_month": 1,
        "pre_license_share": 1.0,
        "tranches": {1: 15.0, 4: 15.0, 7: 20.0},
        "reach_cap": 5_000_000,
    },
    "stress": {
        "label": "استرس (نصف پلن، CAC ۱٫۵ برابر، ریزش ۸٪)",
        "cac": 15_000,
        "churn": 0.08,
        "arpu": 14_000,
        "variable_pct": 0.15,
        "marketing": [0.5] * 18 + [0.3] * 18,
        "marketing_unit": "میلیارد تومان در ماه",
        "fixed": [2.58] * 12 + [3.2] * 12 + [4.0] * 12,
        "license_month": 7,
        "pre_license_share": 0.6,
        "tranches": {1: 15.0, 7: 15.0},
        "reach_cap": 5_000_000,
    },
    "severe": {
        "label": "شدید (۲۵٪ پلن، CAC ۳ برابر، ریزش ۱۲٪، مجوز ماه ۱۳)",
        "cac": 30_000,
        "churn": 0.12,
        "arpu": 14_000,
        "variable_pct": 0.15,
        "marketing": [0.2] * 12 + [0.1] * 24,
        "marketing_unit": "میلیارد تومان در ماه",
        "fixed": [2.58] * 6 + [2.0] * 6 + [1.8] * 24,
        "license_month": 13,
        "pre_license_share": 0.6,
        "tranches": {1: 15.0},
        "reach_cap": 5_000_000,
    },
}

# مبالغ در جدول‌ها به میلیارد تومان‌اند
B = 1_000_000_000


def run(name):
    s = SCENARIOS[name]
    marketing = series(s["marketing"])
    fixed = series(s["fixed"])
    active = 0.0
    op_cum = 0.0
    cash = 0.0
    invested = 0.0
    payback = None
    gap = None
    rows = []
    for m in range(1, MONTHS + 1):
        budget = marketing[m - 1] * B
        adds = min(budget / s["cac"], max(0.0, s["reach_cap"] - active))
        spend = adds * s["cac"]
        churned = active * s["churn"]
        active = active - churned + adds
        share = 1.0 if m >= s["license_month"] else s["pre_license_share"]
        revenue = active * s["arpu"] * share
        variable = revenue * s["variable_pct"]
        ebitda = revenue - variable - fixed[m - 1] * B - spend
        tranche = s["tranches"].get(m, 0.0) * B
        invested += tranche
        op_cum += ebitda
        cash += tranche + ebitda
        if payback is None and invested > 0 and op_cum >= invested:
            payback = m
        if gap is None and cash < 0:
            gap = m
        rows.append({
            "month": m, "adds": adds, "churned": churned, "active": active,
            "revenue": revenue, "variable": variable, "fixed": fixed[m - 1] * B,
            "marketing": spend, "ebitda": ebitda, "tranche": tranche,
            "op_cum": op_cum, "cash": cash,
        })
    return {"name": name, "label": s["label"], "spec": s, "rows": rows,
            "payback": payback, "gap": gap, "invested": invested}


def at(rows, month, key):
    return rows[month - 1][key]


def money(x):
    """میلیارد تومان با یک رقم اعشار."""
    return f"{x / B:,.1f}"


def pct(x):
    return f"{x * 100:,.0f}%"


def build_report(runs):
    L = []
    L.append("# مدل مالی سناریومحور آتیوار")
    L.append("")
    L.append("**روش:** شبیه‌سازی ماه‌به‌ماه ۳۶ ماهه با جذب ناخالص از بودجه بازاریابی و CAC، "
             "ریزش ماهانه، درآمد بر پایه حساب فعال، هزینه ثابت پله‌ای، سهم درآمد قبل از مجوز، "
             "و ترانش‌های سرمایه. همه مبالغ به تومان محاسبه و در جدول‌ها به **میلیارد تومان** نمایش داده شده‌اند.")
    L.append("")
    L.append("> این مدل برای تست انسجام و ریسک است، نه پیش‌بینی. هیچ عددی از آینده خبر ندارد؛ "
             "همه از فرض‌های جدول زیر می‌آیند و هر فرض قابل تغییر است.")
    L.append("")

    # assumptions
    L.append("## ۱. فرض‌های سه سناریو")
    L.append("")
    L.append("| فرض | پایه | استرس | شدید |")
    L.append("| --- | ---: | ---: | ---: |")
    L.append("| CAC هر حساب فعال | ۱۰٬۰۰۰ تومان | ۱۵٬۰۰۰ | ۳۰٬۰۰۰ |")
    L.append("| ریزش ماهانه | ۵٪ | ۸٪ | ۱۲٪ |")
    L.append("| ARPU ماهانه | ۱۴٬۰۰۰ | ۱۴٬۰۰۰ | ۱۴٬۰۰۰ |")
    L.append("| حاشیه متغیر | ۸۵٪ | ۸۵٪ | ۸۵٪ |")
    L.append("| ماه دریافت مجوز | ۱ | ۷ | ۱۳ |")
    L.append("| سهم درآمد قبل از مجوز | ۱۰۰٪ | ۶۰٪ | ۶۰٪ |")
    L.append("| ترانش سرمایه (میلیارد) | ۱۵ + ۱۵ + ۲۰ | ۱۵ + ۱۵ | ۱۵ |")
    L.append("| بودجه بازاریابی ۱۸ ماه (میلیارد) | ۱۰٬۰ | ۹٬۰ | ۳٬۰ |")
    L.append("")
    L.append("**هزینه ثابت ماهانه:** سال ۱: ۲٬۵۸ میلیارد (۳۱ میلیارد در سال)؛ سال ۲: ۳٬۲؛ سال ۳: ۴٬۰. "
             "در سناریوی شدید، بعد از ماه ۶ به ۲٬۰ و بعد از ماه ۱۲ به ۱٬۸ کاهش می‌یابد (مدیریت بحران).")
    L.append("")

    # summary
    L.append("## ۲. خلاصه مقایسه")
    L.append("")
    L.append("| شاخص | پایه | استرس | شدید |")
    L.append("| --- | ---: | ---: | ---: |")
    L.append("| حساب فعال ماه ۹ | " + " | ".join(f"{at(r['rows'], 9, 'active'):,.0f}" for r in runs) + " |")
    L.append("| درآمد ماه ۹ (میلیارد) | " + " | ".join(money(at(r['rows'], 9, 'revenue')) for r in runs) + " |")
    L.append("| درآمد ماه ۱۲ (میلیارد) | " + " | ".join(money(at(r['rows'], 12, 'revenue')) for r in runs) + " |")
    L.append("| EBITDA ماه ۹ (میلیارد) | " + " | ".join(money(at(r['rows'], 9, 'ebitda')) for r in runs) + " |")
    L.append("| EBITDA ماه ۱۲ (میلیارد) | " + " | ".join(money(at(r['rows'], 12, 'ebitda')) for r in runs) + " |")
    L.append("| جریان نقد عملیاتی تجمعی ماه ۱۲ (میلیارد) | " + " | ".join(money(at(r['rows'], 12, 'op_cum')) for r in runs) + " |")
    L.append("| جریان نقد عملیاتی تجمعی ماه ۲۴ (میلیارد) | " + " | ".join(money(at(r['rows'], 24, 'op_cum')) for r in runs) + " |")
    L.append("| جریان نقد عملیاتی تجمعی ماه ۳۶ (میلیارد) | " + " | ".join(money(at(r['rows'], 36, 'op_cum')) for r in runs) + " |")
    L.append("| موجودی نقد ماه ۱۲ (میلیارد) | " + " | ".join(money(at(r['rows'], 12, 'cash')) for r in runs) + " |")
    L.append("| موجودی نقد ماه ۳۶ (میلیارد) | " + " | ".join(money(at(r['rows'], 36, 'cash')) for r in runs) + " |")
    L.append("| بازگشت سرمایه | " + " | ".join(f"ماه {r['payback']}" if r['payback'] else "بعد از ۳۶ ماه" for r in runs) + " |")
    L.append("| ماه اتمام نقد | " + " | ".join(f"ماه {r['gap']}" if r['gap'] else "نمی‌رسد" for r in runs) + " |")
    L.append("")
    L.append("**هدف خود دک برای ماه ۱۲: ۱۴ میلیارد تومان در ماه.** مدل پایه به ۹٬۰ می‌رسد؛ "
             "یعنی هدف ماه ۱۲ با بودجه بازاریابی ۱۰ میلیاردی تأمین نمی‌شود.")
    L.append("")

    # base detail
    base = runs[0]
    L.append("## ۳. سناریوی پایه، ماه‌به‌ماه")
    L.append("")
    L.append("| ماه | جذب | ریزش | فعال | درآمد | EBITDA | نقد تجمعی |")
    L.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in base["rows"]:
        L.append("| {m} | {a:,.0f} | {c:,.0f} | {act:,.0f} | {rev} | {eb} | {cash} |".format(
            m=row["month"], a=row["adds"], c=row["churned"], act=row["active"],
            rev=money(row["revenue"]), eb=money(row["ebitda"]), cash=money(row["cash"])))
    L.append("")

    # stress and severe quarterly
    for r in runs[1:]:
        L.append(f"## ۴. سناریوی {r['label']}، هر سه ماه")
        L.append("")
        L.append("| ماه | فعال | درآمد | EBITDA | نقد تجمعی |")
        L.append("| ---: | ---: | ---: | ---: | ---: |")
        for row in r["rows"]:
            if row["month"] % 3 == 0:
                L.append("| {m} | {act:,.0f} | {rev} | {eb} | {cash} |".format(
                    m=row["month"], act=row["active"], rev=money(row["revenue"]),
                    eb=money(row["ebitda"]), cash=money(row["cash"])))
        L.append("")

    # findings
    L.append("## ۵. پنج یافته")
    L.append("")
    b9 = at(base["rows"], 9, "active")
    L.append(f"1. **هدف ماه ۹ شدنی است، ولی هدف ماه ۱۲ نه.** در سناریوی پایه، ماه ۹ به "
             f"{b9:,.0f} حساب فعال و {money(at(base['rows'], 9, 'revenue'))} میلیارد درآمد می‌رسد "
             f"(نزدیک به هدف ۸ میلیارد). اما ماه ۱۲ فقط {money(at(base['rows'], 12, 'revenue'))} میلیارد است، "
             f"نه ۱۴ میلیارد. برای ۱ میلیون حساب در ماه ۱۲ با ریزش ۵٪، حدود ۱۶۵ هزار حساب جدید در ماه لازم است "
             f"— یعنی ~۱٬۶ میلیارد بازاریابی در ماه، در حالی که بودجه ~۰٬۴ میلیارد است. **کمبود ~۳٬۸ میلیارد.**")
    L.append(f"2. **بازگشت سرمایه در ماه {base['payback']} است، نه ماه ۹.** "
             f"جریان نقد عملیاتی تجمعی ماه ۱۲ حدود {money(at(base['rows'], 12, 'op_cum'))} میلیارد است "
             f"و با ۵۰ میلیارد سرمایه، تازه در ماه {base['payback']} جبران می‌شود. "
             f"دک عدد ۶۱ میلیارد برای ماه ۹ را گفته بود؛ مدل با همان رمپ به "
             f"{money(at(base['rows'], 9, 'op_cum'))} میلیارد می‌رسد.")
    L.append(f"3. **در سناریوی استرس، کسب‌وکار در ماه ۱۲ تقریباً سربه‌سر است "
             f"({money(at(runs[1]['rows'], 12, 'ebitda'))} میلیارد EBITDA) ولی "
             f"جریان نقد تجمعی {money(at(runs[1]['rows'], 12, 'op_cum'))} میلیارد است.** "
             f"با ۳۰ میلیارد ترانش، تا ماه ۳۶ فقط {money(at(runs[1]['rows'], 36, 'cash'))} میلیارد نقد می‌ماند؛ "
             f"یعنی بدون راند دوم، شرکت زنده می‌ماند ولی سرمایه برنمی‌گردد.")
    L.append(f"4. **در سناریوی شدید، نقد در ماه {runs[2]['gap']} تمام می‌شود.** "
             f"با CAC ۳۰ هزار و ریزش ۱۲٪، حتی ۱۵ میلیارد هم تا سال اول کافی نیست؛ "
             f"زیان تجمعی تا ماه ۳۶ به {money(at(runs[2]['rows'], 36, 'op_cum'))} میلیارد می‌رسد. "
             f"این سناریو نیاز به تصمیم سخت دارد: توقف، واگذاری، یا بازتعریف B2B-only.")
    L.append("5. **حساس‌ترین متغیر، CAC است، نه ARPU.** با CAC ۱۵ هزار، حساب‌های ماه ۹ به "
             f"{at(runs[1]['rows'], 9, 'active'):,.0f} می‌رسد (۳۷٪ پلن)؛ با CAC ۳۰ هزار، به "
             f"{at(runs[2]['rows'], 9, 'active'):,.0f} (۶٪ پلن). هر ۵ هزار تومان افزایش CAC، "
             "حدود یک‌سوم از پلن را می‌برد. پس اول اعتماد و کانال را بساز، بعد بودجه را زیاد کن.")
    L.append("")
    L.append("## ۶. چه چیزی این مدل را عوض می‌کند")
    L.append("")
    L.append("| اقدام | اثر | کدام سناریو را نجات می‌دهد |")
    L.append("| --- | --- | --- |")
    L.append("| LOI و قرارداد کانال | CAC را از ۱۵–۳۰ به ۸–۱۲ می‌آورد | استرس |")
    L.append("| تحویل ۱۰۰ گرم و اعتمادسازی | ریزش را از ۸–۱۲٪ به ۴–۵٪ می‌آورد | استرس و شدید |")
    L.append("| قیمت واحد و شفاف | حاشیه را از ۸۵٪ پایین نمی‌آورد؛ نرخ تبدیل را بالا می‌برد | پایه |")
    L.append("| ترانش سوم مشروط | ریسک را از ۵۰ به ۳۰ میلیارد کم می‌کند | پایه |")
    L.append("| مدل B2B-only بدون مجوز | سربه‌سر را پایین می‌آورد؛ درآمد را کم می‌کند | شدید |")
    L.append("")
    L.append("## ۷. فایل داده")
    L.append("")
    L.append("`founder/financial-model.csv` — ۱۰۸ ردیف (۳ سناریو × ۳۶ ماه) با همه ستون‌ها.")
    L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join("founder", "financial-model.md"))
    ap.add_argument("--csv", default=os.path.join("founder", "financial-model.csv"))
    args = ap.parse_args()
    runs = [run(n) for n in ("base", "stress", "severe")]
    text = build_report(runs)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(args.csv, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "month", "adds", "churned", "active", "revenue",
                    "variable", "fixed", "marketing", "ebitda", "tranche", "op_cum", "cash"])
        for r in runs:
            for row in r["rows"]:
                w.writerow([r["name"]] + [row[k] for k in
                           ("month", "adds", "churned", "active", "revenue", "variable",
                            "fixed", "marketing", "ebitda", "tranche", "op_cum", "cash")])
    print("wrote", args.out, "and", args.csv)
    print()
    for r in runs:
        print(f"{r['name']}: M9 active={at(r['rows'],9,'active'):,.0f} | "
              f"M12 revenue={money(at(r['rows'],12,'revenue'))}B | "
              f"M12 EBITDA={money(at(r['rows'],12,'ebitda'))}B | "
              f"payback={r['payback']} | cash gap={r['gap']}")


if __name__ == "__main__":
    main()
