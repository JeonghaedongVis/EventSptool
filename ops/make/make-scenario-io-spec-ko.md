# Make 시나리오 단계별 I/O 명세서 (모듈별 필드 매핑표)

대상 시나리오: `lead/onboard`  
목표: 이벤트별로 달라지는 Google Sheet/Form 입력을 표준 CRM 스키마로 정규화 후 HubSpot + 메시징 채널로 처리

---

## 1) 시나리오 개요

## 트리거
- Webhook (Meta Lead Ads / Google Apps Script / Sheet row trigger)

## 최종 산출
- HubSpot Contact/Deal upsert
- 자동응답 템플릿 발송
- SLA/상태/다음 액션 필드 업데이트
- 실패 시 재시도 큐 + 알림

---

## 2) 모듈 체인 (권장)
1. `M01_Webhook_In`
2. `M02_Validate_Required`
3. `M03_Load_Event_Mapping`
4. `M04_Normalize_Payload`
5. `M05_Dedupe_Check`
6. `M06_Upsert_Contact`
7. `M07_Upsert_Deal`
8. `M08_Assign_Owner_RoundRobin`
9. `M09_Select_Template`
10. `M10_Send_Message`
11. `M11_Update_CRM_Status`
12. `M12_Log_Audit`
13. `M13_Error_Retry_Queue`

---

## 3) 공통 표준 필드(정규화 결과)
| 표준 필드 | 타입 | 설명 |
|---|---|---|
| `lead_external_id` | string | 원천 리드 고유 ID |
| `event_name` | string | 이벤트명 |
| `source_channel` | string | instagram_ads / google_form / google_sheet |
| `submitted_at` | datetime | 원천 제출시각 |
| `mobile_e164` | string | E.164 전화번호 |
| `country_code` | string | ISO2 |
| `preferred_lang` | string | ko/en/ru/kk |
| `interest_service` | string | checkup/spine/intervention |
| `firstname` | string | 이름 |
| `ad_campaign_id` | string | 캠페인 ID |
| `sla_deadline_at` | datetime | 제출+10분 |
| `template_code` | string | 발송 템플릿 코드 |

---

## 4) 모듈별 I/O 명세

## M01_Webhook_In
**Input**: 없음 (외부 진입)  
**Output**: `raw_payload`

예시 Output:
```json
{
  "source": "google_sheet",
  "event_name": "카자흐스탄 4월 검진 이벤트",
  "submitted_at": "2026-04-20T09:10:30Z",
  "row_data": {
    "이름": "홍길동",
    "전화번호": "8 (701) 123-45-67",
    "국가": "Kazakhstan",
    "관심진료": "검진",
    "캠페인ID": "12021188990001"
  }
}
```

## M02_Validate_Required
**Input**: `raw_payload`  
**Rules**:
- 필수: `event_name`, `row_data`, 전화번호 소스 컬럼
- 누락 시: `M13_Error_Retry_Queue`로 이동

**Output**:
- `validation_ok` (bool)
- `validation_errors` (array)

## M03_Load_Event_Mapping
**Input**: `event_name`  
**Lookup Source**: `ops/samples/google-sheet-mapping.csv` (실운영은 Data Store/DB)

**Output**:
- `mapping_rows[]`
  - `source_column_name`
  - `target_field`
  - `transform_rule`
  - `required`

## M04_Normalize_Payload
**Input**: `raw_payload`, `mapping_rows[]`  
**Process**:
- source 컬럼 → 표준 필드 매핑
- transform_rule 적용 (`normalize_phone`, `to_iso2`, `map_service`)
- `sla_deadline_at = submitted_at + 10m`

**Output**: `normalized`
```json
{
  "lead_external_id": "google_sheet:2026-04-20T09:10:30Z:+77011234567",
  "event_name": "카자흐스탄 4월 검진 이벤트",
  "source_channel": "google_sheet",
  "submitted_at": "2026-04-20T09:10:30Z",
  "mobile_e164": "+77011234567",
  "country_code": "KZ",
  "preferred_lang": "ko",
  "interest_service": "checkup",
  "firstname": "홍길동",
  "ad_campaign_id": "12021188990001",
  "sla_deadline_at": "2026-04-20T09:20:30Z"
}
```

## M05_Dedupe_Check
**Input**: `normalized.mobile_e164`, `normalized.event_name`  
**Logic**:
- key = `mobile_e164 + event_name`
- HubSpot 검색 또는 Data Store 해시 조회

**Output**:
- `is_duplicate` (bool)
- `existing_contact_id` (nullable)
- `existing_deal_id` (nullable)

## M06_Upsert_Contact
**Input**: `normalized`, `existing_contact_id`  
**HubSpot Contact Mapping**:
- `mobile_e164 -> phone`
- `firstname -> firstname`
- `country_code -> country_code`
- `preferred_lang -> preferred_lang`
- `interest_service -> interest_service`
- `event_name -> event_name`
- `source_channel -> source_channel`
- `ad_campaign_id -> ad_campaign_id`
- `sla_deadline_at -> sla_deadline_at`

**Output**:
- `contact_id`

## M07_Upsert_Deal
**Input**: `contact_id`, `normalized`, `existing_deal_id`  
**Deal Mapping**:
- `dealname = "{event_name}-{firstname}-{mobile_e164}"`
- `dealstage = new_lead`
- `status_reason = none`
- `next_action_at = submitted_at + 24h`

**Output**:
- `deal_id`

## M08_Assign_Owner_RoundRobin
**Input**: `deal_id`, `country_code`, `interest_service`  
**Rule**:
- 국가/진료 라우팅 그룹 선택 후 순환 배정

**Output**:
- `owner_id`

## M09_Select_Template
**Input**: `preferred_lang`, `interest_service`, `dealstage= new_lead`  
**Rule**:
- 템플릿 키: `btn_checkup_info_{lang}` 또는 서비스별 규칙

**Output**:
- `template_code`
- `template_variables`

## M10_Send_Message
**Input**: `template_code`, `template_variables`, `mobile_e164`, `country_code`  
**Router**:
- KR/카카오 가능권역: Kakao Provider API
- 그 외: WhatsApp Cloud API

**Output**:
- `message_status` (sent/delivered/failed)
- `provider_message_id`
- `provider_error` (nullable)

## M11_Update_CRM_Status
**Input**: `contact_id`, `deal_id`, `message_status`, `template_code`, `owner_id`  
**Update Rules**:
- 성공: `dealstage = auto_replied`
- 실패: `dealstage = new_lead`, `status_reason = message_failed`
- 공통: `last_template_code`, `message_last_status`, `owner_id`

**Output**:
- `crm_update_ok` (bool)

## M12_Log_Audit
**Input**: 전 모듈 결과  
**Output Sink**:
- Make Data Store / BigQuery / Sheet (선택)

로그 필드:
- `run_id`, `event_name`, `contact_id`, `deal_id`, `template_code`, `message_status`, `latency_ms`, `error_code`

## M13_Error_Retry_Queue
**Trigger**:
- 검증 실패 / API 실패 / rate limit / timeout

**Retry Policy**:
- 1회: +1분
- 2회: +5분
- 3회: +15분
- 4회 실패: 담당자 수동 태스크 + Slack 경고

---

## 5) 모듈별 필드 매핑표 (요약)
아래 파일을 함께 사용:
- `ops/make/module-field-mapping.csv`

---

## 6) SLA 계산 규칙
- `sla_deadline_at = submitted_at + 10 minutes`
- `first_response_minutes = first_agent_reply_at - submitted_at`
- `first_response_minutes > 10` 이면 SLA 위반 플래그

---

## 7) 검증 체크리스트 (시나리오 테스트)
- [ ] 서로 다른 이벤트 시트 컬럼 구조 2종 이상에서 정상 매핑
- [ ] 전화번호 정규화 실패 시 에러 큐 이동
- [ ] 중복 리드 시 신규 Deal 남발 방지
- [ ] 메시지 실패 시 재시도 3회 동작
- [ ] 성공 시 `auto_replied` 단계 이동 확인
- [ ] 10분 SLA 타이머 계산 정확성 확인

