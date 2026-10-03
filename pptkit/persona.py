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
    assumed = {k: v for k, v in PROFILE_DEFAULTS.items() if not prof.get(k)}
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
    return meta


def _pick_design(prof: dict, brief: dict) -> str:
    explicit = brief.get("design") or brief.get("tone") or prof.get("design") or prof.get("tone")
    if explicit:
        if explicit not in design_paths():  # never fall back silently to another look
            raise SystemExit(f"design '{explicit}' not found. available: {', '.join(design_paths())}")
        return explicit
    purpose, industry = brief.get("purpose", ""), prof.get("industry", "")
    if industry == "public":
        return "public"
    if brief.get("formality") == "friendly" or purpose in ("sales", "education"):
        return "forest"
    if purpose in ("pitch", "ir", "strategy") or industry == "startup":
        return "signal"
    return "executive"


def resolve_tone(brief: dict) -> tuple[dict, str]:
    """Return (tone, summary for the model). Missing brief fields are reported, not guessed."""
    prof = load_profile()
    tone = load_design(_pick_design(prof, brief))
    brand = str(prof.get("brand", "none")).lstrip("#")
    if len(brand) == 6:
        tone["colors"]["accent"] = brand.upper()  # brand drives the accent; chart series stay validated
    mode = brief.get("mode", "balanced")
    tone["density"] = dict(CATALOG["density"].get(mode, CATALOG["density"]["balanced"]))
    voice = brief.get("voice") or prof.get("org_culture", "gaejosik")
    if brief.get("formality") == "friendly" and voice in ("gaejosik", "formal"):
        voice = "friendly"  # friendly decks read better in ~합니다/~해요 than in report shorthand
    tone["voice"] = voice
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
    missing = [f"- {k}: {q}" for k, q in BRIEF_REQUIRED.items() if not brief.get(k)]
    if missing:
        summary.insert(0, "BRIEF MISSING (ask before building):\n" + "\n".join(missing))
    return tone, "\n".join(summary)
