# 왜 GitHub 커밋 창이 비어 보이나요?

현재 로컬 저장소 상태:
- 작업 브랜치: `work`
- 커밋 히스토리:
  - `a2bd8c9` Add root artifact index to improve git visibility
  - `d3bd65f` Add Korean Event CRM blueprint, implementation playbook, and Ops starter pack
  - `e2d5dd4` Initialize repository
- **원격(remote) 설정이 없음** → GitHub에 push되지 않아 웹(main)에서 보이지 않음

---

## 빠른 해결 방법

### 1) 원격 추가
```bash
git remote add origin https://github.com/JeonghaedongVis/EventSptool.git
```

### 2) main 브랜치 생성/전환 후 반영
```bash
git checkout -B main
```

### 3) 현재 작업 반영 (권장: 브랜치 단위)
```bash
git fetch --all --prune
git cherry-pick origin/work
```

### 4) GitHub로 push
```bash
git push -u origin main
```

---

## 대안 (work 브랜치 그대로 푸시)
```bash
git remote add origin https://github.com/JeonghaedongVis/EventSptool.git
git push -u origin work
```
그 후 GitHub에서 `work` → `main` PR 생성.

---

## 포함되어야 할 파일
- `docs/event-crm-blueprint-ko.md`
- `docs/event-crm-implementation-playbook-ko.md`
- `ops/README.md`
- `ops/config/hubspot-properties.json`
- `ops/config/pipeline-stages.json`
- `ops/config/response-buttons.json`
- `ops/templates/message-templates.json`
- `ops/samples/google-sheet-mapping.csv`
- `ops/samples/incoming-webhook-payload.json`
- `FILES_INDEX.md`

---

## VS Code에서 지금 화면 기준으로 진행 (Publish Branch 버튼)
지금 화면은 정상입니다. 아래 순서대로 하면 됩니다.

1. 좌측 Source Control에서 **`Publish Branch`** 클릭
2. GitHub 로그인/권한 승인 요청이 뜨면 승인
3. 퍼블리시 후 브랜치가 원격에 생성됨 (예: `origin/main` 또는 `origin/work`)
4. GitHub 저장소 페이지 새로고침 후 `Commits` 확인

### 만약 `main`에 바로 안 올라가고 `work`로 올라간 경우
1. GitHub에서 **Compare & pull request** 클릭
2. base: `main`, compare: `work` 확인
3. PR 생성 후 Merge

### 확인 명령어 (터미널)
```bash
git branch -vv
git remote -v
git log --oneline --decorate -n 5
```

> 핵심: 지금은 "코드가 없는 상태"가 아니라, **원격으로 publish 전 상태**일 가능성이 가장 큽니다.


---

## `fatal: bad revision` 오류가 날 때
예: `fatal: bad revision 'd3bd65f'`

원인: 해당 커밋 해시 객체가 **현재 로컬 저장소에 없음** (다른 PC/다른 클론/미fetch 상태).

### 해결 순서
1. 원격 브랜치 목록 확인
```bash
git fetch --all --prune
git branch -r
```
2. `origin/work`가 보이면 브랜치 단위로 반영
```bash
git checkout main
git cherry-pick origin/work
```
3. `origin/work`도 없으면, 현재 PC에서 파일을 직접 커밋 후 push
```bash
git add .
git commit -m "Add Event CRM docs and ops starter pack"
git push -u origin main
```

> 즉, 해시 기반 cherry-pick은 해시가 로컬에 있을 때만 동작합니다.

---

## PowerShell에서 `&&` 에러 날 때
오래된 Windows PowerShell(5.x)은 `&&`를 지원하지 않습니다.

### 방법 A) 명령을 한 줄씩 실행
```powershell
git add .
git commit -m "Add Event CRM docs and ops starter pack"
git push -u origin main
```

### 방법 B) 세미콜론(`;`) 사용
```powershell
git add .; git commit -m "Add Event CRM docs and ops starter pack"; git push -u origin main
```

> 참고: PowerShell 7 이상(`pwsh`)에서는 `&&` 사용 가능.

---

## `origin/work`가 안 보일 때 (가장 확실한 방법)
`origin/work`는 **원격에 work 브랜치를 한 번도 push하지 않으면 존재하지 않습니다.**

아래 명령으로 현재 로컬 브랜치를 원격 `work`로 바로 올리세요:

```bash
git push -u origin HEAD:work
```

그 다음:
1. GitHub에서 브랜치 `work`가 생성됐는지 확인
2. `work -> main` PR 생성 후 Merge

### main에 바로 올리고 싶으면
```bash
git push -u origin HEAD:main
```

### 점검 명령
```bash
git remote -v
git branch -vv
git ls-remote --heads origin
```

---

## 머지 후 로컬 싱크(자동)
PR을 GitHub에서 머지한 뒤 로컬을 최신 `main`으로 맞추려면:

### macOS/Linux
```bash
bash scripts/sync_after_merge.sh https://github.com/JeonghaedongVis/EventSptool.git
```

### Windows PowerShell
```powershell
./scripts/sync_after_merge.ps1 -RemoteUrl "https://github.com/JeonghaedongVis/EventSptool.git"
```
