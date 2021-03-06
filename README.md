# ev
ev charger

## 전기차 충전기 카드충전을 가정한 시뮬레이터

 본 문서는 ocpp 1.6 기반 전기차 충전시스템의 충전기 모듈에 대한 시뮬레이션을 위해 만들어졌으며,
 ocpp websoket 방식 전기차충전기가 아닌, http방식으로 변경한 충전기 시뮬레이터이다.
 사용 하기 위해 python 3.x를 설치 해야 하며, 추가로 설치 해야 하는 모듈은 아래와 같다.
 - requests
 - colorlog

 4개의 파일을 같은 폴더에 설치하고 위의 모듈을 설치 한 후 아래와 같이 실행 한다.
 app.py 파일은 향후 oneM2M을 통한 명령 수신을 가정한 충전기 서버 구성을 위한 것으로 무시.

> $ python charger.py

 테스트 케이스는 scenario.py에 임의로 몇개가 지정 되어 있으며,
 해당 파일을 고쳐서 다양한 케이스를 시험 할 수 있다.

 props.py 에는 중계서버와 중계기 이벤트(boot, authorize, statusNotification 등)의 api url을 정의 할 수 있다.

 기본 로그는 중계기로 보내는 header, body를 보여주고, response를 보여준다.

## 개략적인 작동 절차는 다음과 같다.

- props.py에 지정된 url, host등을 참조하고, scenario의 이벤트 순서에 따라 송신할 header와 body를 만들어 전송한다.
 - 송신 후 response가 오면 해당 response의 적절성을 검사하고 누락된 정보 등을 noti해 준다.
 - 각 request event별로 request 송신 전/후 생성해야 하는 파라메터 및 충전기내에 저장해야 하는 상태정보 등을 처리한다.

### 상세한 시험 시나리오 작성 예제는 아래와 같다.
```python
#일반 충전/종료 케이스
normal_case = [
    ["boot", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
    ["statusNotification", "Charging"],
    ["meterValue"],
    ["stopTransaction", "Finished"],
    ["statusNotification", "Finishing"],
    ["statusNotification", "Available"],
    ["heartbeat", None]
]
```
위의 예제는 boot notification(reason:PowerUp) 후 충전기 상태를 Available로 바꾼 후, authorize로 카드 태깅이 이루어 진 후
다시 상태를 Preparing으로 변경하고, 해당 idtag의 카드 기준의 tarfiff를 조회 한다.
이후 transaction을 시작하여, 충전중(Charging) 상태로 변경하고 미터값을 반복해서 발생 시키고 끝나면 Finish상태로 바꾸면서 상태를 CS로 올린다.
이후 다시 상태를 Available로 변경하고 이후 heartbeat을 발생 시킨다.
상헤한 케이스 작성 방법 등은 scenario.py를 참조 바라며, parameter, response의 변경이 있는 경우 props.py의 수정이 필요하다.

## 주의 : 완성된 상태가 아니며, CS(Central System)과 서로 맞춰가며 테스트가 필요함
