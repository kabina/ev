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

from abc import *
from datetime import datetime
import requests
import json
import props
import time
from evlogger import Logger

REQ_POST = 1
REQ_GET = 2
local_var = {
    "transactionId":None,
    "heartbeatInterval":None,
    "vendorId":None,
    "connectorId":None,
    "status":None,
    "idTag":None,
    "X-EVC-MDL": "LGE-123",
    "X-EVC-BOX": None,
    "X-EVC-OS": "Linux 5.5",
}


logger = Logger()
evlogger = logger.initLogger()

setter = {
    "timestamp": lambda x: datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z") + "Z",
    "transactionId": lambda x: local_var[x],
    "vendorId": lambda x: local_var[x],
    "connectorId": lambda x: local_var[x],
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

    def send_response(response):
        print(response)

    def ltouch_parameter(self, parameter):
        """Request시 정의된 JSON내 변경이 필요한 항목을 탐색하여 수정함.
        timestamp나 transactionId등을 해당 시점에 맞는 값으로 변경 해 줌

        Args:
          parameter: CS로 송신되는 파라메터값, Recursive하게 들어옴.

        Returns:
          변경된 Parameter.

        Raises:
          None.
        """
        newParam = []
        for item in parameter:
            if type(item) is dict:
                newParam.append(self.touch_parameter(item))
            elif type(item) is list:
                newParam.append(self.ltouch_parameter(item))
            elif item in setter:
                newParam.append(setter[item](item))
            else:
                newParam.append(item)
        return newParam

    def touch_parameter(self, parameter, meterValue = None):
        """Request시 정의된 JSON내 변경이 필요한 항목을 탐색하여 수정함.
        timestamp나 transactionId등을 해당 시점에 맞는 값으로 변경 해 줌

        Args:
          parameter: CS로 송신되는 파라메터값, Recursive하게 들어옴.

        Returns:
          변경된 Parameter.

        Raises:
          None.
        """
        newParam = {}
        found_meter = False
        for item in parameter.items():
            if type(item[1]) is dict :
                newParam[item[0]] = self.touch_parameter(item[1])
            elif type(item[1]) is list:
                newParam[item[0]] = self.ltouch_parameter(item[1])
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
            if type(to_item[1]) is dict:
                if to_item[0] in diff_from_items:
                    self.check_response(diff_from_items[to_item[0]], to_item[1])
                else:
                    evlogger.error("No Response Item '{}'".format(to_item[0]))
            elif type(to_item[1]) is list:
                pass
            elif to_item[0] in diff_from_items:
                if to_item[1][1] :
                    update_var(to_item[1][1], diff_from_items[to_item[0]])
            else:
                if(to_item[1][1]=="M"):
                    evlogger.error("No Response Item '{}'".format(to_item[0]))
                else:
                    evlogger.warning("No Response Item '{}'(Optional)".format(to_item[0]))


    def make_request(self, request_type, command=None, status=None):
        """충전기에서 CS(Central System)으로 보낼 데이터를 생성 하고 송신 후 Response를 수신 함
        수신된 Response는 포맷/필수여부/로컬변수 저장등을 위해 check_response함수 호출

        Args:
          request_type : POS or GET
          command : 충전기에서 서버로 보낼 명령(authorize, boot, startTransactionRequest ... )

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
        parameter = self.touch_parameter(parameter)
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

        if request_type == REQ_POST:
            response = requests.post(url, headers=header, data=data)
        else:
            response = requests.get(url, headers=header,  data=data)
        response = response.json()

        evlogger.info("<"*10+"수신 DATA"+"<"*10)
        evlogger.info(response)

        if command not in props.api_response :
            evlogger.warning("NO response checker for {}".format(command))
        else:
            self.check_response(response, props.api_response[command])

        if status is not None :
            local_var["status"] = status

def start_charger():
    """충전기 기본 시뮬레이트 실행. 기본 정상 프로시저에 따른 충전 수행
    Args:

    Returns:
      None.

    Raises:
      None.
    """
    operation_sequence =[
        ["boot"],
        ["statusNotification","Available"],
        ["authorize"],
        ["statusNotification","Preparing"],
        ["dataTransferTariff"],
        ["startTransaction"],
        ["statusNotification","Charging"],
        ["meterValue"],
        ["stopTransaction"],
        ["statusNotification", "Finishing"],
        ["statusNotification", "Available"],
        ["heartbeat"]
    ]

    charger = Charger("123123123123", "123123123", "01")
    # charger.login("test", "test1")
    for task in operation_sequence:
        if task[0] == "statusNotification" :
            charger.make_request(REQ_POST, command=task[0], status=task[1])
        elif task[0]== "meterValue":
            for i in range(1, 10):
                props.meter_value = 1000 * i
                charger.make_request(REQ_POST, command="meterValues")
                time.sleep(1)
        else:
            charger.make_request(REQ_POST, command=task[0])
        time.sleep(1)

    evlogger.info(local_var)

start_charger()