# Pull Request 형태로만 작업하는 방법 (merge commit 최소화)

## 핵심 원칙
- `main`에는 직접 commit/push 하지 않기
- 항상 기능 브랜치(`feat/...`)에서 작업 후 PR 생성
- 로컬 pull 전략을 rebase/ff-only로 설정하여 불필요한 merge commit 방지

## 1) 1회 설정
```bash
git config --global pull.rebase true
git config --global pull.ff only
git config --global rebase.autoStash true
```

## 2) 작업 시작
```bash
git checkout main
git pull origin main --ff-only
git checkout -b feat/event-crm-ui
```

## 3) 작업/커밋
```bash
git add .
git commit -m "feat: implement event crm ui flow"
```

## 4) 원격 브랜치 push + PR
```bash
git push -u origin feat/event-crm-ui
```
- GitHub에서 `Compare & pull request` 클릭
- base=`main`, compare=`feat/event-crm-ui`

## 5) 머지 전략 권장
- **Squash and merge** (커밋 히스토리 정리)
- 또는 **Rebase and merge** (선형 히스토리)
- Merge commit 방식은 지양

## PowerShell (한 줄 체이닝 금지 환경)
PowerShell 5.x에서는 `&&` 대신 줄바꿈 또는 `;` 사용.
