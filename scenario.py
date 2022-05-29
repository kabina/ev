## 일반 충전/종료 케이스
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
    ["heartbeat"]
]

# 충전 중 비상정지 후 리부팅
#
error_in_charge = [
    ["boot", "PowerUp"],
    ["statusNotification", "Available"],
    ["authorize"],
    ["statusNotification", "Preparing"],
    ["dataTransferTariff"],
    ["startTransaction"],
    ["statusNotification", "Charging"],
    ["meterValue"],
    ["stopTransaction", "EmergencyStop"],
    ["boot"]
]

# 부팅 후 heartbeat 진행 중 리부팅 됨(리부팅 후 부팅 안됨)
error_after_boot = [
    ["boot", "PowerUp"],
    ["heartbeat"],
    ["stopTransaction", "Reboot"],
]

heartbeat_after_boot = [
    ["boot", "LocalReset"],
    ["heartbeat"]
]