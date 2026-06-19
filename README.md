# 후보자 코멘트 자동 정리 에이전트

전화 면접 **음성 녹음 파일**을 넣으면, 자동으로 받아쓰기하고 항목을 추출해
**"후보자 코멘트" 양식(.docx)** 으로 만들어 주는 AI 에이전트입니다.

```
input/ 폴더에 음성(.m4a 등) 넣기
   │
   ├─ ① Naver CLOVA Speech 로 한국어 받아쓰기 (화자분리 포함)
   ├─ ② Claude(claude-opus-4-8)로 양식 항목 추출
   └─ ③ output/ 폴더에 완성된 .docx + 전사문 저장
```

추출하는 항목: 직무명 · 성명 · 경력 · 현재/희망 연봉 · 기술스택 ·
수행업무 요약([내용]) · 구직상태/입사가능시기([상황]) · 재직기업별 이직사유.

---

## 1. 사전 준비

### (1) Anthropic API 키
- https://console.anthropic.com 에서 API 키 발급.

### (2) Naver CLOVA Speech 설정
1. [네이버 클라우드 플랫폼](https://www.ncloud.com) 가입/로그인
2. **CLOVA Speech** 상품 신청 → **도메인 생성**
3. 생성한 도메인 상세에서 **Invoke URL** 과 **Secret Key** 확인

---

## 2. 설치

```bash
# 가상환경 (권장)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

`.env.example` 을 복사해 `.env` 를 만들고 값을 채웁니다.

```bash
cp .env.example .env
# 편집기로 .env 를 열어 키 4개(ANTHROPIC_API_KEY, CLOVA_SPEECH_INVOKE_URL,
# CLOVA_SPEECH_SECRET 등)를 입력
```

---

## 3. 실행

### 폴더 자동 감시 (기본 사용법)
```bash
python -m src.watch
```
실행해 두고 `input/` 폴더에 음성 파일을 넣으면 자동으로 처리되어
`output/` 에 결과 `.docx` 와 전사문 `.txt` 가 생성됩니다. (종료: `Ctrl+C`)

### 파일 1건만 즉시 처리 (테스트용)
```bash
python -m src.run_once "input/면접녹음.m4a"
```

---

## 4. 구조

| 파일 | 역할 |
|------|------|
| `src/stt.py` | CLOVA Speech 음성→텍스트 변환 |
| `src/extract.py` | Claude로 양식 항목 추출 (구조화 출력) |
| `src/render.py` | 추출 결과를 .docx 로 생성 |
| `src/pipeline.py` | 전사 → 추출 → 생성 한 번에 처리 |
| `src/watch.py` | `input/` 폴더 감시 (진입점) |
| `src/config.py` | 환경변수/경로 설정 |
| `templates/` | 원본 양식 (참고용) |

---

## 5. 커스터마이징

- **추출 항목 추가/변경**: `src/extract.py` 의 `CandidateComment` 모델과
  `SYSTEM_PROMPT` 를 수정하세요.
- **문서 서식 변경**: `src/render.py` 의 `render()` 함수에서 문단/스타일을 조정하세요.
- **긴 음성(수십 분 이상)**: CLOVA Speech의 동기(sync) 응답이 타임아웃될 수 있습니다.
  이 경우 `src/stt.py` 의 `completion` 을 `async` 로 바꾸고 콜백/폴링 방식으로
  결과를 받아오도록 변경해야 합니다.

---

## 6. 주의

- `.env` 와 `input/`, `output/` 내용물은 `.gitignore` 로 저장소에 올라가지 않습니다
  (개인정보·비밀키 보호).
- 음성에 없는 정보는 빈칸으로 둡니다. 결과 문서는 사람이 한 번 검토한 뒤 사용하세요.
