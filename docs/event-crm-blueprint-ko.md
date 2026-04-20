# 이벤트 대응 CRM 시스템 설계안 (Google Sheet 가변 구조 대응)

## 1) 목표 요약
- **목표:** 인스타 광고 유입 리드를 5~10분 이내 1차 응대하고, 상담 생산성과 표준화를 동시에 달성.
- **핵심 포인트:**
  - 속도 자동화 (즉시 메시지, 자동 배정, 미응답 추적)
  - 직원 응대 표준화 (버튼형 스크립트)
  - 파이프라인 운영 (드래그형 단계 관리)
  - 이벤트별 성과 분석 (태그/캠페인 기준 집계)

---

## 2) 현실적인 BEST 조합 (권장 스택)

### A안: **HubSpot + Make + WhatsApp Cloud API + 카카오 알림톡 공급사** (권장)
- **CRM:** HubSpot Sales/Service Hub
- **자동화 오케스트레이션:** Make
- **채널:**
  - 해외/글로벌: WhatsApp Business Platform(Cloud API)
  - 한국: 카카오 비즈메시지(알림톡/친구톡, 공식 공급사 경유)
- **입력 소스:** Google Form/Google Sheet, Meta Lead Ads
- **이유:**
  - 운영자가 쓰기 쉬운 UI + 파이프라인 보드 + 기본 리포트
  - 워크플로우/소유자 라우팅/알림 기능이 성숙
  - Make로 시트 구조가 바뀌어도 매핑 레이어를 분리해 대응 가능

### B안: **GoHighLevel + n8n + WhatsApp** (비용 민감형)
- 장점: 자동화/퍼널 기능이 강하고 비교적 저비용.
- 단점: 엔터프라이즈 관점 데이터 거버넌스/권한/감사 추적은 HubSpot 대비 약할 수 있음.

### C안: **Airtable Interface + Make + 메시징 API** (초고속 MVP)
- 장점: 화면/버튼/뷰 구성 매우 빠름.
- 단점: CRM 고급기능(권한·고급 리포트·대규모 운영) 확장 시 재구성 가능성.

---

## 3) 요구사항 매핑

### 핵심1: 속도 자동화 (5분 내 응답)
1. 리드 유입 즉시 webhook 수신
2. CRM 레코드 생성 + 이벤트 태그 자동 부여
3. 즉시 자동 메시지 발송 (채널별 템플릿)
4. 응답 없으면 10분 알림(담당자/팀 리더)
5. 1일 2회 미응답 배치 점검

### 핵심2: 직원 응대 표준화
- CRM 레코드 우측 패널/커스텀 카드에 **“응대 버튼”** 제공:
  - `[검진 안내 보내기]`
  - `[가격 안내 보내기]`
  - `[예약 유도 메시지]`
  - `[재문의 유도]`
- 버튼 클릭 시:
  - 템플릿 전송
  - 전송 로그 저장
  - 상태 자동 변경(예: 상담 진행중)
  - 다음 리마인드 자동 예약

### 핵심3: 파이프라인 구조
- 단계(권장):
  1) 신규 리드
  2) 자동응답 완료
  3) 상담 진행중
  4) 예약 유도
  5) 예약 완료
  6) 미응답
  7) 재접촉 필요
- 보드(Kanban)에서 드래그 이동 + 단계 진입 시 자동 액션

### 핵심4: 행사 태그 관리
- 필수 속성:
  - `event_name` (예: 카자흐스탄 4월 검진 이벤트)
  - `country`
  - `interest_service` (검진/척추/인터벤션)
- 운영/분석용 추가 권장:
  - `source` (instagram_ads / organic / referral)
  - `ad_campaign_id`, `adset_id`, `creative_id`
  - `sla_deadline_at`, `first_response_at`, `first_response_minutes`

---

## 4) “행사마다 다른 구글시트” 대응 설계

문제: 시트 컬럼 이름/순서가 행사마다 다름.

해결: **2단 매핑 구조**
1. `raw payload` 원본 저장 (JSON 그대로)
2. `mapping table`로 표준 CRM 필드로 변환

### 매핑 테이블 예시
- `event_id`
- `source_sheet_id`
- `source_column_name`
- `target_field`
- `transform_rule` (전화번호 정규화, 국가코드 변환 등)

### 동작
- 새 이벤트 시작 시 매핑 테이블만 10~20분 세팅
- 자동화 본체는 재사용
- 컬럼 변경이 와도 매핑 업데이트로 복구

---

## 5) 권장 아키텍처

```text
Instagram Lead Ads / Google Form
        ↓
   (Webhook/Sheet trigger)
        ↓
     Make Scenario
  - dedupe
  - normalize
  - field mapping
  - SLA timer set
        ↓
      HubSpot CRM
  - contact/deal 생성
  - owner round-robin 배정
  - pipeline stage 설정
        ↓
Messaging Layer
- WhatsApp Cloud API
- Kakao BizMessage provider API
        ↓
Ops Alerts
- Slack/Email/Telegram
- 미응답, SLA 초과, 실패 재시도 알림
```

---

## 6) 데이터 모델(최소)

### Contact(리드)
- `lead_id` (외부키)
- 이름, 전화번호, 국가, 언어
- 관심진료, 이벤트명
- 최초유입시각, 최초응답시각, 응답속도(분)

### Opportunity(상담건)
- 파이프라인 단계
- 담당자(owner)
- 다음 액션일시(next_action_at)
- 상태 사유코드(status_reason)

### Message Log
- 채널(카톡/WhatsApp)
- 템플릿 코드
- 발송/성공/실패 상태
- 공급사 message_id
- 실패 사유

### SLA Log
- SLA 목표(예: 10분)
- 경과시간
- 위반여부
- 위반 알림 시각

---

## 7) 자동화 플로우(실행 수준)

### 플로우 1: 신규 리드 등록
- Trigger: Form submit / Sheet new row / Meta lead webhook
- Steps:
  1. 필수값 검증(전화번호, 국가, 이벤트명)
  2. 중복 체크(전화번호+이벤트 기준)
  3. Contact/Deal upsert
  4. 오너 자동배정(round-robin)
  5. 즉시 자동 메시지 전송
  6. `자동응답 완료` 단계 이동
  7. `SLA 타이머` 시작

### 플로우 2: 미응답 감시
- Trigger: 5분 주기 스케줄러
- 조건:
  - `first_agent_reply_at IS NULL`
  - `created_at + 10분 < now`
- 액션:
  - 담당자 DM 알림
  - 팀장 escalation
  - 상태 `미응답` 이동

### 플로우 3: 응대 버튼 액션
- Trigger: CRM 버튼 클릭(커스텀 액션)
- 액션:
  - 템플릿 전송
  - 메시지 로그 기록
  - 단계 자동 이동
  - 다음 팔로업 생성

### 플로우 4: 하루 2회 점검
- Trigger: 10:00 / 17:00 배치
- 액션:
  - `미응답`, `재접촉 필요` 목록 생성
  - 담당자별 할당량 리밸런싱
  - 일일 운영 리포트 전송

---

## 8) 메시지 템플릿 구조(예시)

### 템플릿 키 규칙
`{country}_{service}_{stage}_{purpose}`
예: `KZ_checkup_new_intro`

### 버튼별 템플릿 예시
- `btn_checkup_info`
- `btn_price_info`
- `btn_booking_push`
- `btn_reengage`

각 템플릿은 아래 변수를 사용:
- `{{name}}`, `{{hospital_name}}`, `{{available_slots}}`, `{{consultant_name}}`, `{{booking_link}}`

---

## 9) 직원용 화면 설계 (최소 클릭)

### 화면 1: 오늘 신규 리드 큐
- 컬럼: 이름/국가/이벤트/경과분/상태/담당자
- 상단 필터: 내 담당, 10분 초과, 국가별

### 화면 2: 상담 상세 패널
- 상단: 고객 기본정보 + 태그
- 중단: 대화 히스토리
- 우측: **응대 버튼 4종**
- 하단: 다음 액션/리마인드 설정

### 화면 3: 미응답 관제 보드
- SLA 초과건 우선 정렬
- 원클릭 재배정

---

## 10) SLA 운영 룰(필수)
- 1차 응답 목표: **10분 이내** (권장 5분)
- 10분 초과 시 자동 경고
- 30분 초과 시 팀장 에스컬레이션
- 하루 2회 미응답 리뷰(10:00, 17:00)
- 주간 리포트:
  - 평균 응답시간
  - SLA 준수율
  - 이벤트별 예약 전환율

---

## 11) 도입 로드맵

### Phase 1 (1~2주): MVP
- 단일 이벤트 연동
- 자동 등록 + 즉시 자동메시지 + 라운드로빈 + 미응답 알림
- 기본 파이프라인

### Phase 2 (2~4주): 운영 고도화
- 버튼형 스크립트 + 템플릿 버전관리
- 국가/진료별 분기 로직
- 리마인드 자동화 강화

### Phase 3 (4~8주): 분석/최적화
- 이벤트별 CAC/예약률 대시보드
- 상담사 성과 리포트
- 응답 스크립트 A/B 테스트

---

## 12) 리스크와 대응
- **카카오/WhatsApp 템플릿 승인 지연** → 이벤트 전 최소 1주 승인 완료
- **시트 컬럼 변경** → 매핑 테이블로 흡수
- **중복 리드 폭증** → 전화번호 정규화 + dedupe 룰
- **담당자 편중** → 라운드로빈 + 재분배 배치
- **전송 실패** → 재시도 큐 + fallback(SMS)

---

## 13) 운영 KPI (최소)
- `first_response_median_minutes`
- `sla_10m_compliance_rate`
- `no_response_rate`
- `booking_conversion_rate`
- `recontact_success_rate`
- 이벤트/국가/관심진료별 분해 지표

---

## 14) 벤더/기술 체크리스트
- webhook 지연시간 SLA
- 메시지 템플릿 승인/관리 UX
- 발송 성공/실패 콜백 제공 여부
- API rate limit
- 개인정보 마스킹/권한제어/접속로그
- 다국어 템플릿 지원

---

## 15) 결론
가장 현실적인 시작점은 **HubSpot + Make + (WhatsApp Cloud API + 카카오 비즈메시지 공급사)** 조합입니다.
핵심은 “툴”보다 **매핑 레이어 + 버튼형 표준 응대 + SLA 관제**를 먼저 고정하는 것입니다.
이 3가지를 먼저 만들면 행사/국가가 바뀌어도 반복 가능한 운영 시스템이 됩니다.