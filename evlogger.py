from logging import handlers
import logging
import colorlog
import os
import sys


class Logger:
    """
    커스텀 로거 클래스
    """

    def __init__(self, filePath=None):

        # 로거 이름
        self.className = "Logger"

        # 로그 파일 생성 경로
        if filePath is None:
            self.filePath = "./log/"

        # 로그 파일 생성 경로 부재 시 생성
        if not os.path.exists(self.filePath):
            os.makedirs(self.filePath)

    def initLogger(self):
        """
        로거 인스턴스 반환
        """
        # 로거 인스턴스 생성
        __logger = logging.getLogger("Logger")

        # =====================================================
        # 포매터 설정
        # =====================================================
        # 스트림 핸들러 포매터 설정
        streamFormatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)-8s]%(reset)s <%(name)s>: %(module)s:%(lineno)d:  %(bg_black)s%(message)s"
        )
        # 파일 핸들러 포매터 설정
        fileFormatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] <%(name)s>: %(module)s:%(lineno)d: %(message)s"
        )
        # =====================================================
        # 핸들러 설정
        # =====================================================
        # 스트림 핸들러 정의
        streamHandler = colorlog.StreamHandler(sys.stdout)

        # 파일 핸들러 정의
        fileHandler = handlers.TimedRotatingFileHandler(
            os.path.abspath(f"{self.filePath}logData.log"),
            when="midnight",
            interval=1,
            backupCount=14,
            encoding="utf-8",
            delay=False
        )
        # =====================================================
        # 핸들러에 포매터 지정
        # =====================================================
        streamHandler.setFormatter(streamFormatter)
        fileHandler.setFormatter(fileFormatter)

        # 로거 인스턴스에 핸들러 삽입
        __logger.addHandler(streamHandler)
        __logger.addHandler(fileHandler)

        # 로그 레벨 정의
        __logger.setLevel(logging.DEBUG)

        return __logger