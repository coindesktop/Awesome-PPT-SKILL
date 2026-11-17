"""Profile (who) x Brief (this deck) -> Tone = DESIGN.md tokens + density/voice/unit (what the renderer uses)."""
import os
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CATALOG = yaml.safe_load((HERE / "catalog.yaml").read_text(encoding="utf-8"))

# Asked only when they cannot be inferred from the request.
PROFILE_ASK = {
    "role": "어떤 일을 하시나요? (예: 사업기획, 마케팅, 연구, 공공행정, 강사)",
    "industry": "업종은? finance/public/startup/consulting/education/saas/기타",
}
# Never asked: assume the default and tell the user in one line.
PROFILE_DEFAULTS = {"org_culture": "gaejosik", "audiences": ["임원"], "brand": "none"}
BRIEF_REQUIRED = {
    "ask": "이 덱을 본 청중이 무엇을 결정하거나 해야 하나요?",
    "mode": "발표용(present)인가요, 읽는 배포용(handout)인가요? 둘 다면 balanced",
}


def home() -> Path:
    return Path(os.environ.get("PPTKIT_HOME", Path.home() / ".pptkit"))


def load_profile() -> dict:
    p = home() / "profile.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def save_profile(data: dict) -> Path:
    p = home() / "profile.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def set_profile(pairs: list[str]) -> dict:
    prof = load_profile()
    for kv in pairs:
        k, _, v = kv.partition("=")
        k, v = k.strip(), v.strip()
        prof[k] = [s.strip() for s in v.split(",")] if k in ("audiences", "likes", "dislikes") else v
    save_profile(prof)
    return prof


def profile_report() -> str:
    """One line when complete; otherwise what to infer/ask and which defaults to state."""
    prof = load_profile()
    missing = [k for k in PROFILE_ASK if not prof.get(k)]
    defaults = {**PROFILE_DEFAULTS, **({"audiences": ["투자자"], "org_culture": "formal"}
                                        if prof.get("industry") == "startup" else {})}
    assumed = {k: v for k, v in defaults.items() if not prof.get(k)}
    if not missing and not assumed:
        return "PROFILE OK " + " | ".join(f"{k}={_fmt(prof[k])}" for k in [*PROFILE_ASK, *PROFILE_DEFAULTS])
    lines = []
    if missing:
        lines.append("PROFILE MISSING (infer from the request; ask only if you cannot):")
        lines += [f"- {k}: {PROFILE_ASK[k]}" for k in missing]
    if assumed:
        lines.append("ASSUME (do not ask; mention in one line): " + ", ".join(f"{k}={_fmt(v)}" for k, v in assumed.items()))
    lines.append("save: pptkit profile set key=value ...")
    return "\n".join(lines)


def _fmt(v):
    return ",".join(v) if isinstance(v, list) else str(v)


# ---------- designs (DESIGN.md: YAML front matter = tokens, body = rationale) ----------

def design_paths() -> dict:
    found = {p.stem: p for p in sorted((HERE / "designs").glob("*.md"))}
    found.update({p.stem: p for p in sorted((home() / "designs").glob("*.md"))})  # user designs override
    return found


def load_design(name: str) -> dict:
    paths = design_paths()
    if name not in paths:
        raise SystemExit(f"unknown design '{name}'. available: {', '.join(paths)}")
    text = paths[name].read_text(encoding="utf-8")
    meta = yaml.safe_load(text.split("---", 2)[1])
    meta["name"] = name
    _check_design(name, meta)
    return meta


COLOR_ROLES = ("bg", "dark", "ink", "body", "muted", "accent", "card", "line", "neutral_series", "positive", "negative")


def _check_design(name, d):
    """A user DESIGN.md with a missing token fails here with the token's name, not deep inside a slide."""
    import re
    colors = d.get("colors") or {}
    missing = [k for k in COLOR_ROLES if k not in colors]
    bad = [k for k, v in colors.items() if not re.fullmatch(r"[0-9A-Fa-f]{6}", str(v))]
    series = d.get("series") or []
    shape = d.get("shape") or {}
    problems = []
    if missing:
        problems.append(f"colors missing {missing}")
    if bad:
        problems.append(f"colors not 6-digit hex (no #) {bad}")
    if len(series) < 4 or any(not re.fullmatch(r"[0-9A-Fa-f]{6}", str(v)) for v in series):
        problems.append("series needs 4+ hex colours (validate them: adjacent pairs must differ for colour-blind readers)")
    for k in ("type", "shape", "fonts", "cover"):
        if k not in d:
            problems.append(f"`{k}:` missing")
    if shape.get("card", "fill") not in ("fill", "outline", "elevated"):
        problems.append(f"shape.card '{shape.get('card')}' is not fill | outline | elevated")
    if problems:
        raise SystemExit(f"design '{name}': " + "; ".join(problems) + ". Compare with pptkit/designs/corporate.md")


def _pick_design(prof: dict, brief: dict) -> str:
    explicit = brief.get("design") or brief.get("tone") or prof.get("design") or prof.get("tone")
    if explicit:
        if explicit not in design_paths():  # never fall back silently to another look
            raise SystemExit(f"design '{explicit}' not found. available: {', '.join(design_paths())}")
        return explicit
    purpose, industry = brief.get("purpose", ""), prof.get("industry", "")
    if industry == "public":
        return "public"
    story = _storyline(brief)
    if story.get("design"):
        return story["design"]
    if purpose in ("pitch", "demo-day"):
        return "launch"
    if brief.get("formality") == "friendly" or purpose in ("sales", "education"):
        return "forest"
    if purpose in ("pitch", "ir", "strategy") or industry == "startup":
        return "signal"
    return "corporate"  # company reports; `executive` stays available as the quieter consulting look


def _storyline(brief):
    sid = brief.get("storyline")
    if not sid:
        return {}
    from . import plan
    return plan._get(sid)


def resolve_tone(brief: dict) -> tuple[dict, str]:
    """Return (tone, summary for the model). Missing brief fields are reported, not guessed."""
    prof = load_profile()
    tone = load_design(_pick_design(prof, brief))
    brand = str(prof.get("brand", "none")).lstrip("#")
    if len(brand) == 6:
        tone["colors"]["accent"] = brand.upper()  # brand drives the accent; chart series stay validated
    mode = brief.get("mode") or _storyline(brief).get("mode", "balanced")
    tone["density"] = dict(CATALOG["density"].get(mode, CATALOG["density"]["balanced"]))
    voice = brief.get("voice") or prof.get("org_culture", "gaejosik")
    formality = brief.get("formality")
    if formality == "friendly" and voice in ("gaejosik", "formal"):
        voice = "friendly"  # friendly decks read better in ~합니다/~해요 than in report shorthand
    elif formality == "neutral" and voice == "gaejosik":
        voice = "formal"  # full sentences in ~합니다, neither report shorthand nor 해요체
    tone["voice"] = voice
    if brief.get("length"):
        tone["length"] = brief["length"]
    tone["callout_title"] = CATALOG["callout_titles"].get(voice, "시사점")
    conv = CATALOG["conventions"].get(prof.get("industry", "default"), {})
    tone["unit"] = brief.get("unit") or conv.get("unit", "")
    rules = CATALOG["conventions"]["default"]["rules"] + conv.get("rules", [])
    rules += [f"싫어함: {d}" for d in prof.get("dislikes", [])]
    if mode == "present":
        rules.append("슬라이드마다 notes:에 발표 멘트 2~3문장")
    d = tone["density"]
    summary = [
        f"DESIGN {tone['name']}: {tone['description']}",
        f"VOICE {voice}: {CATALOG['voices'][voice]} | bullets<={d['max_bullets']} x {d['max_chars']}자",
        "RULES: " + "; ".join(rules),
    ]
    if formality and formality not in ("formal", "friendly", "neutral"):
        summary.append(f"NOTE formality={formality} is not used: formal (org voice) | neutral (~합니다) | friendly")
    missing = [f"- {k}: {q}" for k, q in BRIEF_REQUIRED.items() if not brief.get(k)
               and not (k == "mode" and brief.get("storyline"))]
    if missing:
        summary.insert(0, "BRIEF MISSING (ask before building):\n" + "\n".join(missing))
    return tone, "\n".join(summary)
