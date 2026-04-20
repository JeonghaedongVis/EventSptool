# 이벤트 CRM 구현 플레이북 (다음 턴: 바로 구축 가능한 수준)

본 문서는 `docs/event-crm-blueprint-ko.md`의 후속 실행안입니다.
목표는 **운영팀이 1~2주 내 MVP를 실제 가동**할 수 있도록, 필드/워크플로우/템플릿을 바로 복사해 설정하는 것입니다.

---

## 0) 이번 턴 산출물
- HubSpot 속성(필드) 표준 명세
- 파이프라인/단계별 자동화 트리거
- Make 시나리오 모듈 설계(에러/재시도 포함)
- 상담사 버튼 액션(템플릿/상태 전환) 정의
- SLA 관제 규칙 + 일일 운영 루틴
- 메시지 템플릿 초안 (KR/EN)
- UAT 체크리스트(실행 검증표)

---

## 1) HubSpot 설정 명세

## 1-1. Contact 속성 (필수)
| 속성명(내부키) | 타입 | 예시 | 비고 |
|---|---|---|---|
| `lead_external_id` | single-line text | `meta_2384...` | 유입 소스 원본 ID |
| `mobile_e164` | phone number/text | `+7701xxxxxxx` | 전화번호 정규화 결과 |
| `country_code` | dropdown select | `KZ`, `KR` | ISO2 권장 |
| `preferred_lang` | dropdown select | `ko`, `ru`, `en` | 메시지 템플릿 분기 |
| `interest_service` | dropdown select | `checkup/spine/intervention` | 관심 진료 |
| `event_name` | single-line text | `카자흐스탄 4월 검진 이벤트` | 이벤트 태그 핵심 |
| `source_channel` | dropdown select | `instagram_ads`, `google_form` | 유입 채널 |
| `ad_campaign_id` | single-line text | `1202...` | 광고 성과 집계 |
| `first_response_at` | datetime | `2026-04-20T09:13:00Z` | 최초 응대 시각 |
| `sla_deadline_at` | datetime | `2026-04-20T09:20:00Z` | 생성+10분 |
| `first_response_minutes` | number | `4.2` | SLA 분석 핵심 |

## 1-2. Deal(상담건) 속성 (필수)
| 속성명(내부키) | 타입 | 예시 | 비고 |
|---|---|---|---|
| `dealstage` | pipeline stage | `new_lead` | 단계 관리 |
| `owner_id` | hubspot owner | `홍길동` | 라운드로빈 배정 |
| `next_action_at` | datetime | `2026-04-20T17:00:00Z` | 리마인드 기준 |
| `status_reason` | dropdown | `no_answer`, `price_pending` | 상태 사유 |
| `last_template_code` | single-line text | `btn_price_info_kr` | 품질 추적 |
| `message_last_status` | dropdown | `sent/delivered/failed` | 전송 상태 |

## 1-3. Pipeline 단계값 (권장)
1. `new_lead` (신규 리드)
2. `auto_replied` (자동응답 완료)
3. `consulting` (상담 진행중)
4. `booking_push` (예약 유도)
5. `booked` (예약 완료)
6. `no_response` (미응답)
7. `recontact_needed` (재접촉 필요)

---

## 2) 자동화 설계 (HubSpot Workflow + Make)

## 2-1. Workflow A: 신규 리드 생성 후 즉시 처리
**Trigger:** Contact 생성 AND `mobile_e164` is known

**Actions:**
1. `sla_deadline_at = createdate + 10min`
2. Deal 생성(없으면)
3. Deal stage → `new_lead`
4. Owner 라운드로빈 배정
5. Make webhook 호출 (`/lead/onboard`)

---

## 2-2. Make Scenario: `/lead/onboard`

### 모듈 순서
1. **Webhook** (HubSpot payload 수신)
2. **Data Store 조회**: dedupe key(`mobile_e164 + event_name`)
3. **Router**
   - 신규: 계속 진행
   - 중복: note만 추가 후 종료
4. **Mapping Resolver**
   - `event_name` 기준 mapping table 조회
5. **Normalizer**
   - 전화번호, 국가코드, 언어 fallback 정리
6. **Message Sender**
   - KR: Kakao provider API
   - 글로벌: WhatsApp Cloud API
7. **HubSpot Update**
   - stage=`auto_replied`
   - `message_last_status`, `last_template_code` 업데이트
8. **Error Handler**
   - 실패시 retry queue 저장 + Slack 알림

### 재시도 정책
- 1차 실패: 1분 후 재시도
- 2차 실패: 5분 후 재시도
- 3차 실패: 담당자 수동응대 태스크 생성 + 팀 채널 경고

---

## 2-3. Workflow B: SLA 미준수 감시
**Trigger:** 매 5분 스케줄

**조건:**
- `first_response_at` unknown
- `now > sla_deadline_at`
- `dealstage != booked`

**Actions:**
1. 담당자 DM/이메일 알림
2. 20분 초과 시 팀장 에스컬레이션
3. Deal stage → `no_response`
4. `status_reason = no_answer`

---

## 2-4. Workflow C: 하루 2회 운영 점검
**스케줄:** 10:00, 17:00 (현지 시간)

**출력:**
- 담당자별 `no_response`, `recontact_needed` 건수
- SLA 위반 리드 목록
- 재배정 추천 리스트

---

## 3) 응대 버튼(상담사 UX) 사양

## 3-1. 버튼 정의
| 버튼명 | 템플릿 코드 | 단계 이동 | 다음 액션 |
|---|---|---|---|
| 검진 안내 보내기 | `btn_checkup_info_{lang}` | `consulting` | +24h |
| 가격 안내 보내기 | `btn_price_info_{lang}` | `consulting` | +24h |
| 예약 유도 메시지 | `btn_booking_push_{lang}` | `booking_push` | +12h |
| 재문의 유도 | `btn_reengage_{lang}` | `recontact_needed` | +48h |

## 3-2. 버튼 클릭 공통 액션
1. 템플릿 발송
2. Message Log 기록
3. Deal stage 갱신
4. `next_action_at` 자동 세팅
5. 발송 실패시 재시도 큐 적재

---

## 4) 메시지 템플릿 초안

## 4-1. KR - 검진 안내
```
안녕하세요 {{name}}님,
문의주신 {{interest_service}} 관련 기본 검진 안내드립니다.
가장 빠른 예약 가능 시간은 {{available_slots}} 입니다.
원하시면 바로 예약 도와드릴게요.
```

## 4-2. KR - 예약 유도
```
{{name}}님, 현재 {{available_slots}} 슬롯이 가능합니다.
원하시는 시간 알려주시면 바로 예약 확정 도와드리겠습니다.
```

## 4-3. EN - Intro
```
Hi {{name}}, thanks for your inquiry.
We can help you with {{interest_service}} consultation.
Available slots: {{available_slots}}.
Reply with your preferred time and we will book it for you.
```

> 운영 팁: 템플릿은 국가/언어별 승인 리드타임이 있으므로 이벤트 시작 최소 7일 전에 승인 완료.

---

## 5) UAT(운영 검수) 체크리스트

## 5-1. 기능 테스트
- [ ] 신규 리드 생성 후 1분 내 자동 메시지 발송
- [ ] 10분 내 수동응대 없으면 알림 발송
- [ ] 버튼 클릭 시 템플릿 전송 + 단계 이동 확인
- [ ] 중복 리드 입력 시 중복 차단/병합 처리
- [ ] 실패 재시도 3회 후 에스컬레이션 생성

## 5-2. 데이터 테스트
- [ ] `event_name`, `country_code`, `interest_service` 누락률 < 1%
- [ ] `first_response_minutes` 계산 정확성 검증
- [ ] 메시지 로그와 CRM 상태 정합성 확인

## 5-3. 운영 리허설
- [ ] 담당자 3명 라운드로빈 균등 분배
- [ ] 하루 2회 점검 리포트 자동 발송
- [ ] 팀장 에스컬레이션 수신 확인

---

## 6) 7일 실행 계획 (실무형)
- **Day 1:** 필드/파이프라인 생성, 권한 설정
- **Day 2:** Make 시나리오 구축(신규 유입 + 자동메시지)
- **Day 3:** 라운드로빈/미응답 워크플로우 구축
- **Day 4:** 버튼 액션 + 템플릿 연동
- **Day 5:** UAT 1차, 실패 재시도/알림 튜닝
- **Day 6:** 실제 이벤트 샘플 데이터 리허설
- **Day 7:** 운영 전환 + 모니터링

---

## 7) 다음 액션(권장)
1. 현재 사용 중인 메신저 공급사(카카오/WhatsApp) 확정
2. 첫 이벤트의 실제 시트 컬럼 샘플 1개 확보
3. 본 문서 기준으로 내부키(속성명) 확정 후 즉시 구축 시작