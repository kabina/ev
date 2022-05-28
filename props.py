from datetime import datetime

# host = "http://deveasyvolt.uplus.co.kr"
# chost = "http://devevspcharger.uplus.co.kr"
host = "http://localhost:5000"
chost = "http://localhost:5000"
urls = {
    "login": host+"/adm/cmm-api/v1/AUTH/login",
    "chl_info":host+"/adm/api/v1/CHL/retrieveChannelInfo",
    "authorize":chost+"/cs/api/v1/OCPP/authorize/999332",
    "boot":chost+"/cs/api/v1/OCPP/bootNotification/999332",
    "heartbeat":chost+"/cs/api/v1/OCPP/dataTransfer/999332",
    "prepare":chost+"/cs/api/v1/OCPP/statusNotification/999332",
    "startTransaction":chost+"/cs/api/v1/OCPP/startTransaction/999332",
    "stopTransaction":chost+"/cs/api/v1/OCPP/stopTransaction/999332",
    "meterValues":chost+"/cs/api/v1/OCPP/meterValues/999332",
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
        "heartbeat":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-CON"],
        "prepare":
    ["X-EVC-RI","X-EVC-BOX","X-EVC-CON"],
        "stopTransaction":
    ["X-EVC-RI","X-EVC-BOX"],
        "startTransaction":
    ["X-EVC-RI","X-EVC-BOX"],
        "meterValues":
    ["X-EVC-RI","X-EVC-BOX"],
}

api_post_status={
        "authorize":"Preparing",
        "boot":"Available",
        "heartbeat":"Available",
        "prepare":"Available",
        "stopTransaction":"Available",
        "startTransaction":"Charging",
        "meterValues":"Charging",
}

api_params = {"chl_info":{
            "chnId" : "",
            "bizConsChnlCd" : "",
            "jobTrstCd":"",
            "copNm":"",
            "clntCd":"",
            "brno":"",
            "coRegNo":"",
            "cntcStusCd":""
        }, "authorize":{
            "idTag":"1234567890123456",
        }, "prepare":{
            "connectorId":"01",
            "errorCode":"NoError",
            "info":{
                "reason":"None",
                "cpv":100,
                "rv":11,
            },
            "status":"Available",
            "timestamp":datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")+"Z",
            "vendorErrorCode":"",
            "vendorId":"LGE"
        }, "meterValues":{
            "connectorId":"01",
            "transactionId":"123123123",
            "meterValue":[
                {
                "measurand":"01",
                "phase":"01",
                "unit":"01",
                "value":"01",
            },{
                "measurand":"02",
                "phase":"02",
                "unit":"02",
                "value":"02",
            }]
            
        }, "stopTransaction":{
            "idTag":"1234567890123456",
            "meterStop":"200",
            "reason":"Finished",
            "timestamp":datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")+"Z",
            "transactionId":"123123123",
            "transactionData":[{
            "timestamp":datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")+"Z",
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
            "idTag":"1234567890123456",
            "connectorId":"01",
            "meterStart":"222222",
            "timestamp":datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")+"Z",
        }, "heartbeat":{
            "vendorId":"LGE",
            "messageId":"heartbeat",
            "data":{
                "rssi":80,
                "snr":1,
                "rsrp":1,
            }
        }, "boot":{
            "reason":"ApplicationReset",
            "chargePointSerialNumber":"C2313123131231232",
            "chargePointVendor":"LGE",
            "chargePointModel":"LGE2323211",
            "firmwareVersion":"V1.3",
            "lccid":"usim121331",
            "imsi":"01023224444",
            "meterSerialNumber":"CNTER23123123",
            "rssi":"23124124",
            "entityId":"M2M2442"
        }
}
