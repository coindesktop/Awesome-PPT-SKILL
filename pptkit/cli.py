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

    p = sub.add_parser("data", help="summarize a csv/xlsx")
    p.add_argument("file")

    p = sub.add_parser("pivot", help="pivot a csv/xlsx")
    p.add_argument("file")
    p.add_argument("--rows", required=True)
    p.add_argument("--cols", required=True)
    p.add_argument("--val", required=True)
    p.add_argument("--agg", default="sum")
    p.add_argument("--top", type=int)
    p.add_argument("-o", "--out")

    p = sub.add_parser("build", help="deck.md -> pptx")
    p.add_argument("deck")
    p.add_argument("-o", "--out")
    p.add_argument("--sample", action="store_true", help="cover + one slide, for tone approval")

    p = sub.add_parser("qa", help="failures only")
    p.add_argument("pptx")

    p = sub.add_parser("install-skill", help="copy the Claude skill to ~/.claude/skills/ppt")
    p.add_argument("--dest", default=str(Path.home() / ".claude" / "skills" / "ppt"))

    a = ap.parse_args(argv)
    from . import data, persona, qa, render  # lazy: keep `pptkit -h` fast

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
    elif a.cmd == "data":
        print(data.summary(a.file))
    elif a.cmd == "pivot":
        pv = data.pivot(data.load(a.file), a.rows, a.cols, a.val, a.agg, a.top)
        out = Path(a.out or Path(a.file).with_suffix(".pivot.csv"))
        pv.to_csv(out, encoding="utf-8-sig")
        print(pv.round(1).to_string(max_rows=15) + f"\n-> {out}")
    elif a.cmd == "build":
        print(render.build(a.deck, a.out, a.sample))
    elif a.cmd == "qa":
        issues = qa.check(a.pptx)
        print("\n".join(issues) if issues else "OK")
        return 1 if issues else 0
    elif a.cmd == "install-skill":
        src = Path(__file__).with_name("skill")
        if not src.exists():  # running from a source checkout
            src = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "ppt"
        shutil.copytree(src, a.dest, dirs_exist_ok=True)
        print(f"skill -> {a.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
