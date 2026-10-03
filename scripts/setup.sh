#!/usr/bin/env bash
# 의존성 설치. 이미 설치돼 있으면 건너뛰므로 여러 번 실행해도 된다.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! python3 -c "import pptx, pydantic, markitdown, pandas, openpyxl, matplotlib, wbgapi, PublicDataReader" 2>/dev/null; then
  python3 -m pip install -q -r requirements.txt
fi

# pptkit CLI (편집 모드 설치: 소스 수정이 바로 반영됨)
command -v pptkit >/dev/null || python3 -m pip install -q -e .

# 렌더 확인용: LibreOffice Impress 모듈과 한국어 폰트 (클라우드 컨테이너에는 빠져 있음)
if command -v apt-get >/dev/null && [ "$(id -u)" = 0 ]; then
  dpkg -s libreoffice-impress >/dev/null 2>&1 || apt-get install -y -q --no-install-recommends libreoffice-impress >/dev/null 2>&1 || true
  fc-list | grep -qi nanum || apt-get install -y -q fonts-nanum >/dev/null 2>&1 || true
fi

# graphify 스킬과 PreToolUse 훅이 쓰는 CLI
command -v graphify >/dev/null || python3 -m pip install -q graphifyy

if ! node -e "require('pptxgenjs')" 2>/dev/null; then
  npm install --silent --no-audit --no-fund
fi

command -v soffice >/dev/null || echo "[setup] LibreOffice(soffice) 없음: 렌더 QA를 쓰려면 설치하세요" >&2
command -v pdftoppm >/dev/null || echo "[setup] poppler(pdftoppm) 없음: 렌더 QA를 쓰려면 설치하세요" >&2
exit 0
