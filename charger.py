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
import props, scenario
import time
from evlogger import Logger

local_var = {
    "transactionId":None,
    "heartbeatInterval":5,
    "vendorId":"LGE",
    "connectorId":None,
    "status":None,
    "errorCode":None,
    "boot_reason":None,
    "stopTransaction_reason":None,
    "idTag":None,
    "X-EVC-MDL": "LGE-123",
    "X-EVC-BOX": None,
    "X-EVC-OS": "Linux 5.5",
}

# meterValue용 파라메터 변수 들 (기본값)
sampled_value = {
    "cimport":12,  # Current.Import, 충전전류(A)
    "voltage": 220.0,  # Voltage
    "eairegister": 30000,  # Energy.Active.Import.Register (Wh)
    "soc" : 10,  # SoC
    "paimport" :0,  # Power.Active.Import 충전기로 지속 충전되는 양 (W)
}

logger = Logger()
evlogger = logger.initLogger()

setter = {
    "timestamp": lambda x: datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z") + "Z",
    "transactionId": lambda x: local_var[x],
    "vendorId": lambda x: local_var[x],
    "connectorId": lambda x: local_var[x],
    "status": lambda x: local_var[x],
    "errorCode": lambda x: local_var[x],
    "boot_reason": lambda x: local_var[x],
    "stopTransaction_reason": lambda x: local_var[x],

}

def disp_header(command):
    print("#"*50)
    print("############# - Request for {}".format(command))
    print("#"*50)

def update_var(item, value):
    local_var[item] = value


class Server(metaclass=ABCMeta):
    @abstractmethod
    def send_response(self, response):
        pass

    def make_request(self, request_type):
        pass

class Charger(Server):
    """충전기 클래스 선언

     충전기는 CS로 요청을 보내기도 하고, 자체 서버를 띄워 요청을 받을 수도 있어야 함(HTTP)

    Attributes:
        Server (Class): 서버 클래스의 abstract class inherit

    """
    def __init__(self, station_id, charger_id, connector_id):
        local_var["X-EVC-BOX"] = station_id+charger_id
        local_var["connectorId"] = connector_id

    def update_var(self, *args, **kwargs):
        for item in kwargs:
            self.local_var[item[0]] = item[1]

    def login(self, userid, password):

        data = {"userId": userid, "userPw": password}
        response = requests.post(props.urls["login"], headers=props.headers,
                                 data=json.dumps(data))
        response_dict = json.loads(response.text)
        self.accessToken = response_dict["payload"]["accessToken"]

    def meter_update(self, command=None):
        sampled_value["cimport"] += sampled_value["cimport"] + random.uniform(-1,1)
        sampled_value["voltage"] = sampled_value["voltage"] + random.uniform(-1,1)
        # sampled_value["eairegister"] = sampled_value["eairegister"] + random.uniform(-1,1)
        sampled_value["soc"] = sampled_value["soc"]
        sampled_value["paimport"] = (sampled_value["paimport"]+1000 +
                                    random.uniform(-1,1) ) if command == "meterValues" else 0

    def get_sampledValue(self):
        self.meter_update(command="meterValues")
        value = [
            {   "measurand": "Current.Import", "phase": "L1", "unit": "A", "value":
                "{:.1f}".format(sampled_value["cimport"]),  # Wh Value
            }, {"measurand": "Voltage", "phase": "L1", "unit": "V", "value":
                "{:.1f}".format(sampled_value["voltage"]),
            }, {"measurand": "Energy.Active.Import.Register", "unit": "Wh", "value":
                "{:.1f}".format(sampled_value["eairegister"])
            }, {"measurand": "SoC", "unit": "%", "value":
                "{}".format(sampled_value["soc"],)
            }, {"measurand": "Power.Active.Import", "unit": "W", "value":
                "{}".format(sampled_value["paimport"])
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
            elif item in setter:
                newParam.append(setter[item](item))
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
            elif item[0] == "reason" and command in ["boot", "stopTransaction"]:
                newParam[item[0]] = setter[command+"_"+item[0]](command+"_"+item[0])
            elif item[0] in setter :
                newParam[item[0]] = setter[item[0]](item[0])
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
                    evlogger.error("No Response Item '{}'".format(to_item[0]))
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
                    update_var(to_item[1][1], diff_from_items[to_item[0]])
            else:
                if(to_item[1][0]=="M"):
                    evlogger.error("No Response Item '{}'".format(to_item[0]))
                else:
                    evlogger.warning("No Response Item '{}'(Optional)".format(to_item[0]))


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
        header=props.api_headers[command]
        parameter=props.api_params[command]
        response=None
        def set_header(header, headers):
            get_headers = {
                        'X-EVC-RI': datetime.now().strftime('%Y%m%d%H%M%S%f')+"_"+command,
                        'X-EVC-MDL': local_var["X-EVC-MDL"],
                        'X-EVC-BOX': local_var["X-EVC-BOX"],
                        'X-EVC-OS': local_var["X-EVC-OS"],
                        'X-EVC-CON': local_var["connectorId"],
                        }
            for h in headers :
                header[h] = get_headers[h]
            return header

        # 기본 템플릿 기반으로 파라미터 설정
        parameter = self.touch_parameter(parameter, command=command)
        if status is not None:
            parameter["status"] = status

        disp_header(command)
        header = props.headers
        # header["Authorization"] = "Bearer {}".format(self.accessToken)
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

        if status is not None :
            local_var["status"] = status

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

    charger = Charger("123123123123", "123123123", "01")
    for task in case:
        if task[0] == "statusNotification" :
            if len(task) > 2: # 2nd element(arg)가 있는 경우만
                update_var("errorCode", task[2])
            charger.make_request(command=task[0], status=task[1])
        elif task[0] in ["boot", "stopTransaction"] :
            # 부팅, 종료(정지) 이유 등록
            update_var(task[0]+"_reason", task[1])
            charger.make_request(command=task[0])
        elif task[0]== "meterValue":
            for i in range(1, random.randrange(5,10)):
                charger.make_request(command="meterValues")
                time.sleep(1)
        elif task[0] == "heartbeat":
            # heartbeat은 10번만 보냄
            if task[1] is None:
                for i in range(1, random.randrange(5,10)):
                    charger.make_request(command="heartbeat")
                    # heartbeatInterval에 따라 주기적으로 전송
                    time.sleep(local_var["heartbeatInterval"])
            elif task[1] == -1:
                while True:
                    charger.make_request(command="heartbeat")
                    # heartbeatInterval에 따라 주기적으로 전송
                    time.sleep(local_var["heartbeatInterval"])
        else:
            charger.make_request(command=task[0])
        evlogger.info("="*20+"최종 충전기 내부 변수 상태"+"="*25)
        evlogger.info(local_var)
        evlogger.info("="*60)
        time.sleep(1)

case_run(scenario.normal_case)
# case_run(scenario.error_in_charge)
# case_run(scenario.error_after_boot)
# case_run(scenario.heartbeat_after_boot)
# case_run(scenario.no_charge_after_authorize)