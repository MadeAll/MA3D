#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MA3D 서비스 메인 파일
이 파일은 ma3d.service에 의해 호출되는 최소한의 템플릿 코드입니다.
실제 기능은 없으며, 서비스 실행을 위한 빈 파일입니다.
"""

import time
import sys
import logging
import os
from pathlib import Path

# 로그 디렉토리 확인 및 생성
log_dir = os.path.expanduser("~/printer_data/logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "ma3d.log")

# 서비스 시작 시 기존 로그 파일 초기화
try:
    # 파일이 존재하면 내용 삭제
    if os.path.exists(log_file):
        open(log_file, 'w').close()
except Exception as e:
    print(f"로그 파일 초기화 중 오류 발생: {e}")

# 로깅 설정
logger = logging.getLogger('ma3d')
logger.setLevel(logging.INFO)

# 파일 핸들러 설정 (append 모드)
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(console_handler)

# 로거 기본 핸들러 제거 (이중 로깅 방지)
logger.propagate = False

def main():
    """메인 함수"""
    logger.info("MA3D 서비스가 실행 중입니다.")
    
    # 무한 대기 (CPU 사용량 최소화)
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
