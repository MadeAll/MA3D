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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 표준 출력으로 로그 전송
    ]
)

def main():
    """메인 함수"""
    logging.info("MA3D 서비스가 실행 중입니다.")
    
    # 무한 대기 (CPU 사용량 최소화)
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
