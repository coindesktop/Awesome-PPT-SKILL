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
    """The deck's brand colour: theme accent1 (pptkit writes the design's first series colour there), else the most
    common non-white fill. White backgrounds alone say nothing about the look."""
    try:
        from pptx.opc.constants import RELATIONSHIP_TYPE as RT
        from lxml import etree
        root = etree.fromstring(prs.slide_master.part.part_related_by(RT.THEME).blob)
        a1 = root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}accent1")
        clr = a1[0].get("val") if a1 is not None and len(a1) else None
        if clr:
            return clr.upper()
    except Exception:
        pass
    c = Counter()
    for sl in prs.slides:
        for s in sl.shapes:
            try:
                if s.fill.type == 1 and str(s.fill.fore_color.rgb) not in ("FFFFFF", "000000"):
                    c[str(s.fill.fore_color.rgb)] += 1
            except Exception:
                pass
    return c.most_common(1)[0][0] if c else None


def material(issue):
    """pptkit qa is tuned to pptkit's own geometry; for decks from other tools keep only clear failures."""
    if " sparse:" in issue:
        return False  # a layout hint, not a defect
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
    elif eval_id in (6, 7):
        raw = " ".join(questions(out))
        story = re.findall(r"YC|시드 표준|Sequoia|세쿼이아|트랙션 우선|데모데이|PSST|문제 중심|사례 중심|구성안", raw)
        prs, e = common(out, p, 6, 13)
        if eval_id == 7:
            e.append(ex("목적(투자·고객·채용 등)을 먼저 물음", re.search(r"목적|투자자|고객|채용|누구에게|어떤 자리", raw), raw[:120]))
        e.append(ex("구성안을 2개 이상 제시하고 고르게 함(질문 기록)", len(set(story)) >= 2, f"options {sorted(set(story))}"))
        if prs and eval_id == 6:
            allt = " ".join(t for sl in texts(prs) for t in sl)
            charts = [s.chart for sl in prs.slides for s in sl.shapes if s.has_chart]
            trend = [ch for ch in charts if any(abs((v or 0) - 2950) < 1 or abs((v or 0) - 86) < 0.5
                                                for sr in ch.plots[0].series for v in sr.values)]
            donut = [ch for ch in charts if ch.chart_type is not None and "DOUGHNUT" in str(ch.chart_type)]
            market = [" ".join(sl) for sl in texts(prs) if re.search(r"TAM|SAM|SOM|시장 규모", " ".join(sl))]
            invented = [m for m in market if re.search(r"\d[\d,.]*\s*(조|억)", m) and not re.search(r"예시|가정|추정|확인 필요|TBD", m)]
            e += [ex("트랙션이 CSV 값(최신 MRR 2,950 또는 기관 86곳) 차트로 들어감", trend, f"{len(trend)} matching chart(s)"),
                  ex("팀 3명이 모두 들어감", all(n in allt for n in ("정하늘", "윤재민", "한소라")), "names"),
                  ex("투자 요청: 15억 원과 자금 사용처(도넛 또는 50/30/20%)", "15억" in allt and (donut or all(k in allt for k in ("50%", "30%", "20%"))),
                     f"15억:{'15억' in allt} donut:{len(donut)}"),
                  ex("메모에 없는 시장 규모 수치를 지어내지 않음(넣었다면 예시·가정 표기)", not invented, invented[:1] or "none")]
    elif eval_id == 8:
        prs, e = common(out, p, 6, 12)
        e.append(ex("첫 질문이 5개 이하", len(qs) <= 5, f"{len(qs)} questions"))
        if prs:
            allt = " ".join(t for sl in texts(prs) for t in sl)
            charts = [s.chart for sl in prs.slides for s in sl.shapes if s.has_chart]
            vals = [v for ch in charts for sr in ch.plots[0].series for v in sr.values if v is not None]
            rate = re.search(r"100\.7\s*%", allt)
            vs_target = re.findall(r"\d+%\s*(달성|근접|미달)", allt) or any(
                "목표" in (sr.name or "") for ch in charts for sr in ch.plots[0].series)
            bridge = [ch for ch in charts if any(abs(v - 285.6) < 0.06 for sr in ch.plots[0].series for v in sr.values if v)
                      and any(abs(v - 319.3) < 0.06 for sr in ch.plots[0].series for v in sr.values if v)]
            status = [c for sl in prs.slides for s in sl.shapes if s.has_table for r in s.table.rows for c in
                      [r.cells[i].text for i in range(len(r.cells))] if re.search(r"지연|주의|정상|완료", c)]
            e += [ex("전체 목표 달성률 100.7%가 들어감", rate, "100.7%" if rate else allt[:100]),
                  ex("지역별 목표 대비 실적을 시각화(진척 막대 또는 목표 계열 차트)", vs_target, str(vs_target)[:80]),
                  ex("전년 동기→올해 증감을 한 차트에 시작 285.6·끝 319.3으로 분해(워터폴 등)", bridge, f"{len(bridge)} chart(s)"),
                  ex("과제 상태를 표로 정리(상태 단어 4개 이상)", len(status) >= 4, f"{len(status)} status cells"),
                  ex("평택 대리점 재계약 지연이 드러남", "평택" in allt or "재계약" in allt, "평택/재계약")]
    elif eval_id == 9:
        prs, e = common(out, p, 5, 8)
        if prs:
            allt = " ".join(t for sl in texts(prs) for t in sl)
            charts = [s.chart for sl in prs.slides for s in sl.shapes if s.has_chart]
            cats = [str(c) for ch in charts for c in ch.plots[0].categories]
            prose = " ".join(p.text for sl in prs.slides for s in sl.shapes if s.has_text_frame
                             for p in s.text_frame.paragraphs)  # tables keep last month's row on purpose
            stale = [w for w in ("170.5", "2026-09 매출 170", "영남팀만 목표를 넘", "늘어", "증가분 대부분",
                                 "영남팀 증가가 가장 큼", "중부팀만 소폭 감소", "호남팀 달성률이 가장 낮") if w in prose]
            e += [ex("10월 매출 166.3이 들어감", "166.3" in allt, "166.3"),
                  ex("차트가 10월까지 갱신됨(범주에 2026-10)", any("2026-10" in c or "26.10" in c for c in cats), cats[-3:]),
                  ex("전체 달성률 92.8%가 들어감", "92.8" in allt, "92.8"),
                  ex("9월 수치·틀린 서술이 남지 않음", not stale, stale or "none"),
                  ex("감소를 감소로 서술함(감소/하락/줄)", any(w in allt for w in ("감소", "하락", "줄")), "감소 words")]
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
