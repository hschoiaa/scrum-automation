# 🤖 스크럼 보고서 자동화

매일 자동으로 JIRA 티켓을 분석하여 Confluence 위키에 스크럼 보고서를 등록하는 자동화 시스템입니다.

## ✨ 기능

- 📊 최근 1주일간 업데이트된 JIRA 티켓 자동 조회
- 💬 JIRA 댓글까지 포함한 상세 분석
- 📁 월별 폴더 자동 생성 (예: 2026-01)
- 📄 일자별 페이지 자동 생성 (예: 2026-01-29)
- 🏷️ 진행중/KTLO 자동 분류
- 🔗 JIRA 티켓 링크 자동 삽입
- ⏰ 매일 오전 9시 자동 실행
- 🎯 수동 실행도 가능

## 🚀 GitHub Actions 자동 실행

이 프로젝트는 GitHub Actions를 사용하여 매일 자동으로 실행됩니다.

### 실행 일정
- **자동**: 매일 오전 9시 (한국 시간)
- **수동**: GitHub Actions 탭에서 "Run workflow" 버튼 클릭

## 🔧 설정 방법

### 1. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions > New repository secret

다음 3개의 Secret을 추가하세요:

| Name | Value | 설명 |
|------|-------|------|
| `JIRA_EMAIL` | `hschoi82@musinsa.com` | JIRA 로그인 이메일 |
| `JIRA_TOKEN` | `ATATT3xFf...` | JIRA API 토큰 |
| `WIKI_PARENT_PAGE_ID` | `291243949` | 위키 부모 페이지 ID |

### 2. JIRA API 토큰 발급

1. https://id.atlassian.com/manage-profile/security/api-tokens 접속
2. "Create API token" 클릭
3. 토큰 이름 입력 (예: "github-actions-scrum")
4. 생성된 토큰 복사 → GitHub Secrets에 등록

## 📁 위키 페이지 구조

```
스크럼 문서 자동화 (291243949)
└── 2026-01 (자동 생성)
    ├── 2026-01-29 (자동 생성)
    ├── 2026-01-30
    └── 2026-01-31
```

## 🔗 링크

- **메인 위키**: https://wiki.team.musinsa.com/wiki/spaces/~hschoi82/pages/291243949
- **JIRA**: https://jira.team.musinsa.com

## 🧪 로컬 테스트

```bash
# 환경 변수 설정
export JIRA_EMAIL="hschoi82@musinsa.com"
export JIRA_TOKEN="your-token-here"
export WIKI_PARENT_PAGE_ID="291243949"

# 실행
python3 scrum_report.py
```

## 📝 수동 실행 방법

1. GitHub 저장소 접속
2. "Actions" 탭 클릭
3. "Daily Scrum Report" 워크플로우 선택
4. "Run workflow" 버튼 클릭
5. "Run workflow" 확인

## 🛠️ 문제 해결

### 토큰 만료 시
1. 새 JIRA API 토큰 발급
2. GitHub Secrets의 `JIRA_TOKEN` 업데이트

### 워크플로우 실패 시
1. Actions 탭에서 실패한 워크플로우 클릭
2. 로그 확인
3. 환경 변수 및 권한 확인

## 📄 라이선스

MIT License
