"""pptkit: every command prints a short result meant to be read by a model, not a human dashboard."""
import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd
import yaml


def fmt_s(s, f):
    return "  ".join(f"{k}={'n/a' if pd.isna(v) else format(v, f)}" for k, v in s.items())


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp949
    ap = argparse.ArgumentParser(prog="pptkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("profile", help="who the user is (~/.pptkit/profile.yaml)")
    p.add_argument("action", choices=["show", "set", "reset"], nargs="?", default="show")
    p.add_argument("pairs", nargs="*", help="key=value (lists comma-separated)")

    p = sub.add_parser("tone", help="profile x brief -> tone.yaml")
    p.add_argument("--brief", default="brief.yaml")
    p.add_argument("-o", "--out")

    p = sub.add_parser("plan", help="purpose -> storyline options -> deck.md skeleton + questions for the user")
    p.add_argument("what", nargs="?", help="nothing | a purpose (pitch) | a storyline id (pitch/vc-seed)")
    p.add_argument("-o", "--out", help="write the deck.md skeleton for a storyline id")

    p = sub.add_parser("icons", help="line icons for pillars/process/kpi/points (`icon: rocket`)")
    p.add_argument("query", nargs="?", help="filter, e.g. chart")

    p = sub.add_parser("data", help="summarize a csv/xlsx")
    p.add_argument("file")

    p = sub.add_parser("pivot", help="pivot a csv/xlsx")
    p.add_argument("file")
    p.add_argument("--rows", required=True)
    p.add_argument("--cols", help="optional: omit for one total per row")
    p.add_argument("--val", required=True)
    p.add_argument("--where", action="append", default=[], help="keep rows: col=v1,v2 (repeatable)")
    p.add_argument("--group", action="append", default=[], help="merge row labels: 수도권=서울,경기 (repeatable)")
    p.add_argument("--percent", action="store_true", help="values are fractions (0.362): print them as %% (36.2); with --per: a rate in %% (actual/target)")
    p.add_argument("--change", action="store_true", help="with --pct row|col: change of the share vs previous period (%%p)")
    p.add_argument("--pct", choices=["row", "col", "growth", "diff"], help="shares within row/col, or %% change vs previous period")
    p.add_argument("--agg", default="sum", help="sum | mean | count | wmean (needs --weight)")
    p.add_argument("--weight", help="weight column for --agg wmean")
    p.add_argument("--per", help="ratio: sum(val) / sum(per) per cell, e.g. --val mrr --per customers")
    p.add_argument("--top", type=int)
    p.add_argument("--bridge", metavar="START,END",
                   help="waterfall input: change per row between two --cols values, printed as a values: line")
    p.add_argument("-o", "--out", help="also save the pivot as csv (nothing is written without it)")

    sub.add_parser("design", help="list designs (DESIGN.md files; user ones in ~/.pptkit/designs override)")

    p = sub.add_parser("style", help="learn a personal design from a deck the user already made")
    p.add_argument("action", choices=["extract"])
    p.add_argument("pptx")
    p.add_argument("--name", help="design name (default: file name)")

    p = sub.add_parser("build", help="deck.md -> pptx")
    p.add_argument("deck")
    p.add_argument("-o", "--out")
    p.add_argument("--sample", action="store_true", help="cover + one slide, for tone approval")
    p.add_argument("--design", help="override the design for this build (compare looks quickly)")

    p = sub.add_parser("qa", help="failures only")
    p.add_argument("pptx")
    p.add_argument("-s", "--slides", help="e.g. 3,5")
    p.add_argument("--com", action="store_true", help="Windows+PowerPoint: measure text with PowerPoint itself")

    p = sub.add_parser("map", help="any pptx: one line per slide + recommended read level")
    p.add_argument("pptx")
    p.add_argument("--changed", action="store_true", help="only slides changed since the last map")

    p = sub.add_parser("read", help="read only the slides/shapes you need")
    p.add_argument("pptx")
    p.add_argument("-s", "--slides", required=True, help="e.g. 3,5")
    p.add_argument("-l", "--level", default="L1", choices=["L1", "L2", "L3"], help="L1 text+data, L2 +geometry, L3 XML")
    p.add_argument("--shape", help="shape ids, e.g. 4,7")

    p = sub.add_parser("patch", help="apply ops.yaml to any pptx (keeps formatting; first in-place patch saves .bak)")
    p.add_argument("pptx")
    p.add_argument("ops")
    p.add_argument("-o", "--out")

    p = sub.add_parser("fetch", help="public statistics -> csv + .meta.json (cached)")
    p.add_argument("source", choices=["wb", "kosis"])
    p.add_argument("indicator", nargs="?", help="wb indicator code, e.g. NY.GDP.MKTP.KD.ZG")
    p.add_argument("--country", default="KOR", help="wb: ISO3 list, e.g. KOR,JPN,USA")
    p.add_argument("--years", required=True, help="e.g. 2021-2025")
    p.add_argument("--org", help="kosis orgId")
    p.add_argument("--tbl", help="kosis tblId")
    p.add_argument("--prd", default="Y", help="kosis period: Y | Q | M")
    p.add_argument("-o", "--out", default=".", help="output folder")
    p.add_argument("--refresh", action="store_true")

    p = sub.add_parser("key", help="API keys for optional sources (never printed)")
    p.add_argument("action", choices=["set", "status", "rm"])
    p.add_argument("source", nargs="?")

    sub.add_parser("sources", help="available data sources and key status")

    p = sub.add_parser("install-skill", help="copy the Claude skill to ~/.claude/skills/ppt")
    p.add_argument("--dest", default=str(Path.home() / ".claude" / "skills" / "ppt"))

    a = ap.parse_args(argv)
    from . import data, edit, persona, qa, render  # lazy: keep `pptkit -h` fast

    if a.cmd == "profile":
        if a.action == "set":
            persona.set_profile(a.pairs)
        elif a.action == "reset":
            (persona.home() / "profile.yaml").unlink(missing_ok=True)
        print(persona.profile_report())
    elif a.cmd == "tone":
        bp = Path(a.brief)
        brief = yaml.safe_load(bp.read_text(encoding="utf-8")) if bp.exists() else {}
        tone, summary = persona.resolve_tone(brief or {})
        out = Path(a.out or bp.with_name("tone.yaml"))
        out.write_text(yaml.safe_dump(tone, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(summary + f"\n-> {out}")
    elif a.cmd == "plan":
        from . import plan
        print(plan.report(a.what))
        if a.out and a.what and "/" in a.what:
            out = Path(a.out)
            if out.exists():
                raise SystemExit(f"{out} exists; not overwriting (delete it or pick another -o)")
            out.write_text(plan.skeleton(a.what), encoding="utf-8")
            print(f"-> {out} (replace every TODO, delete slides you do not need)")
    elif a.cmd == "icons":
        names = [n for n in render.icon_names() if not a.query or a.query in n]
        print(f"{len(names)} icons: " + " ".join(names))
    elif a.cmd == "data":
        print(data.summary(a.file))
    elif a.cmd == "pivot":
        df = data.load(a.file)
        bad = [c for c in (a.rows, a.cols, a.val, a.weight) if c and c not in df.columns]
        if bad:
            raise SystemExit(f"unknown column(s) {bad}; one --val per call. columns: {', '.join(map(str, df.columns))}")
        where = {k: [data.coerce(df[k], v) for v in vs.split(",")] for k, _, vs in (w.partition("=") for w in a.where)}
        for g in a.group:
            name, _, members = g.partition("=")
            df[a.rows] = df[a.rows].where(~df[a.rows].astype(str).isin(members.split(",")), name)
        if a.bridge:
            if not a.cols or a.pct or a.per:
                raise SystemExit("--bridge needs --cols (the period column) and no --pct/--per")
            pv = data.pivot(df, a.rows, a.cols, a.val, a.agg, None, where=where, weight=a.weight)
            try:
                items, chg = data.bridge(pv, *a.bridge.split(","), top=a.top or 6)
            except KeyError as e:
                raise SystemExit(e.args[0])
            except TypeError:
                raise SystemExit("--bridge takes START,END")
            n = lambda v, d=1: f"{round(v, d):g}"
            print("values: {" + ", ".join(f'{k}: {chr(34) + "=" + chr(34) if v == "=" else n(v)}' for k, v in items) + "}")
            start = items[0][1]
            print(f"change {n(chg)} ({n(chg / start * 100) if start else 'n/a'}%)")
            cum = 0.0
            for k, v in items[1:-1]:
                cum += v
                print(f"  {k}: {n(v)} = {n(v / chg * 100, 0) if chg else 'n/a'}% of change"
                      + (f" (cumulative {n(cum / chg * 100, 0)}%)" if chg and k != items[-2][0] else ""))
            return 0
        if a.per:  # revenue per customer and similar ratios, computed per cell (not an average of ratios)
            num = data.pivot(df, a.rows, a.cols, a.val, "sum", a.top, where=where)
            den = data.pivot(df, a.rows, a.cols, a.per, "sum", a.top, where=where)
            num.columns = den.columns = [f"{a.val}/{a.per}"] if not a.cols else num.columns
            pv = num / den
            if a.pct:
                body = pv.drop(index="합계", errors="ignore").drop(columns="합계", errors="ignore")
                pv = data.apply_pct(body, a.pct, data.is_time(body.index), data.is_time(body.columns))
        else:
            pv = data.pivot(df, a.rows, a.cols, a.val, a.agg, a.top, where=where, weight=a.weight, pct=a.pct)
        if a.percent:
            pv = pv * 100
        if a.change and a.pct in ("row", "col"):
            body = pv.drop(index="합계", errors="ignore")
            pv = data.apply_pct(body, "diff", data.is_time(body.index), data.is_time(body.columns))
            print("%p change of the share vs previous row")
        elif a.pct:
            along = "column" if a.cols and data.is_time(list(pv.columns)) and not data.is_time(list(pv.index)) else "row"
            print({"growth": f"% change vs previous {along}", "diff": f"change vs previous {along} (same unit)"}.get(
                a.pct, f"% {a.pct} shares"))
        print(data.smart_round(pv, a.pct in ("growth", "row", "col")).to_string(max_rows=15, na_rep="-"))
        if a.pct in ("growth", "diff") and not a.per:  # the summary of the underlying values helps the title
            base = data.pivot(df, a.rows, a.cols, a.val, a.agg, a.top, where=where, weight=a.weight)
            gs = data.growth_summary(base.drop(index="합계", errors="ignore").drop(columns="합계", errors="ignore"))
            if gs is not None and a.agg == "sum":
                print(f"first→last x {fmt_s(gs[2], '.2f')}\n{gs[0]} % {fmt_s(gs[1], '.1f')}")
        rows_t = data.is_time([i for i in pv.index if i != "합계"])  # keep the total row when years run across
        g = data.growth_summary((pv.drop(index="합계", errors="ignore") if rows_t else pv).drop(columns="합계", errors="ignore")) \
            if a.agg == "sum" and not a.pct else None
        if g is not None:
            label, rate, mult = g
            print(f"first→last x {fmt_s(mult, '.2f')}")
            print(f"{label} % {fmt_s(rate, '.1f')}")
        if a.out:
            pv.to_csv(a.out, encoding="utf-8-sig")
            print(f"-> {a.out}")
    elif a.cmd == "style":
        from . import style
        print(style.extract(a.pptx, a.name))
    elif a.cmd == "design":
        for name in persona.design_paths():
            d = persona.load_design(name)
            print(f"{name:10} [{d.get('formality', '')}] {d['description']}")
    elif a.cmd == "build":
        print(render.build(a.deck, a.out, a.sample, a.design))
    elif a.cmd == "qa":
        sl = {int(x) for x in a.slides.split(",")} if a.slides else None
        issues = (qa.check_com if a.com else qa.check)(a.pptx, sl)
        print("\n".join(issues) if issues else "OK")
        return 1 if issues else 0
    elif a.cmd == "map":
        print(edit.deck_map(a.pptx, a.changed))
    elif a.cmd == "read":
        ids = {int(x) for x in a.shape.split(",")} if a.shape else None
        print(edit.read(a.pptx, [int(x) for x in a.slides.split(",")], a.level, ids))
    elif a.cmd == "patch":
        print(edit.patch(a.pptx, a.ops, a.out))
    elif a.cmd == "fetch":
        from . import sources
        kw = ({"indicator": a.indicator, "countries": a.country.split(","), "years": a.years} if a.source == "wb"
              else {"org": a.org, "tbl": a.tbl, "years": a.years, "prd": a.prd})
        print(sources.fetch(a.source, a.out, a.refresh, **kw))
    elif a.cmd == "key":
        from . import sources
        print(sources.key_cmd(a.action, a.source))
    elif a.cmd == "sources":
        from . import sources
        print(sources.sources_report())
    elif a.cmd == "install-skill":
        src = Path(__file__).with_name("skill")
        if not src.exists():  # running from a source checkout
            src = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "ppt"
        shutil.copytree(src, a.dest, dirs_exist_ok=True)
        print(f"skill -> {a.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
