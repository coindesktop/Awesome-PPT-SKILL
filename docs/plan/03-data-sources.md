# 통계 데이터 연결 설계 (준비 단계)

> 요구: 통계는 붙일 수 있도록 준비만 한다. 사용자의 API 키는 호출 한도와 유출 위험이 있으므로 기본 동작에서 쓰지 않는다. 키 없이도 스킬이 완전히 동작해야 한다.

## 1. 원칙

1. **키 없이 동작한다.** 기본 경로는 사용자 파일과 키가 필요 없는 공개 API다. 스킬 실행 중에 "API 연결이 필요합니다" 같은 안내가 뜨는 일은 기본적으로 없다.
2. **키는 Claude를 거치지 않는다.** 키가 필요한 소스를 쓰기로 선택한 경우에도 키는 OS 자격 증명 저장소(Windows 자격 증명 관리자)나 환경 변수에만 둔다. CLI가 직접 읽고, 출력에도 로그에도 남기지 않는다. Claude에게는 `kosis: connected` 같은 상태만 보인다.
3. **데이터는 파일로 받고, Claude는 요약만 본다.** 수집 결과는 CSV와 출처 메타데이터(`.meta.json`)로 저장한다. Claude는 `pptkit data`의 약 100토큰짜리 요약만 읽는다.
4. **한 번 받은 데이터는 캐시한다.** 같은 질의를 반복하면 API를 다시 부르지 않는다. 이 방식으로 호출 한도를 지킨다.
5. **출처는 자동으로 표기한다.** `.meta.json`의 기관명, 표 ID, 수집일이 슬라이드 각주로 들어간다.

## 2. 연결 방식 4단계

| 단계 | 방식 | 키 | 안내 필요 | 상태 |
|---|---|---|---|---|
| T0 | **사용자 파일**: KOSIS·e-나라지표·한국은행 웹사이트에서 받은 CSV·XLSX | 없음 | 없음 | M1에서 구현 |
| T1 | **키가 필요 없는 공개 API**: World Bank, OECD(SDMX), IMF, Eurostat | 없음 | 없음 | M4에서 구현 |
| T2 | **키가 필요한 API**: KOSIS, 한국은행 ECOS, 공공데이터포털 | 사용자 키 | 사용자가 요청할 때만 1회 | 인터페이스만 준비 |
| T3 | **MCP 서버(stdio·원격)**: 공개된 KOSIS MCP 서버 | 서버마다 다름 | 설치 안내 | 탐색용으로만 권장 |

### T0: 사용자 파일 (기본)

- KOSIS 웹사이트의 통계표 화면에서 "다운로드 → CSV"로 받은 파일을 그대로 넣는다.
- KOSIS CSV는 머리글이 여러 줄이고 셀 병합 흔적이 있다. `pptkit data`가 이 형식을 인식해서 정돈된 표로 바꾼다.
- 키도 네트워크도 필요 없으므로 항상 동작한다.

### T1: 키가 필요 없는 공개 API

```bash
pptkit fetch wb NY.GDP.MKTP.KD.ZG --country KOR,JPN,USA --years 2019-2025
pptkit fetch oecd <dataflow> --filter ...
```

- 국제 비교 지표(GDP, 물가, 고용, 무역)를 키 없이 받을 수 있다.
- 결과는 `data/wb_NY.GDP.MKTP.KD.ZG.csv`와 `.meta.json`으로 저장한다.

### T2: 키가 필요한 API (선택)

| 소스 | 키 발급 | 저장 위치 |
|---|---|---|
| KOSIS OpenAPI | kosis.kr/openapi 가입 후 즉시 발급 | 자격 증명 관리자 `pptkit/kosis` 또는 `KOSIS_API_KEY` |
| 한국은행 ECOS | ecos.bok.or.kr/api 에서 무료 신청 | `pptkit/ecos` 또는 `ECOS_API_KEY` |
| 공공데이터포털 | data.go.kr 활용 신청 | `pptkit/datagokr` 또는 `DATA_GO_KR_KEY` |

- 등록 명령은 `pptkit key set kosis` 하나다. 키는 터미널에서 직접 입력받으므로 대화창에 나타나지 않는다.
- 키가 없는데 사용자가 KOSIS API를 명시적으로 요청한 경우에만, 발급 URL과 위 명령을 한 번 안내한다. 그 외에는 T0로 대신하는 방법을 제안한다.

### T3: MCP 서버

| 서버 | 방식 | 키 | 비고 |
|---|---|---|---|
| rubatoyd/kosis-openapi-mcp | 로컬 stdio + CLI | 사용자 키 필요 | 4만 셀 초과 시 기간 자동 분할, CSV·XLSX 내보내기. MIT |
| pipeworx-io/mcp-kosis-kr | 로컬 stdio (`npx`) | 사용자 키 필요 | 통계표 검색·목록·수치 조회. MIT |
| Dayoooun/korea-stats-mcp | 원격(Vercel) 또는 `npx` | 원격은 키 불필요 | 운영자 키를 공유하는 제3자 서버다. 가용성과 데이터 경로를 우리가 통제할 수 없다. 응답은 최대 32KiB다 |

**MCP는 탐색용으로만 권장한다.** MCP 도구의 응답은 대화 컨텍스트로 그대로 들어온다. 응답이 최대 32KiB이면 대략 8,000토큰 이상이다. 반면 `pptkit fetch`는 데이터를 파일로 저장하고 요약 약 100토큰만 돌려준다. 그래서 "어떤 통계표가 있는지 찾기"는 MCP로, "데이터 받기"는 CLI로 나누는 편이 효율적이다.

### RSS

KOSIS는 공지와 보도자료를 RSS로 제공한다. 하지만 RSS에는 수치 데이터가 없다. 그래서 RSS는 "새 통계가 발표됐다"는 알림이나 출처 날짜 확인에만 쓸 수 있다. 우선순위는 낮게 둔다(P2).

## 3. CLI 인터페이스 (준비할 것)

```
pptkit data <file>                 T0 파일 정돈 + 요약
pptkit fetch <source> <query...>   T1/T2 수집 → CSV + .meta.json (캐시 사용)
pptkit key set|status|rm <source>  T2 키 관리 (키 값은 절대 출력하지 않음)
pptkit sources                     사용 가능한 소스와 연결 상태 목록
```

어댑터는 소스마다 파일 하나(`pptkit/sources/wb.py` 등)로 둔다. 새 소스를 추가할 때 다른 코드를 고칠 필요가 없게 한다.

## 4. 이 컨테이너의 제약

클라우드 개발 환경의 네트워크 정책이 `api.worldbank.org`, `kosis.kr`, `apis.data.go.kr`, `sdmx.oecd.org`를 막고 있다. 그래서 T1 어댑터는 저장해 둔 응답으로 테스트하고, 실제 호출 확인은 로컬 Windows에서 한다.
