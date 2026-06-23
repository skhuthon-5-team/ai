# 🛠️ Git & GitHub 협업 가이드

처음 협업하는 팀원을 위한 가이드입니다. **이슈 → 브랜치 → 커밋/푸시 → PR** 순서대로 진행하면 됩니다.

> ⚠️ **절대 `main`, `develop`에 직접 push 하지 마세요.** 모든 작업은 브랜치 → PR을 거칩니다.

---

## 0. 작업 흐름 한눈에 보기

```
이슈 생성  →  develop에서 브랜치 분기  →  작업 & 커밋  →  push  →  PR 생성  →  리뷰/머지
```

브랜치 구조:

```
main      ← 배포용 (직접 건드리지 않음)
└─ develop ← 개발 통합 브랜치 (여기서 분기)
   └─ feature/#12  ← 각자 작업 브랜치
```

---

## 1. 이슈(Issue) 생성

작업을 시작하기 **전에** 항상 이슈를 먼저 만듭니다. 브랜치 이름과 커밋에 이슈 번호가 들어가기 때문입니다.

1. 레포 상단 **Issues** 탭 → **New issue**
2. 제목 컨벤션: `[타입] 작업 내용`
   - 예: `[Feat] 로그인 API 구현`
   - 예: `[Fix] 회원가입 시 중복 이메일 검증 누락`
3. 본문에 **무엇을, 왜** 하는지 간단히 작성
4. 생성하면 `#12` 같은 **이슈 번호**가 부여됨 → 이 번호를 기억하세요.

**이슈 제목 타입** (커밋 타입과 동일하게 사용):

| 타입 | 의미 |
|------|------|
| Feat | 새 기능 |
| Fix | 버그 수정 |
| Refactor | 리팩토링 (기능 변화 없음) |
| Docs | 문서 (README 등) |
| Style | 코드 포맷, 세미콜론 등 (로직 변화 없음) |
| Chore | 빌드, 설정, 패키지 등 잡일 |

---

## 2. 브랜치 생성

> 📌 핵심: **`develop`에서 분기**, 이름은 **`feature/#이슈번호`**

```bash
# 1. develop 브랜치로 이동
git checkout develop

# 2. 원격 최신 내용 받아오기 (중요! 안 하면 충돌 잦아짐)
git pull origin develop

# 3. develop에서 새 브랜치 분기 (이슈 번호가 12라면)
git checkout -b feature/#12
```

`git checkout -b`는 **브랜치 생성 + 이동**을 한 번에 합니다.

> 일부 셸에서 `#`이 주석으로 처리되면 따옴표로 감싸세요: `git checkout -b "feature/#12"`

---

## 3. 작업 → 커밋 → 푸시

### 커밋

```bash
# 1. 변경한 파일 확인
git status

# 2. 커밋할 파일 추가 (전체 추가)
git add .
# 또는 특정 파일만: git add src/LoginService.java

# 3. 커밋 (컨벤션: 타입: 작업 내용 (#이슈번호))
git commit -m "feat: 로그인 API 구현 (#12)"
```

**커밋 메시지 컨벤션:** `타입: 작업 내용 (#이슈번호)`

```
feat: 로그인 API 구현 (#12)
fix: 토큰 만료 시 401 반환되도록 수정 (#15)
refactor: UserService 중복 로직 분리 (#18)
docs: README에 실행 방법 추가 (#20)
```

- 타입은 위 [이슈 타입 표](#1-이슈issue-생성)와 동일 (소문자)
- 한 커밋엔 하나의 논리적 변경만. "이것저것 다 함" 식으로 몰아 커밋하지 마세요.

### 푸시

```bash
# 처음 푸시할 때 (원격에 브랜치가 없으므로 -u로 연결)
git push -u origin feature/#12

# 이후엔 그냥
git push
```

---

## 4. PR(Pull Request) 생성

푸시하면 GitHub 레포 페이지 상단에 **"Compare & pull request"** 버튼이 뜹니다.

1. 그 버튼 클릭 (없으면 **Pull requests** 탭 → **New pull request**)
2. **base 브랜치를 반드시 `develop`으로 설정** (기본값이 `main`일 수 있으니 꼭 확인!)
```
   base: develop  ←  compare: feature/#12
```
3. **제목 컨벤션:** `[타입] 작업 내용 (#이슈번호)`
   - 예: `[Feat] 로그인 API 구현 (#12)`
4. **본문**에 아래 내용 작성:

```markdown
예시
## 작업 내용
- 로그인 API 엔드포인트 추가
- JWT 토큰 발급 로직 구현

## 관련 이슈
Closes #12

## 리뷰 포인트
- 토큰 만료 시간 설정값 확인 부탁드립니다
```

> 💡 본문에 `Closes #12`를 적으면 PR이 머지될 때 **이슈가 자동으로 닫힙니다.**

5. **Reviewers**에 팀원 지정 → **Create pull request**

### 머지 규칙

- **자기 PR을 스스로 머지하지 않습니다.** 최소 1명 이상 리뷰 승인 후 머지.
- 충돌(conflict)이 나면 머지 전에 해결:
```bash
  git checkout feature/#12
  git pull origin develop   # develop 최신 내용을 내 브랜치에 반영
  # 충돌 해결 후
  git add .
  git commit
  git push
```
- 머지 후 작업 브랜치는 삭제 (GitHub PR 화면의 **Delete branch** 버튼)

---

## 5. 다음 작업 시작할 때

머지 끝났으면 다시 `develop`을 최신화하고 새 브랜치를 팝니다.

```bash
git checkout develop
git pull origin develop
git checkout -b feature/#23   # 새 이슈 번호로
```

---

## ❓ 자주 막히는 부분

| 상황 | 해결 |
|------|------|
| `develop`에 실수로 커밋함 | 머지 전이면 멈추고 팀에 공유. 혼자 `reset` 하지 말 것 |
| push했더니 거부됨(rejected) | `git pull origin feature/#12` 먼저 한 뒤 다시 push |
| 브랜치 잘못 만듦 | `git branch -d feature/#잘못된번호`로 삭제 후 재생성 |
| 커밋 메시지 오타 | 직전 커밋이면 `git commit --amend -m "올바른 메시지"` |
