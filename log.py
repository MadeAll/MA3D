import logging
import logging.handlers
import os

def setup_logger():
    log_dir = os.path.expanduser('~/printer_data/logs/')
    log_file = os.path.join(log_dir, 'ma3d.log')
    
    # 로그 디렉토리가 없으면 생성
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 파일 초기화
    open(log_file, 'w').close()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 파일 핸들러 설정
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 예시 사용
# logger = setup_logger()
# logger.info("This is an info message")
