# Event CRM Ops Starter Pack

다음 파일들은 문서 수준을 넘어 실제 설정/구축 시 바로 참조할 수 있는 **운영 아티팩트 샘플**입니다.

## 파일 구성
- `config/hubspot-properties.json`: HubSpot Contact/Deal 커스텀 속성 정의 샘플
- `config/pipeline-stages.json`: 파이프라인 단계 키/순서 샘플
- `config/response-buttons.json`: 상담사 응대 버튼 동작 정의
- `templates/message-templates.json`: 메시지 템플릿 코드/문구 샘플
- `samples/google-sheet-mapping.csv`: 이벤트별 시트 컬럼 매핑 샘플
- `samples/incoming-webhook-payload.json`: 유입 payload 샘플

## 사용 방법 (권장)
1. 이벤트 시작 전 `samples/google-sheet-mapping.csv`를 이벤트별로 복제해 컬럼 매핑 확정
2. `hubspot-properties.json` 기준으로 내부키를 고정 생성
3. `pipeline-stages.json` 단계키를 CRM과 동기화
4. `response-buttons.json` + `message-templates.json` 조합으로 버튼 액션 구성
5. 샘플 payload로 E2E 테스트 후 운영 전환

## 주의
- 실제 API 스키마는 사용 중인 HubSpot 버전/메시징 공급사 사양에 맞춰 조정 필요
- 템플릿은 국가별 정책/승인 절차(카카오/WhatsApp)에 맞춰 사전 승인 필요


## 검증(Validation)
다음 명령으로 산출물 무결성을 빠르게 점검할 수 있습니다.

```bash
python3 scripts/validate_ops_artifacts.py
```

검증 항목:
- 필수 파일 존재 여부
- JSON 문법 검사
- Make 모듈 매핑 CSV 헤더/빈값 검사
- CSV 출력 필드와 I/O 명세서 텍스트 간 교차 점검


## 현재 상태 점검
아래 명령으로 Git/원격/산출물/검증 결과를 한 번에 확인할 수 있습니다.

```bash
bash scripts/check_current_status.sh
```

```powershell
./scripts/check_current_status.ps1
```
