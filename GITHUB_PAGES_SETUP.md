# GitHub Pages 설정 가이드

이 가이드는 프로젝트를 GitHub Pages에서 볼 수 있도록 설정하는 방법을 설명합니다.

## 📋 사전 준비

1. GitHub 저장소가 public이어야 합니다 (또는 GitHub Pro 이상)
2. 저장소에 대한 관리자 권한이 필요합니다

## 🚀 설정 단계

### 1단계: 파일 커밋 및 푸시

생성된 파일들을 GitHub에 푸시합니다:

```bash
git add docs/index.html .github/workflows/deploy-pages.yml
git commit -m "Add GitHub Pages setup"
git push origin cursor/rust-mvp-3c29
```

### 2단계: GitHub Pages 활성화

1. GitHub 저장소로 이동: https://github.com/lovelyjhk/AI_basic
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Pages** 클릭
4. **Source** 섹션에서:
   - **GitHub Actions**를 선택

### 3단계: GitHub Actions 권한 설정

1. **Settings** → **Actions** → **General**로 이동
2. **Workflow permissions** 섹션에서:
   - "Read and write permissions" 선택
   - "Allow GitHub Actions to create and approve pull requests" 체크
3. **Save** 클릭

### 4단계: 배포 확인

1. **Actions** 탭으로 이동
2. "Deploy to GitHub Pages" 워크플로우가 실행 중인지 확인
3. 워크플로우가 성공적으로 완료되면 (초록색 체크 표시)
4. **Settings** → **Pages**에서 배포된 URL 확인

## 🌐 접속 URL

배포가 완료되면 다음 URL에서 접속할 수 있습니다:

```
https://lovelyjhk.github.io/AI_basic/
```

## 🔄 자동 배포

설정 완료 후:
- `cursor/rust-mvp-3c29` 브랜치에 푸시할 때마다 자동으로 배포됩니다
- 배포는 약 1-2분 정도 소요됩니다

## ⚙️ 수동 배포

필요시 수동으로 배포할 수 있습니다:

1. **Actions** 탭으로 이동
2. "Deploy to GitHub Pages" 워크플로우 클릭
3. **Run workflow** 버튼 클릭
4. 브랜치 선택 후 **Run workflow** 확인

## 🐛 문제 해결

### 404 에러가 발생하는 경우

1. **Settings** → **Pages**에서 Source가 "GitHub Actions"로 설정되어 있는지 확인
2. **Actions** 탭에서 워크플로우가 성공적으로 완료되었는지 확인
3. 실패한 경우 로그를 확인하여 오류 원인 파악

### 워크플로우가 실행되지 않는 경우

1. **Settings** → **Actions** → **General**에서 Actions가 활성화되어 있는지 확인
2. 저장소가 private인 경우 GitHub Actions 사용 가능 여부 확인

### 권한 오류가 발생하는 경우

1. **Settings** → **Actions** → **General**
2. "Workflow permissions"를 "Read and write permissions"로 변경

## 📝 파일 구조

```
AI_basic/
├── docs/
│   └── index.html          # 메인 웹페이지
├── .github/
│   └── workflows/
│       └── deploy-pages.yml # GitHub Actions 워크플로우
└── GITHUB_PAGES_SETUP.md    # 이 가이드
```

## ✨ 커스터마이징

`docs/index.html` 파일을 수정하여 웹페이지를 커스터마이징할 수 있습니다:
- 색상 변경
- 콘텐츠 추가/수정
- 추가 페이지 생성 (docs 폴더 내)

수정 후 커밋 및 푸시하면 자동으로 반영됩니다.

## 🔗 유용한 링크

- [GitHub Pages 공식 문서](https://docs.github.com/en/pages)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [프로젝트 저장소](https://github.com/lovelyjhk/AI_basic)
