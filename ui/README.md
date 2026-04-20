# UI MVP 실행 방법

이 화면은 요청하신 흐름을 빠르게 확인하기 위한 프론트 MVP입니다.
이제 UI가 백엔드 API(`backend/mvp_server.py`)와 연결되어 동작합니다.

## 포함된 사용자 흐름
1. 새로운 행사 입력
2. 구글시트 주소 입력/연결
3. 테스트 리드 유입
4. 자동응답 실행
5. 문의응답선택 버튼으로 상태/로그 업데이트

## 실행
```bash
python3 backend/mvp_server.py
# 브라우저에서 http://localhost:8080/ui/ 접속
```

## API 확인
- `GET http://localhost:8080/api/health`
- 데이터 저장 파일: `data/mvp_db.json`
- Instagram New 인입 API: `POST http://localhost:8080/api/ingest/instagram-new`

## 실제 시트(Instagram New) 기준 컬럼 매핑
- `created_time` → `createdAt`
- `platform` (`ig`/`fb`/`M1`) → `platform` 정규화
- `phone_number` (예: `p:+77475789240`) → `phone` (`p:` 제거)
- `full_name` → `name`
- `lead_status` (`CREATED` 등) → `stage` 초기값 결정

## 비고
- 현재는 MVP 데모용 단일 서버(메모리+json 저장)입니다.
- 실제 Make/HubSpot/메시징 API 연동 전 화면·운영 동선 검증용입니다.

## 404가 날 때
- 반드시 저장소 루트에서 실행하세요.
- URL은 `http://localhost:8080/ui/` 처럼 **끝에 슬래시(/)** 를 붙이세요.
