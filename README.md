# ev
ev charger

# 전기차 충전기 카드충전을 가정한 시뮬레이터

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

# 개략적인 작동 절차는 다음과 같다.
 - props.py에 지정된 url, host등을 참조하고, scenario의 이벤트 순서에 따라 송신할 header와 body를 만들어 전송한다.
 - 송신 후 response가 오면 해당 response의 적절성을 검사하고 누락된 정보 등을 noti해 준다.
 - 각 request event별로 request 송신 전/후 생성해야 하는 파라메터 및 충전기내에 저장해야 하는 상태정보 등을 처리한다.

## 상세한 시험 시나리오 작성 방법 등은 scenario.py를 참조 바라며, parameter, response의 변경이 있는 경우 props.py의 수정이 필요하다.
