"""pptkit: every command prints a short result meant to be read by a model, not a human dashboard."""
import argparse
import shutil
import sys
from pathlib import Path

import yaml


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

    p = sub.add_parser("data", help="summarize a csv/xlsx")
    p.add_argument("file")

    p = sub.add_parser("pivot", help="pivot a csv/xlsx")
    p.add_argument("file")
    p.add_argument("--rows", required=True)
    p.add_argument("--cols", help="optional: omit for one total per row")
    p.add_argument("--val", required=True)
    p.add_argument("--where", action="append", default=[], help="keep rows: col=v1,v2 (repeatable)")
    p.add_argument("--group", action="append", default=[], help="merge row labels: 수도권=서울,경기 (repeatable)")
    p.add_argument("--pct", choices=["row", "col", "growth"], help="shares within row/col, or %% change vs previous period")
    p.add_argument("--agg", default="sum", help="sum | mean | count | wmean (needs --weight)")
    p.add_argument("--weight", help="weight column for --agg wmean")
    p.add_argument("--top", type=int)
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
    elif a.cmd == "data":
        print(data.summary(a.file))
    elif a.cmd == "pivot":
        df = data.load(a.file)
        where = {k: [data.coerce(df[k], v) for v in vs.split(",")] for k, _, vs in (w.partition("=") for w in a.where)}
        for g in a.group:
            name, _, members = g.partition("=")
            df[a.rows] = df[a.rows].where(~df[a.rows].astype(str).isin(members.split(",")), name)
        pv = data.pivot(df, a.rows, a.cols, a.val, a.agg, a.top, where=where, weight=a.weight, pct=a.pct)
        if a.pct:
            print(f"% ({'change vs previous period' if a.pct == 'growth' else a.pct + ' shares'})")
        print(pv.round(1 if a.pct else 3 if a.agg in ("mean", "wmean") else 1).to_string(max_rows=15, na_rep="-"))
        g = data.cagr(pv.drop(columns="합계", errors="ignore")) \
            if a.agg == "sum" and not a.pct else None
        if g is not None:
            print("CAGR % " + "  ".join(f"{k}={v:.1f}" for k, v in g.round(1).items()))
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
