import logging
import logging.handlers
import os

def setup_logger():
    logger_name = 'ma3d_logger'
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        # 이미 핸들러가 설정된 로거가 있으면, 그대로 반환
        return logger

    logger.setLevel(logging.INFO)
    log_dir = os.path.expanduser('~/printer_data/logs/')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'ma3d.log')

    # 로그 파일 초기화
    open(log_file, 'w').close()

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
