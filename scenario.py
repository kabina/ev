#!/usr/bin/python
# -*- coding: utf-8 -*-
"""전기차 충전기 시뮬레이터 테스트 시나리오

     * 안창선
     * 2022-05-27

Todo:
   TODO리스트를 기재
    * 다양한 케스트 확인

 사용법:
   케이스 작성법:
    - boot
      arg1 : Boot Reason (ex: PowerUp)
    - statusNotification
      arg1 : 상태코드
      arg2 : 오류코드 (상태코드가 비정상 인 경우)
    - stopTransaction
      arg1 : 정지(종료) 사유(reason)
    - heartbeat
      arg1 :
        * None : 랜덤(5-10회)
        * -1 : Permanent loop
"""
## 일반 충전/종료 케이스
normal_case = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
    ["statusNotification", "Charging"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["stopTransaction", "Finished"],
    ["statusNotification", "Finishing"],
    ["statusNotification", "Available"],
    ["dataTransferHeartbeat", None],
    ["dataTransferHeartbeat", None],
    ["dataTransferHeartbeat", None],
]
normal_case_without_boot = [
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
    ["statusNotification", "Charging"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["stopTransaction", "Finished"],
    ["statusNotification", "Finishing"],
    ["statusNotification", "Available"],
    ["dataTransferHeartbeat", None],
    ["dataTransferHeartbeat", None],
    ["dataTransferHeartbeat", None],
]

# 충전 중 비상정지 후 리부팅
error_in_charge = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
    ["statusNotification", "Charging"],
    ["meterValues"],
    ["meterValues"],
    ["meterValues"],
    ["stopTransaction", "EmergencyStop"],
    ["boot"]
]

# 부팅 후 heartbeat 진행 중 리부팅 됨(리부팅 후 부팅 안됨)
error_just_after_boot = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Unavailable", "InternalError", "HighTemperature"],
    # ["statusNotification", "Available"],
]

# 부팅 후 대기 중
heartbeat_after_boot = [
    ["bootNotification", "LocalReset"],
    ["dataTransferHeartbeat", None]
]

# 카드 태깅 후 충전 안하고 가버린 케이스
no_charge_after_authorize = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
]

# 충전 시작 후 멈춤(Hang)
error_after_charging = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
]

# 부팅 후 충전기 예약 대기중으로 변경 >> 예약충전기로 진행 해야 함
reserved_after_boot = [
    ["bootNotification", "PowerUp"],
    ["statusNotification", "Reserved"],
    ["dataTransferHeartbeat", None]
]


remote_stop_transaction = [
    ["stopTransaction", "Remote"],
    ["statusNotification", "Finishing"],
    ["statusNotification", "Available"],
    ["dataTransferHeartbeat"],
    ["dataTransferHeartbeat"],
    ["dataTransferHeartbeat"],
]