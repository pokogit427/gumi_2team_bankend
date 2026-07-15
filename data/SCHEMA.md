# 지역정보 JSON 스키마 분석서

이 문서는 현재 워크스페이스의 실제 JSON 파일을 직접 읽어 확인한 결과를 바탕으로 작성한 데이터 구조 분석서입니다.

---

## 1. JSON 파일 목록

| 파일명 | contentType | contentTypeId | 항목 수 |
|---|---|---:|---:|
| 구미_경북권_관광지.json | 관광지 | 12 | 499 |
| 구미_경북권_레포츠.json | 레포츠 | 28 | 110 |
| 구미_경북권_문화시설.json | 문화시설 | 14 | 112 |
| 구미_경북권_쇼핑.json | 쇼핑 | 38 | 411 |
| 구미_경북권_숙박.json | 숙박 | 32 | 80 |
| 구미_경북권_여행코스.json | 여행코스 | 25 | 31 |
| 구미_경북권_음식점.json | 음식점 | 39 | 394 |
| 구미_경북권_축제공연행사.json | 축제공연행사 | 15 | 30 |

총합: 1,667건

---

## 2. JSON 최상위 구조

각 파일은 모두 동일한 구조의 객체입니다.

| 필드 | 타입 | 실제 예시 | 설명 |
|---|---|---|---|
| region | string | 구미_경북권 | 권역명 |
| contentType | string | 관광지 | 카테고리 이름 |
| contentTypeId | integer | 12 | 카테고리 ID |
| total | integer | 499 | 해당 파일의 전체 항목 수 |
| items | array | [] | 실제 지역정보 객체 배열 |

---

## 3. 실제 데이터 배열 경로

- 모든 파일의 실제 지역정보 배열은 최상위의 `items` 아래에 있습니다.
- 백엔드에서 사용할 기본 경로는 다음과 같습니다.
  - `data/구미_경북권_관광지.json.items`
  - `data/구미_경북권_음식점.json.items`
  - …

즉, 각 JSON 파일을 읽은 뒤 `data['items']`를 순회하면 됩니다.

---

## 4. 공통 필드명

모든 파일의 항목 객체는 아래 25개 필드를 공통으로 포함합니다.

| 필드 | 타입 | 실제 예시 | 필수 여부 | 빈값 가능 여부 | 비고 |
|---|---|---|---|---|---|
| contentid | string | "3032819" | 예 | 아니오 | 고유 식별자 |
| contenttypeid | string | "12" | 예 | 아니오 | 카테고리 식별자 |
| title | string | "검성지 생태공원" | 예 | 아니오 | 현재 분석 기준 빈값 없음 |
| addr1 | string | "경상북도 구미시 황상동" | 예 | 예 | 여행코스는 일부 비어 있음 |
| addr2 | string | "" | 아니오 | 예 | 빈 문자열 가능 |
| zipcode | string | "39428" | 아니오 | 예 | 일부 값이 비어 있을 수 있음 |
| tel | string | "" | 아니오 | 예 | 빈 문자열 가능 |
| mapx | string | "128.4380860000" | 예 | 아니오 | 문자열이며 숫자 변환 필요 |
| mapy | string | "36.1148440000" | 예 | 아니오 | 문자열이며 숫자 변환 필요 |
| mlevel | string | "6" | 아니오 | 예 | 지도 레벨 |
| areacode | string | "" | 아니오 | 예 | 빈 문자열 가능 |
| sigungucode | string | "" | 아니오 | 예 | 빈 문자열 가능 |
| lDongRegnCd | string | "47" | 아니오 | 예 | 법정동 코드 |
| lDongSignguCd | string | "190" | 아니오 | 예 | 법정동 시군구 코드 |
| cat1 | string | "" | 아니오 | 예 | 대분류 코드 |
| cat2 | string | "" | 아니오 | 예 | 중분류 코드 |
| cat3 | string | "" | 아니오 | 예 | 소분류 코드 |
| lclsSystm1 | string | "NA" | 아니오 | 예 | 분류 체계 1 |
| lclsSystm2 | string | "NA04" | 아니오 | 예 | 분류 체계 2 |
| lclsSystm3 | string | "NA040500" | 아니오 | 예 | 분류 체계 3 |
| firstimage | string | "https://...jpg" | 아니오 | 예 | 이미지 URL |
| firstimage2 | string | "https://...jpg" | 아니오 | 예 | 썸네일 URL |
| cpyrhtDivCd | string | "Type3" | 아니오 | 예 | 저작권 구분 코드 |
| createdtime | string | "20230831114818" | 아니오 | 예 | YYYYMMDDHHmmss |
| modifiedtime | string | "20260616113921" | 아니오 | 예 | YYYYMMDDHHmmss |

---

## 5. 백엔드 응답 필드와의 매핑

아래는 백엔드에서 응답 모델을 만들 때 권장하는 매핑입니다.

| 원본 필드 | 백엔드 응답 필드 | 비고 |
|---|---|---|
| contentid | id | 문자열 유지 또는 int 변환 가능 |
| contenttypeid | contentTypeId | 문자열 유지 |
| title | title | 직접 사용 |
| addr1 | address | addr2를 붙여서 구성 가능 |
| mapx | longitude | 문자열 → float 변환 |
| mapy | latitude | 문자열 → float 변환 |
| firstimage | imageUrl | 빈값이면 firstimage2 사용 가능 |
| firstimage2 | thumbnailUrl | 선택값 |
| createdtime | createdAt | 문자열 → datetime 변환 가능 |
| modifiedtime | updatedAt | 문자열 → datetime 변환 가능 |

---

## 6. contenttypeid별 데이터 개수

| contenttypeid | 카테고리 | 개수 |
|---:|---|---:|
| 12 | 관광지 | 499 |
| 14 | 문화시설 | 112 |
| 15 | 축제공연행사 | 30 |
| 25 | 여행코스 | 31 |
| 28 | 레포츠 | 110 |
| 32 | 숙박 | 80 |
| 38 | 쇼핑 | 411 |
| 39 | 음식점 | 394 |

---

## 7. contenttypeid와 카테고리 이름 대응 관계

| contenttypeid | contentType |
|---:|---|
| 12 | 관광지 |
| 14 | 문화시설 |
| 15 | 축제공연행사 |
| 25 | 여행코스 |
| 28 | 레포츠 |
| 32 | 숙박 |
| 38 | 쇼핑 |
| 39 | 음식점 |

---

## 8. 결측값 및 빈값 통계

| 항목 | 개수 |
|---|---:|
| title이 비어 있는 데이터 | 0 |
| addr1이 비어 있는 데이터 | 29 |
| mapx가 비어 있는 데이터 | 0 |
| mapy가 비어 있는 데이터 | 0 |
| 이미지 필드가 모두 비어 있는 데이터 | 207 |
| contentid 중복 데이터 | 0 |

- `mapx`와 `mapy`는 모두 문자열 타입이며, 실제 값은 문자열로 저장되어 있습니다.
- 이미지 필드는 `firstimage` 또는 `firstimage2`가 비어 있는 경우가 많습니다.

---

## 9. 좌표 변환 규칙

- `mapx`, `mapy`는 현재 JSON에서 문자열 타입으로 저장되어 있습니다.
- 백엔드에서 사용할 때는 다음 규칙으로 변환하는 것이 안전합니다.
  - 빈 문자열이면 `None`으로 처리
  - 그 외에는 `float(mapx)`, `float(mapy)`로 변환
  - 응답 모델에서는 `longitude`, `latitude` 같은 숫자형 필드로 노출

---

## 10. 날짜 변환 규칙

- `createdtime`, `modifiedtime`은 문자열 형태로 제공됩니다.
- 형식은 `YYYYMMDDHHmmss`로 보입니다.
- 백엔드에서 필요 시 다음처럼 변환할 수 있습니다.
  - `datetime.strptime(value, "%Y%m%d%H%M%S")`
- 현재 확인된 파일에는 축제 시작일/종료일 필드(`eventstartdate`, `eventenddate`)는 존재하지 않습니다.

---

## 11. 결측값 처리 규칙

- 빈 문자열은 백엔드에서 `None` 또는 `""` 중 하나로 통일해 처리하는 것이 좋습니다.
- 권장 규칙은 다음과 같습니다.
  - `title`이 비어 있으면 `"제목 없음"`으로 치환
  - `addr1`이 비어 있으면 `address = None` 또는 `"주소 미제공"`
  - `mapx`/`mapy`가 비어 있으면 좌표 정보는 `None`
  - `firstimage`가 비어 있으면 `firstimage2`를 사용하고, 둘 다 없으면 `imageUrl = None`

---

## 12. 파일별 데이터 구조 차이

실제 확인 결과, 8개 파일 모두 동일한 최상위 구조와 항목 필드 구성을 가집니다.

- 차이점은 거의 없고, 파일별로 `contentType`, `contentTypeId`, `total`, `items`의 값만 다릅니다.
- 따라서 백엔드에서는 공통 모델 하나로 처리해도 됩니다.

---

## 13. 구미/경북권 데이터인지 확인할 수 있는 근거

다음 근거로 구미/경북권 데이터임을 확인할 수 있습니다.

- 각 JSON 파일의 최상위 `region` 값이 모두 `"구미_경북권"`입니다.
- 파일명도 `구미_경북권_...` 형식입니다.
- 제공된 데이터 집합이 구미/경북권 관광정보로 명명되어 있습니다.
