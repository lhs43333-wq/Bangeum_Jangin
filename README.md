# 방음장인 웹 앱 + Windows 도우미

방구석 음향 장인. 스피커 소리를 측정해 방에 맞게 보정하는 웹 앱입니다.

## 구성

| 경로 | 역할 |
| --- | --- |
| docs/index.html | PC에서 여는 웹 앱 (가이드, 측정, 자동 보정, 한·영) |
| docs/phone.html | 스마트폰을 마이크로 쓸 때 폰에서 열리는 페이지 |
| docs/vendor/ | PeerJS(폰 연결), qrcode-generator(QR 코드). 둘 다 MIT 라이선스 |
| helper/bangeum_helper.py | 설정을 Equalizer APO 폴더에 쓰는 Windows 도우미 |
| test/ | 계산 코드와 브라우저 흐름 검증 스크립트 |

## GitHub Pages에 올리기

1. GitHub에서 새 저장소를 만들고(예: `bangeum-jangin`) 이 폴더 전체를 올립니다.
2. 저장소의 Settings > Pages에서 "Deploy from a branch", 브랜치 `main`, 폴더 `/docs`를 고릅니다.
3. 몇 분 뒤 `https://아이디.github.io/bangeum-jangin/` 에서 열립니다.

## 사용 (PC)

1. 위 주소를 PC 브라우저(Chrome 또는 Edge 권장)에서 엽니다.
2. PC 전체 적용까지 하려면 도우미를 실행합니다.

       python helper\bangeum_helper.py --no-browser --allow-origin https://아이디.github.io

   도우미 없이도 측정과 설정 파일 내려받기는 됩니다.
3. 스마트폰을 마이크로 쓰려면 1단계에서 "스마트폰"을 고르고 QR 코드를 폰 카메라로 찍습니다.

## 스마트폰 연결 방식

- PC와 폰은 WebRTC 데이터 채널로 직접 연결됩니다. 녹음은 폰에서 PC로만 전달됩니다.
- 처음 연결을 맺을 때만 PeerJS의 공개 중계 서버(0.peerjs.com)를 거칩니다. 무료 공용 서비스라 가끔 느리거나 멈출 수 있습니다.
  안정적으로 운영하려면 자체 PeerServer를 두고 `peerOptions()`를 바꾸면 됩니다.
- 폰 마이크는 일반 마이크로 취급해 300 Hz 이하만 보정합니다.

## 도우미가 하는 일과 제한

- 이 PC(127.0.0.1)에서 온 요청, 그리고 `--allow-origin`으로 허용한 주소의 요청만 받습니다.
- Preamp, Channel, 피킹 필터 줄만 쓸 수 있습니다. `bangeum_eq.txt` 한 파일만 쓰고,
  config.txt에는 `Include: bangeum_eq.txt` 한 줄만 추가합니다(처음에 config.txt 백업).

## 확인된 것과 아닌 것

- 확인: 계산 코드(가상의 방), 체험 모드, 도우미 적용·끄기와 요청 차단,
  PC 페이지와 폰 페이지의 연결·음량 표시·녹음 전송(한 컴퓨터의 브라우저 두 개와 로컬 중계 서버로 시험).
- 미확인: 실제 폰(iOS Safari, Android Chrome)에서의 동작, 공개 중계 서버를 통한 연결,
  GitHub Pages 주소에서 도우미로 보내는 요청(브라우저가 로컬 네트워크 접근 허용을 물을 수 있음),
  실제 스피커와 마이크 측정.
