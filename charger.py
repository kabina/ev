#!/usr/bin/python
# -*- coding: utf-8 -*-
"""전기차 충전기 시뮬레이터

     * 안창선
     * 2022-05-27

Todo:
   TODO리스트를 기재
    * Logger.
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

logger = Logger()
evlogger = logger.initLogger()


def disp_header(command):
    print("#"*50)
    print("############# - Request for {}".format(command))
    print("#"*50)


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
        self.station_id = station_id
        self.charger_id = charger_id
        self.connector_id = connector_id
        self.x_evc_box = charger_id
        self.x_evc_mdl = "CHG-150"
        self.x_evc_os = "Linux 1.6"
        self.x_evc_con = connector_id
        self.status = "Available"
        self.accessToken = None

    def login(self, userid, password):

        data = {"userId": userid, "userPw": password}
        response = requests.post(props.urls["login"], headers=props.headers,
                                 data=json.dumps(data))
        response_dict = json.loads(response.text)
        self.accessToken = response_dict["payload"]["accessToken"]

    def send_response(response):
        print(response)


    def make_request(self, request_type, command=None):

        url = props.urls[command]
        header=props.api_headers[command]
        parameter=props.api_params[command]
        response=None


        def set_header(header, headers):
            get_headers = {
                        'X-EVC-RI': datetime.now().strftime('%Y%m%d%H%M%S%f')+"_"+command,
                        'X-EVC-MDL': self.x_evc_mdl,
                        'X-EVC-BOX': self.x_evc_box,
                        'X-EVC-OS': self.x_evc_os,
                        'X-EVC-CON': self.x_evc_con,
                        }
            for h in headers :
                header[h] = get_headers[h]
            return header

        disp_header(command)
        header = props.headers
        header["Authorization"] = "Bearer {}".format(self.accessToken)
        header = set_header(header, props.api_headers[command])
        data = json.dumps(parameter)

        evlogger.info(">"*10+"송신 헤더"+">"*10)
        evlogger.info(header)
        evlogger.info(">"*10+"송신 BODY"+">"*10)
        evlogger.info(data)

        if request_type == REQ_POST:
            response = requests.post(url, headers=header,
                                     data=data)
            response = response.json()
        else:
            response = requests.get(url, headers=header,
                                    data=data)
            response = response.json()

        evlogger.info("<"*10+"수신 DATA"+"<"*10)
        evlogger.info(response)

        self.status = props.api_post_status[command]


charger = Charger("123123123123", "123123123", "01")
#charger.login("test", "test1")
# charger.make_request(REQ_POST, command = "boot")
# # time.sleep(3)
charger.make_request(REQ_GET, command = "authorize")
charger.make_request(REQ_GET, command = "authorize")
charger.make_request(REQ_GET, command = "authorize")
charger.make_request(REQ_GET, command = "authorize")
charger.make_request(REQ_GET, command = "authorize")
# time.sleep(3)
# charger.make_request(REQ_POST, command = "prepare")
# # time.sleep(3)
# charger.make_request(REQ_POST, command = "startTransaction")
# # time.sleep(3)
# for _ in range(10) :
#     charger.make_request(REQ_POST, command = "meterValues")
#     # time.sleep(3)
# charger.make_request(REQ_POST, command = "stopTransaction")
# # time.sleep(3)
# charger.make_request(REQ_POST, command = "heartbeat")
# items = charger.response["data"][0].items()
# items = sorted(items, key=lambda x : x[0])
# for s in items :
#     print(s[0], s[1])
# dicts = {i[0]:i[1] for i in items} 
