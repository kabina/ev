host = "https://deveasyvolt.uplus.co.kr"
chost = "https://devevspcharger.uplus.co.kr"
# host = "http://localhost:5000"
# chost = "http://localhost:5000"

urls = {
    "login": host+"/adm/cmm-api/v1/AUTH/login",
    "authorize":chost+"/api/v1/OCPP/authorize/999332",
    "boot":chost+"/api/v1/OCPP/bootNotification/999332",
    "dataTransferHeartbeat":chost+"/api/v1/OCPP/dataTransfer/999332",
    "prepare":chost+"/api/v1/OCPP/statusNotification/999332",
    "dataTransferTariff":chost+"/api/v1/OCPP/dataTransferTariff/999332",
    "startTransaction":chost+"/api/v1/OCPP/startTransaction/999332",
    "stopTransaction":chost+"/api/v1/OCPP/stopTransaction/999332",
    "meterValues":chost+"/api/v1/OCPP/meterValues/999332",
    "statusNotification": chost + "/api/v1/OCPP/statusNotification/999332",
}
headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
}

api_headers={
        "authorize":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-MDL","X-EVC-OS"],
        "boot":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-MDL","X-EVC-OS"],
        "dataTransferHeartbeat":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-CON"],
        "prepare":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-CON"],
        "stopTransaction":
    ["X-EVC-RI","X-EVC-BOX"],
        "startTransaction":
    ["X-EVC-RI","X-EVC-BOX"],
        "meterValues":
    ["X-EVC-RI","X-EVC-BOX"],
        "dataTransferTariff":
    ["X-EVC-RI", "X-EVC-BOX", "X-EVC-MDL"],
        "statusNotification":
    ["X-EVC-RI", "X-EVC-BOX", "X-EVC-MDL"],
}

api_params = {"authorize":{
            "idTag":"5555222233334444",
        }, "statusNotification": {
            "connectorId": "A",
            "errorCode": "NoError",
            "info": [{
                "reason": "None",
                "cpv": 100,
                "rv": 11,
            }],
            "status": "Available",
            "timestamp": "",
            "vendorErrorCode": "",
            "vendorId": "LGE"
        }, "prepare":{
            "connectorId":"A",
            "errorCode":"NoError",
            "info":{
                "reason":"None",
                "cpv":100,
                "rv":11,
            },
            "status":"Available",
            "timestamp":"",
            "vendorErrorCode":"",
            "vendorId":"LGE"
        }, "meterValues":{
            "connectorId":"A",
            "transactionId":"",
            "meterValue":[
                {
                    "timestamp":"",
                    "sampledValue":[
                        {
                            "measurand":"Current.Import",
                            "phase":"L1",
                            "unit":"A",
                            "value":"0", # Wh Value
                        },{
                            "measurand":"Voltage",
                            "phase":"L1",
                            "unit":"V",
                            "value":"0.0"
                        },{
                            "measurand":"Energy.Active.Import.Register",
                            "unit":"Wh",
                            "value":"0"
                        },{
                            "measurand":"SoC",
                            "unit":"%",
                            "value":"0",
                        },{
                            "measurand":"Power.Active.Import",
                            "unit":"W",
                            "value":"0.0"
                        }
                    ]
            }]
            
        }, "stopTransaction":{
            "idTag":"1111222233335555",
            "meterStop":"0",
            "reason":"Finished",
            "timestamp":"",
            "transactionId":"",
            "transactionData":[{
            "timestamp":"",
            "sampledValue":[
                {
                "measurand":"01",
                "phase":"01",
                "unit":"01",
                "value":"01",
            },{
                "measurand":"01",
                "phase":"01",
                "unit":"01",
                "value":"01",
            }]
            }]
        }, "startTransaction":{
            "idTag":"1111222233334444",
            "connectorId":"A",
            "meterStart":"222222",
            "timestamp":"",
        }, "boot":{
            "reason":"ApplicationReset",
            "chargePointSerialNumber":"C2313123131231232",
            "chargePointVendor":"LGE",
            "chargePointModel":"LGE2323211",
            "firmwareVersion":"V1.3",
            "lccid":"usim121331",
            "imsi":"01023224444",
            "meterSerialNumber":"CNTER23123123",
            "rssi":"-80",
            "entityId":"M2M2442"
        }, "dataTransferTariff":{
            "venderId":"LG",
            "messageId":"Tariff",
            "data":{
                "connectorId":"01",
                "idTag":"1111222233335555",
                "timestamp":""
            }
        }, "dataTransferHeartbeat":{
            "vendorId":"LGE",
            "messageId":"heartbeat",
            "data":{
                "rssi":80,
                "snr":57,
                "rsrp":70,
            }
        }
}

"""
 충전기에서 CS로 보낼 API별로 수신해야 하는 응답중 포함해야 하는 변수, 필수여부, 
 로컬 변수에 저장 해야 하는 키 값을 지정
"""

api_response = {
    "boot":{
        "currentTime":["M",None], # should be changed to real
        "interval":["M","heartbeatInterval"],
        "status":["M","status"],
    },
    "authorize": {
        "idTagInfo": {
            "expiryDate": ["O", None],
            "parentIdTag": ["O", None],
            "status": ["M", None]
        },
    },
    "startTransaction":{
        "idTagInfo":{
            "expiryDate":["O", None],
            "parentIdTag":["O",None],
            "status":["M", None]
        },
        "transactionId":["M", "transactionId"]
    }, "stopTransaction":{
        "idTagInfo":{
            "expiryDate":["O", None],
            "parentIdTag":["O", None],
            "status":["M", None]
        },
    },"dataTransferTariff":{
        "status":"Accepted",
        "data":{
            "idTag": ["M", None],
            "timestamp": ["M", None],
            "tariff":[{
                "startAt":["M", None],
                "endAt":["M", None],
                "price":["M", None]
            },{
                "startAt":["M", None],
                "endAt":["M", None],
                "price":["M", None]
            },{
                "startAt":["M", None],
                "endAt":["M", None],
                "price":["M", None]
            }, {
                "startAt":["M", None],
                "endAt":["M", None],
                "price":["M", None]
            }]
        },
    },
    "dataTransferHeartbeat":{
        "status":["M", None],
        "data":{
            "currentTime":["M", None]
        }
    },
    "statusNotification":{

    },
    "meterValues":{

    }
}

charger_status = [
    "Available",
    "Preparing",
    "Charging",
    "SuspendedEVSE",
    "SuspendedEV",
    "Finishing",
    "Reserved",
    "Unavailable",
    "Faulted",
]

stop_reason = [
    "Finished", "DeAuthorized", "EmergencyStop", "EVDisconnected", "HardReset",
    "Local", "Reboot", "Remote", "UnlockCommand"
]

boot_reason = [
    "ApplicationReset", "FirmwareUpdate", "LocalReset", "PowerUp", "scheduledReset",
    "Triggered", "Unknown", "Watchdog"
]

charger_error = [
    "ConnectorLockFailure",
    "EVCommunicationError",
    "GroundFailure",
    "HighTemperature",
    "InternalError",
    "LocalListConflict",
    "NoError",
    "OtherError",
    "OverCurrentFailure",
    "OverVoltage",
    "PowerMeterFailure",
    "PowerSwitchFailure",
    "ReaderFailure",
    "ResetFailure",
    "UnderVoltage",
    "WeakSignal",
    "onem2mfailure",
    "modemreset",
    "emswon",
    "dooropenfailure",
    "cpadfault",
    "fgfault",
    "mconfault",
]