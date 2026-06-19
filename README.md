# 후보자 코멘트 자동 정리 에이전트 (무료 버전)

전화 면접 **음성 녹음 파일**을 넣으면, 자동으로 받아쓰기하고 항목을 추출해
**"후보자 코멘트" 양식(.docx)** 으로 만들어 주는 AI 에이전트입니다.

```
input/ 폴더에 음성(.m4a 등) 넣기
   │
   ├─ ① 로컬 Whisper 로 한국어 받아쓰기   (완전 무료, 오프라인)
   ├─ ② Google Gemini 로 양식 항목 추출   (무료 티어)
   └─ ③ output/ 폴더에 완성된 .docx + 전사문 저장
```

추출하는 항목: 직무명 · 성명 · 경력 · 현재/희망 연봉 · 기술스택 ·
수행업무 요약([내용]) · 구직상태/입사가능시기([상황]) · 재직기업별 이직사유.

> 💡 **비용**: 받아쓰기는 PC에서 직접 처리해 무료, 추출은 Gemini 무료 티어를 씁니다.
> 무료 한도(분당/일일 요청 수) 내에서 운영되며, 키 발급에 카드 등록도 필요 없습니다.

---

## 1. 사전 준비

### Google Gemini API 키 (무료)
- https://aistudio.google.com/apikey 접속 → **Create API key** → 키 복사.
- 무료 티어로 바로 사용 가능합니다.

### (Whisper는 별도 키가 필요 없습니다)
- 처음 실행할 때 음성 인식 모델이 자동으로 한 번 다운로드됩니다(이후엔 오프라인).

---

## 2. 설치

```bash
# 가상환경 (권장)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

> **ffmpeg 필요**: Whisper가 오디오를 읽으려면 `ffmpeg`가 설치돼 있어야 합니다.
> - macOS: `brew install ffmpeg`
> - Windows: `winget install Gyan.FFmpeg` (또는 ffmpeg.org에서 설치)
> - Ubuntu: `sudo apt install ffmpeg`

`.env.example` 을 복사해 `.env` 를 만들고 Gemini 키를 채웁니다.

```bash
cp .env.example .env
# 편집기로 .env 를 열어 GEMINI_API_KEY 입력
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
| `src/stt.py` | 로컬 Whisper 음성→텍스트 변환 |
| `src/extract.py` | Gemini로 양식 항목 추출 (구조화 출력) |
| `src/render.py` | 추출 결과를 .docx 로 생성 |
| `src/pipeline.py` | 전사 → 추출 → 생성 한 번에 처리 |
| `src/watch.py` | `input/` 폴더 감시 (진입점) |
| `src/config.py` | 환경변수/경로 설정 |
| `templates/` | 원본 양식 (참고용) |

---

## 5. 속도 · 정확도 조절

받아쓰기 정확도와 속도는 Whisper 모델 크기로 조절합니다. `.env` 에서:

```
WHISPER_MODEL=medium     # tiny < base < small < medium < large-v3
```

- **느리고 정확**: `large-v3` (GPU 권장)
- **균형**: `medium` (기본값)
- **빠르지만 덜 정확**: `small`, `base`

GPU(NVIDIA)가 있으면 `.env` 에서 `WHISPER_DEVICE=cuda`, `WHISPER_COMPUTE_TYPE=float16`
으로 바꾸면 훨씬 빠릅니다.

---

## 6. 커스터마이징

- **추출 항목 추가/변경**: `src/extract.py` 의 `CandidateComment` 모델과
  `SYSTEM_PROMPT` 를 수정하세요.
- **문서 서식 변경**: `src/render.py` 의 `render()` 함수에서 문단/스타일을 조정하세요.

---

## 7. 주의

- `.env` 와 `input/`, `output/` 내용물은 `.gitignore` 로 저장소에 올라가지 않습니다
  (개인정보·비밀키 보호).
- 받아쓰기는 PC에서 처리되어 외부로 나가지 않지만, **추출 단계에서는 전사문이
  Google Gemini로 전송**됩니다. 민감 정보가 있으면 완전 오프라인(로컬 LLM) 구성도
  가능합니다.
- 음성에 없는 정보는 빈칸으로 둡니다. 결과 문서는 사람이 한 번 검토한 뒤 사용하세요.
