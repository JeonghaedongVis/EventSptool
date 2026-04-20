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
