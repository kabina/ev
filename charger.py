#!/usr/bin/python
# -*- coding: utf-8 -*-
"""전기차 충전기 시뮬레이터

     * 안창선
     * 2022-05-27

Todo:
   TODO리스트를 기재
    * 비정상 케이스에 대한 프로세스 적용
    * ID값들 자동화 처리 필요


"""
import random
from abc import *
from datetime import datetime
import requests
import json
import props
import scenario
import time
from evlogger import Logger

logger = Logger()
evlogger = logger.initLogger()

"""랜덤으로 ID태깅이 이루어 지는 경우 사용될 테스트 ID들
"""
idTags = [
    "5555222233334444",
    "3333222233334444",
    "1111222233336666",
    "1010202030306060"
]


class Server(metaclass=ABCMeta):
    @abstractmethod

    def make_request(self, request_type):
        pass


class Charger(Server):
    """충전기 클래스 선언

     충전기는 CS로 요청을 보내기도 하고, 자체 서버를 띄워 요청을 받을 수도 있어야 함(HTTP)

    Attributes:
        Server (Class): 서버 클래스의 abstract class inherit

    """

    def __init__(self, charger_id=None):

        if charger_id is None or len(charger_id) !=14 :
            logger.error("충전기ID 오류로 충전기를 생성 할 수 없습니다.")
            return

        self.stop_by_error = False  # CS로 부터 Response 정보가 부족하더라도 시뮬레이트 계속 작동
        self.local_var = {
            "transactionId": None,
            "heartbeatInterval": 5,
            "vendorId": "LGE",
            "connectorId": None,
            "status": "Available",
            "errorCode": "NoError",
            "boot_reason": None,
            "stopTransaction_reason": None,
            "statusNotification_reason": None,
            "meterStart": None,
            "meterStop": None,
            "idTag": None,
            "X-EVC-MDL": "LGE-123",
            "X-EVC-BOX": None,
            "X-EVC-OS": "Linux 5.5",
            "tariff": [],
            "responseFailure": False,
        }

        # meterValue용 파라메터 변수 들 (기본값)

        self.sampled_value = {
            "cimport": 12,  # Current.Import, 충전전류(A)
            "voltage": 220.0,  # Voltage
            "eairegister": 0,  # Energy.Active.Import.Register (Wh)
            "soc": 10,  # SoC
            "paimport": 0,  # Power.Active.Import 충전기로 지속 충전되는 양 (W)
        }

        self.local_var["X-EVC-BOX"] = charger_id[:12]
        self.local_var["connectorId"] = charger_id[12:]

        self.setter = {
            "timestamp": lambda x: datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z") + "Z",
            "transactionId": lambda x: self.local_var[x],
            "vendorId": lambda x: self.local_var[x],
            "connectorId": lambda x: self.local_var[x],
            "status": lambda x: self.local_var[x],
            "meterStart": lambda x: self.local_var[x],
            "meterStop": lambda x: self.local_var[x],
            "errorCode": lambda x: self.local_var[x],
            "boot_reason": lambda x: self.local_var[x],
            "idTag": lambda x: idTags[random.randrange(0, len(idTags))],
            "stopTransaction_reason": lambda x: self.local_var[x],
            "statusNotification_reason": lambda x: self.local_var[x],
        }


    def init_local_var(self,):
        fixed = [
            "vendorId",
            "X-EVC-BOX",
            "X-EVC-MDL",
            "X-EVC-OS",
            "heartbeatInterval",
            "connectorId",
        ]
        for item in self.local_var:
            if item not in fixed:
                self.local_var[item] = None

    def disp_header(self, command):
        evlogger.info("#" * 50)
        evlogger.info("############# - Request for {}".format(command))
        evlogger.info("#" * 50)

    def update_var(self, item, value):
        self.local_var[item] = value


    # def update_var(self, *args, **kwargs):
    #     for item in kwargs:
    #         self.local_var[item[0]] = item[1]

    def login(self, userid, password):

        data = {"userId": userid, "userPw": password}
        response = requests.post(props.urls["login"], headers=props.headers,
                                 data=json.dumps(data))
        response_dict = json.loads(response.text)
        self.accessToken = response_dict["payload"]["accessToken"]

    def meter_update(self, command=None):
        self.sampled_value["cimport"] += self.sampled_value["cimport"] + random.uniform(-1,1)
        self.sampled_value["voltage"] = self.sampled_value["voltage"] + random.uniform(-1,1)
        self.sampled_value["eairegister"] = (self.sampled_value["eairegister"]+1000 +
                                    random.uniform(-1,1) ) if command == "meterValues" else 0
        self.sampled_value["soc"] = self.sampled_value["soc"]
        self.sampled_value["paimport"] += self.sampled_value["paimport"] + random.uniform(-1,1)

        self.update_var("meterStop",self.sampled_value["paimport"])

    def get_sampledValue(self):
        self.meter_update(command="meterValues")
        value = [
            {   "measurand": "Current.Import", "phase": "L1", "unit": "A", "value":
                "{:.1f}".format(self.sampled_value["cimport"]),  # Wh Value
            }, {"measurand": "Voltage", "phase": "L1", "unit": "V", "value":
                "{:.1f}".format(self.sampled_value["voltage"]),
            }, {"measurand": "Energy.Active.Import.Register", "unit": "Wh", "value":
                "{:.1f}".format(self.sampled_value["eairegister"])
            }, {"measurand": "SoC", "unit": "%", "value":
                "{}".format(self.sampled_value["soc"],)
            }, {"measurand": "Power.Active.Import", "unit": "W", "value":
                "{:.1f}".format(self.sampled_value["paimport"])
            }
        ]
        return value

    def send_response(response):
        print(response)

    def ltouch_parameter(self, parameter, command=None):
        """Request시 정의된 JSON내 변경이 필요한 항목을 탐색하여 수정함.
        timestamp나 transactionId등을 해당 시점에 맞는 값으로 변경 해 줌

        Args:
          parameter: CS로 송신되는 파라메터값, Recursive하게 들어옴.
          command: 충전기->CS, 요청(boot, statusNotification, startTransaction, ... )

        Returns:
          변경된 Parameter.

        Raises:
          None.
        """
        newParam = []
        for item in parameter:
            if type(item) is dict:
                newParam.append(self.touch_parameter(item, command=command))
            elif type(item) is list:
                newParam.append(self.ltouch_parameter(item, command=command))
            elif item in self.setter:
                newParam.append(self.setter[item](item))
            else:
                newParam.append(item)
        return newParam

    def touch_parameter(self, parameter, command=None):
        """Request시 정의된 JSON내 변경이 필요한 항목을 탐색하여 수정함.
        timestamp나 transactionId등을 해당 시점에 맞는 값으로 변경 해 줌

        Args:
          parameter: CS로 송신되는 파라메터값, Recursive하게 들어옴.
          command: 충전기에서 CS로 보내는 명령 종류(bootNotification, Authorize, ... )

        Returns:
          변경된 Parameter.

        Raises:
          None.
        """
        newParam = {}
        for item in parameter.items():
            if type(item[1]) is dict :
                newParam[item[0]] = self.touch_parameter(item[1], command=command)
            elif type(item[1]) is list:
                if command == "meterValues" and item[0] == "sampledValue" :
                    newParam[item[0]] = self.get_sampledValue()
                else:
                    newParam[item[0]] = self.ltouch_parameter(item[1], command=command)
            elif item[0] == "reason" and command in ["boot", "stopTransaction", "statusNotification"]:
                newParam[item[0]] = self.setter[command+"_"+item[0]](command+"_"+item[0])
            elif item[0] in self.setter :
                newParam[item[0]] = self.setter[item[0]](item[0])
            else:
                newParam[item[0]]=item[1]
        return newParam

    def check_response(self, diff_from_items, diff_to_items):
        # from_item : response
        # to_item : props
        """Response 데이터의 포맷 및 필수값 확인, Response값 중 충전기 내부적으로
        관리 해야 하는 데이터는 로컬 변수에 저장(트랜젹선ID 등).

        Args:
          diff_from_items: 실제 충전기로 전달 된 응답값
          diff_to_items: 응답값과 비교 해야 할 표준 응답 포맷 및 필수여부, 저장 해야 할 키 값

        Returns:
          None.

        Raises:
          None.
        """
        for to_item in diff_to_items.items():
            # 데이터타입이 Dict인 경우
            if type(to_item[1]) is dict:
                if to_item[0] in diff_from_items:
                    self.check_response(diff_from_items[to_item[0]], to_item[1])
                else:
                    msg = "No Response Item '{}'".format(to_item[0])
                    evlogger.error(msg)
                    if self.stop_by_error :
                        raise Exception(msg)
            # 데이터타입이 List인 경우 (반드시 Element는 1개 이상의 Dict임)
            elif type(to_item[1]) is list and type(to_item[1][0]) is dict:
                # tariff와 같이 하위 List Element내에 dict가 반복되는 데이터셋 처리
                if to_item[0] in diff_from_items :
                    for idx in range(len(to_item)):
                        if diff_from_items[to_item[0]][idx] is dict :
                            self.check_response(diff_from_items[to_item[0]][idx], to_item[1][idx])
                        else:
                            break
                 # evlogger.info("CS Not ready for list in response")
            elif to_item[0] in diff_from_items:
                if to_item[1][1] :
                    self.update_var(to_item[1][1], diff_from_items[to_item[0]])
            else:
                if(to_item[1][0]=="M"):
                    evlogger.error("No Response Item '{}'".format(to_item[0]))
                    self.update_var("responseFailure", True)
                else:
                    evlogger.warning("No Response Item '{}'(Optional)".format(to_item[0]))

    def resp_post_process(self, response, command):
        """충전기는 CS(Central System)로 부터 받은 응답을 후처리 함

        Args:
          response : CS로 부터 받은 응답
          command : 충전기에서 서버로 보낸 명령(authorize, boot, startTransactionRequest ... )

        Returns:
          errorCode: -1 : No error
                      > 1 : Error
          errorMsg: error message.

        Raises:
          None.cmd
        """
        errorCode = -1
        errorMsg = None

        # 사용자 요금정보(Tariff) 처리

        if command == "dataTransferTariff" :
            self.local_var["tariff"] = response["data"]["tariff"]
        if command == "startTransaction" :
            if response["transactionId"] is None or len(response["transactionId"]) == 0 :
                evlogger.error("No Transaction ID")
                errorMsg = "No Transaction ID"
                errorCode = 1
            else :
                self.local_var["transactionId"] = response["transactionId"]

        if errorCode > 0 :
            raise Exception(errorMsg)

    def make_request(self, command=None, status=None):
        """충전기에서 CS(Central System)으로 보낼 데이터를 생성 하고 송신 후 Response를 수신 함
        수신된 Response는 포맷/필수여부/로컬변수 저장등을 위해 check_response함수 호출

        Args:
          command : 충전기에서 서버로 보낼 명령(authorize, boot, startTransactionRequest ... )
          status : 명령 수행 후 변경 할 상태 지정(Available, Charging, Preparing, ... )

        Returns:
          None.

        Raises:
          None.
        """

        url = props.urls[command]
        parameter=props.api_params[command]

        def set_header(header, headers):
            if command == "boot":
                ri = "boot"
            elif command == "dataTransferHeartbeat":
                ri = "heartbeat"
            else:
                ri = "card"
            get_headers = {
                        'X-EVC-RI': datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]+"_"+ri,
                        'X-EVC-MDL': self.local_var["X-EVC-MDL"],
                        'X-EVC-BOX': self.local_var["X-EVC-BOX"],
                        'X-EVC-OS': self.local_var["X-EVC-OS"],
                        'X-EVC-CON': self.local_var["connectorId"],
                        }
            for h in headers :
                header[h] = get_headers[h]
            return header

        # 기본 템플릿 기반으로 파라미터 설정
        parameter = self.touch_parameter(parameter, command=command)

        if status is not None:
            parameter["status"] = status

        self.disp_header(command)
        header = props.headers
        # header["Authorization"] = "Bearer {}".format(self.accessToken)
        if command in ["boot", "authorize", "dataTransferHeartbeat"]:
            header = set_header(header, props.api_headers[command])

        data = json.dumps(parameter)

        evlogger.info(">"*10+"송신 헤더"+">"*10)
        evlogger.info(header)
        evlogger.info(">"*10+"송신 BODY"+">"*10)
        evlogger.info(data)

        response = requests.post(url, headers=header, data=data)
        response = response.json()

        evlogger.info("<"*10+"수신 DATA"+"<"*10)
        evlogger.info(response)

        if command not in props.api_response :
            evlogger.warning("NO response checker for {}".format(command))
        else:
            self.check_response(response, props.api_response[command])

        # 정상 Response를 받은 경우 아래 수행
        if not self.local_var["responseFailure"]:
            self.resp_post_process(response, command)


def case_run(case):
    """충전기 기본 시뮬레이트 실행. 시험 케이스에 따라 충전기 동작 수행
    Args:
      case(Dictionary) : scenario 파일에 정의된 case 입력 받음

    Returns:
      None.

    Raises:
      None.
    """

    # param 1: 충전소
    # param 2: 충전기
    # param 3: Connector
    # 케이스 별로 사전 상태변수 및 오류코드 세팅 후 Request 요청

    charger = Charger(charger_id = "01040001000101")
    # charger = Charger("010400001", "010400001100A", "01")

    retval = None

    while True:
        charger.init_local_var()
        for task in case:
            if task[0] == "statusNotification" :
                if len(task) > 2: # 2nd element(arg)가 있는 경우만
                    charger.update_var("errorCode", task[2])
                    charger.update_var("statusNotification_reason", task[3])
                charger.make_request(command=task[0], status=task[1])
            elif task[0] in ["boot", "stopTransaction"] :
                # 부팅, 종료(정지) 이유 등록
                charger.update_var(task[0]+"_reason", task[1])
                charger.make_request(command=task[0])
            elif task[0]== "meterValue":
                for i in range(1, random.randrange(5,10)):
                    charger.make_request(command=task[0])
                    time.sleep(1)
            elif task[0] == "dataTransferHeartbeat":
                # heartbeat은 10번만 보냄
                if len(task) == 1 or task[1] is None:
                    for i in range(1, random.randrange(5,10)):
                        charger.make_request(command=task[0])
                        # heartbeatInterval에 따라 주기적으로 전송
                        time.sleep(charger.local_var["heartbeatInterval"])
                elif task[1] == -1:
                    while True:
                        charger.make_request(command=task[0])
                        # heartbeatInterval에 따라 주기적으로 전송
                        time.sleep(charger.local_var["heartbeatInterval"])
            else:
                charger.make_request(command=task[0])
            evlogger.info("="*20+"최종 충전기 내부 변수 상태"+"="*18)
            evlogger.info(charger.local_var)
            evlogger.info("="*60)
            time.sleep(1)

case_run(scenario.normal_case)
# case_run(scenario.error_after_charging)
# case_run(scenario.error_in_charge)
# case_run(scenario.error_just_after_boot)
# case_run(scenario.heartbeat_after_boot)
# case_run(scenario.no_charge_after_authorize)
# case_run(scenario.reserved_after_boot)
# case_run(scenario.remote_stop_transaction)