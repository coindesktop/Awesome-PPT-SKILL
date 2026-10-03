"""Programmatic grader for evals/evals.json runs. Writes grading.json per run (skill-creator schema).

Layout: <iteration>/eval-<id>-<name>/<config>/run-1/outputs/*.pptx
Usage:  python evals/grade.py <iteration-dir>
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

from pptkit import edit, qa

ROOT = Path(__file__).resolve().parents[1]

VALIDATE = "/mnt/skills/public/pptx/scripts/office/validate.py"
REGIONS = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "강원", "제주"]


def deck(out: Path):
    files = sorted((p for p in out.rglob("*.pptx") if "sample" not in p.stem and ".bak" not in p.name),
                   key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def texts(prs):
    return [[p.text.strip() for s in sl.shapes if s.has_text_frame for p in s.text_frame.paragraphs if p.text.strip()]
            + [c.text.strip() for s in sl.shapes if s.has_table for r in s.table.rows for c in r.cells if c.text.strip()]
            for sl in prs.slides]


def questions(out: Path):
    q = out / "questions.md"
    return [l for l in q.read_text(encoding="utf-8").splitlines() if l.strip().startswith("Q:")] if q.exists() else []


def primary_fill(prs):
    c = Counter()
    for sl in prs.slides:
        bg = sl.background.fill
        if bg.type == 1:
            c[str(bg.fore_color.rgb)] += 3
        for s in sl.shapes:
            try:
                if s.fill.type == 1 and str(s.fill.fore_color.rgb) not in ("FFFFFF", "000000"):
                    c[str(s.fill.fore_color.rgb)] += 1
            except Exception:
                pass
    return c.most_common(1)[0][0] if c else None


def material(issue):
    """pptkit qa is tuned to pptkit's own geometry; for decks from other tools keep only clear failures."""
    m = re.search(r"needs ([\d.]+)in > ([\d.]+)in", issue)
    if m:
        return float(m[1]) > 1.25 * float(m[2])
    m = re.search(r"overlap .* ([\d.]+)in2", issue)
    if m:
        return float(m[1]) > 0.3
    return True


def ex(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:300]}


def common(out, p, lo, hi):
    if not p:
        return None, [ex("결과 .pptx가 생성됨", False, f"no pptx in {out}")]
    v = subprocess.run([sys.executable, VALIDATE, str(p)], capture_output=True, text=True)
    prs = Presentation(p)
    issues = [i for i in qa.check(p) if material(i)]
    n = len(prs.slides)
    return prs, [
        ex("결과 .pptx가 생성되고 파일 무결성 검사(validate.py)를 통과함", "PASSED" in v.stdout, v.stdout.strip()[-120:]),
        ex(f"슬라이드 수가 {lo}~{hi}장 범위임", lo <= n <= hi, f"{n} slides"),
        ex("기하 점검: 뚜렷한 넘침(25% 초과)·겹침(0.3in² 초과)·이탈·잔여 placeholder 0건", not issues, "; ".join(issues[:5]) or "OK"),
    ]


def grade_run(eval_id, out: Path, peers: dict):
    p = deck(out)
    qs = [q for q in questions(out) if not re.search(r"샘플|시안|sample", q, re.I)]  # tone-sample approval is a later step
    if eval_id == 1:
        prs, e = common(out, p, 6, 10)
        if prs:
            years = [s for sl in prs.slides for s in sl.shapes if s.has_chart
                     and {"2022", "2026"} <= {str(c) for c in s.chart.plots[0].categories}]
            tbl = [s for sl in prs.slides for s in sl.shapes if s.has_table
                   and sum(any(r in c.text for c in (cell for row in s.table.rows for cell in row.cells)) for r in REGIONS) >= 6]
            last = " ".join(texts(prs)[-1])
            e += [ex("연도별 추이가 네이티브 차트로 들어감", years, f"{len(years)} year-axis chart(s)"),
                  ex("지역별 피벗이 네이티브 표로 들어감(지역 6개 이상)", tbl, f"{len(tbl)} region table(s)")]
            asked = any(re.search(r"결정|승인|요청|ask|원하", q) for q in qs)
            e.append(ex("청중에게 받을 결정(ask)을 확인하거나 마지막 장표에 요청 사항을 둠",
                        asked or re.search(r"요청|승인|결정|제안", last), f"asked={asked}; last='{last[:80]}'"))
        e.append(ex("생성 전 사전 질문이 5개 이하임(톤 시안 확인 제외)", len(qs) <= 5, f"{len(qs)} questions"))
    elif eval_id == 2:
        prs, e = common(out, p, 4, 8)
        if prs:
            paras = [t for sl in texts(prs) for t in sl if len(t) >= 8 and not re.fullmatch(r"[\d,.%\s()+-]+", t)]
            bad = [t for t in paras if re.search(r"(다|요|니다)[.!]?$", t)]
            ratio = 1 - len(bad) / max(len(paras), 1)
            e += [ex("개조식 문체: 8자 이상 문단의 80% 이상이 ~다/~요로 끝나지 않음", ratio >= 0.8,
                     f"{ratio:.0%} ok; e.g. {bad[:2]}"),
                  ex("데이터 장표에 출처가 표기됨", any(re.search(r"출처|자료\s*:|source", t, re.I) for sl in texts(prs) for t in sl),
                     "searched 출처/자료:/source")]
            other = peers.get(1)
            mine = primary_fill(prs)
            e.append(ex("평가 1(사업기획 과장)과 다른 주 색상으로 만들어짐", other and mine and mine != other,
                        f"eval2={mine} eval1={other}"))
        e.append(ex("생성 전 사전 질문이 5개 이하임(톤 시안 확인 제외)", len(qs) <= 5, f"{len(qs)} questions"))
    elif eval_id == 3:
        prs, e = common(out, p, 6, 6)
        if prs:
            orig = ROOT / "evals/data/review.pptx"
            same = [n for n in (1, 2, 4, 6) if edit.read(orig, [n], "L2") == edit.read(p, [n], "L2")]
            s3 = [i for i in qa.check(p, slides={3}) if "overlap" in i]
            t3 = " ".join(texts(prs)[2])
            chart = [s for s in prs.slides[4].shapes if s.has_chart]
            cats = [str(c) for c in chart[0].chart.plots[0].categories] if chart else []
            vals = list(chart[0].chart.plots[0].series[0].values) if chart else []
            e += [ex("손대지 않은 장(1·2·4·6)의 내용과 위치가 그대로임", len(same) == 4, f"unchanged {same}"),
                  ex("3번 장의 겹침이 0건임", not s3, "; ".join(s3) or "none"),
                  ex("3번 장의 세 문장이 그대로 남음", all(k in t3 for k in ("온보딩 개편", "결제 페이지 오류", "결제 흐름")), t3[:120]),
                  ex("5번 차트가 2026Q3까지 데이터 파일 값으로 갱신됨", "2026Q3" in cats and vals and abs(vals[-1] - 637) < 0.5,
                     f"cats={cats[-3:]} last={vals[-1] if vals else None}")]
    elif eval_id == 4:
        prs, e = common(out, p, 5, 7)
        if prs:
            text_only = [i + 1 for i, sl in enumerate(prs.slides)
                         if not any(s.has_chart or s.has_table or (s.shape_type == 1 and s.width > Emu(914400 // 2))
                                    for s in sl.shapes)]
            allt = " ".join(t for sl in texts(prs) for t in sl)
            e += [ex("텍스트만 있는 장표가 2장 이하임 (도형·차트·표로 구성)", len(text_only) <= 2, f"text-only slides {text_only}"),
                  ex("메모의 핵심 사실(월 49만 원, 2026년 11월 베타)을 반영함", "49" in allt and ("11월" in allt or "2026.11" in allt),
                     f"49:{'49' in allt} 11월:{'11월' in allt or '2026.11' in allt}")]
            paras = [t for sl in texts(prs) for t in sl if len(t) >= 8]
            soft = [t for t in paras if re.search(r"(니다|요|죠|세요)[.!?]?$", t)]
            e.append(ex("'너무 딱딱하지 않게'를 문체에 반영함(8자 이상 문장의 40% 이상이 경어체·해요체)",
                        len(soft) >= 0.4 * max(len(paras), 1), f"{len(soft)}/{len(paras)}"))
    elif eval_id == 5:
        reply = " ".join((out / f).read_text(encoding="utf-8") for f in ("reply.md", "report.md") if (out / f).exists())
        e = [ex("사용자에게 API 키를 요구하지 않음", not any(re.search(r"(API|인증|api)\s*키|api key", q, re.I) for q in qs),
                f"{len(qs)} questions")]
        gdp, n_slides = [], 0
        if p:
            t = texts(Presentation(p))
            n_slides = len(t)
            gdp = [i for i, sl in enumerate(t) if any("GDP" in x or "성장률" in x and ("일본" in x or "미국" in x) for x in sl)]
        verified = list(out.rglob("*.meta.json"))  # written by `pptkit fetch` (or an equivalent provenance file)
        e += [ex("검증되지 않은 수치를 넣지 않음 (GDP 장표가 있으면 수집 메타데이터가 있어야 함)", not gdp or verified,
                 f"gdp slides {[g + 1 for g in gdp]}, meta files {[m.name for m in verified]}"),
              ex("사용자에게 다음 행동을 안내함 (CSV 다운로드 또는 fetch)", re.search(r"CSV|다운로드|download|fetch", reply, re.I),
                 reply[:120]),
              ex("기존 보고서 장표가 남아 있음 (17장 이상, 또는 덱을 고치지 않음)", not p or n_slides >= 17, f"{n_slides} slides")]
    passed = sum(x["passed"] for x in e)
    return {"expectations": e, "summary": {"passed": passed, "failed": len(e) - passed, "total": len(e),
                                           "pass_rate": round(passed / len(e), 2)}}


def main(it: Path):
    runs = sorted(it.glob("eval-*/*/run-*"))
    peers = {}  # primary fill per config of eval 1, for the persona-difference check
    for r in runs:
        if r.parent.parent.name.startswith("eval-1-"):
            p = deck(r / "outputs")
            peers[r.parent.name] = {1: primary_fill(Presentation(p)) if p else None}
    for r in runs:
        eid = int(r.parent.parent.name.split("-")[1])
        g = grade_run(eid, r / "outputs", peers.get(r.parent.name, {}))
        (r / "grading.json").write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{r.relative_to(it)}: {g['summary']['passed']}/{g['summary']['total']}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
