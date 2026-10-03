"""Profile (who) x Brief (this deck) -> Tone (what the renderer uses)."""
import os
from pathlib import Path

import yaml

CATALOG = yaml.safe_load((Path(__file__).with_name("catalog.yaml")).read_text(encoding="utf-8"))

# field: (question, default) - shown only for missing fields
PROFILE_QUESTIONS = {
    "role": ("어떤 일을 하시나요? (예: 사업기획, 마케팅, 연구, 공공행정, 강사)", None),
    "industry": ("업종은? finance/public/startup/consulting/education/saas/기타", "default"),
    "org_culture": ("보고 문체는? gaejosik(~함/~임) / formal(~합니다) / spoken(발표형)", "gaejosik"),
    "audiences": ("주로 누구에게 보여주나요? (예: 임원, 팀, 고객, 투자자)", "임원"),
    "brand": ("회사 대표색 HEX가 있나요? (없으면 none)", "none"),
}
BRIEF_REQUIRED = {
    "ask": "이 덱을 본 청중이 무엇을 결정하거나 해야 하나요?",
    "mode": "발표용(present)인가요, 읽는 배포용(handout)인가요? 둘 다면 balanced",
}


def home() -> Path:
    return Path(os.environ.get("PPTKIT_HOME", Path.home() / ".pptkit"))


def load_profile() -> dict:
    p = home() / "profile.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {} if p.exists() else {}


def save_profile(data: dict) -> Path:
    p = home() / "profile.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def set_profile(pairs: list[str]) -> dict:
    prof = load_profile()
    for kv in pairs:
        k, _, v = kv.partition("=")
        v = v.strip()
        prof[k.strip()] = [s.strip() for s in v.split(",")] if k in ("audiences", "likes", "dislikes") else v
    save_profile(prof)
    return prof


def profile_report() -> str:
    """One line when complete; otherwise only the missing questions (with defaults)."""
    prof = load_profile()
    missing = [k for k in PROFILE_QUESTIONS if not prof.get(k)]
    if not missing:
        return "PROFILE OK " + " | ".join(f"{k}={_fmt(prof[k])}" for k in PROFILE_QUESTIONS)
    lines = [f"PROFILE MISSING {len(missing)} (infer from the request first; ask only what you cannot infer)"]
    for k in missing:
        q, d = PROFILE_QUESTIONS[k]
        lines.append(f"- {k}: {q}" + (f" [default: {d}]" if d else ""))
    lines.append("save: pptkit profile set key=value ...")
    return "\n".join(lines)


def _fmt(v):
    return ",".join(v) if isinstance(v, list) else str(v)


def _pick_tone(prof: dict, brief: dict) -> str:
    if brief.get("tone") or prof.get("tone"):
        return brief.get("tone") or prof["tone"]
    purpose, industry = brief.get("purpose", ""), prof.get("industry", "")
    if purpose in ("pitch", "ir", "sales") or industry == "startup":
        return "pitch-bold"
    if purpose in ("report", "proposal") and industry in ("consulting", "finance", "saas", "default", ""):
        return "consulting-navy"
    return "corporate-clean"


def resolve_tone(brief: dict) -> tuple[dict, str]:
    """Return (tone dict, summary text for the model). Missing brief fields are reported, not guessed."""
    prof = load_profile()
    name = _pick_tone(prof, brief)
    tone = {"name": name, **CATALOG["tones"][name]}
    brand = str(prof.get("brand", "none")).lstrip("#")
    if len(brand) == 6:
        tone["primary"] = brand.upper()  # brand drives structure only; series stay validated
    mode = brief.get("mode", "balanced")
    tone["density"] = CATALOG["density"].get(mode, CATALOG["density"]["balanced"])
    voice = brief.get("voice") or prof.get("org_culture", "gaejosik")
    if mode == "present" and voice == "gaejosik" and brief.get("purpose") in ("pitch", "education"):
        voice = "spoken"
    tone["voice"] = voice
    ind = prof.get("industry", "default")
    conv = CATALOG["conventions"].get(ind, {})
    tone["unit"] = brief.get("unit") or conv.get("unit", "")
    tone["frame"] = "plain" if name == "pitch-bold" or brief.get("purpose") == "education" else "kr-report"
    rules = CATALOG["conventions"]["default"]["rules"] + conv.get("rules", [])
    rules += [f"싫어함: {d}" for d in prof.get("dislikes", [])]
    d = tone["density"]
    missing = [f"- {k}: {q}" for k, q in BRIEF_REQUIRED.items() if not brief.get(k)]
    summary = [
        f"TONE {name} | frame={tone['frame']} | voice={voice} | bullets<={d['max_bullets']} x {d['max_chars']}자 | body {d['body_pt']}pt",
        "WRITE: " + CATALOG["voices"][voice],
        "RULES: " + "; ".join(rules),
    ]
    if missing:
        summary.insert(0, "BRIEF MISSING (ask before building):\n" + "\n".join(missing))
    return tone, "\n".join(summary)
