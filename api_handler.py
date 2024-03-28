import requests
import logging
import json

logger = logging.getLogger(__name__)


def main(message):
    url = "http://localhost/"
    try:
        # message가 문자열인 경우, 딕셔너리로 변환
        if isinstance(message, str):
            message = json.loads(message)
        # message가 딕셔너리이므로 직접 접근
        if message["method"] == "GET":
            response = requests.get(url + message["url"])
        # 여기서 JSON 대신 response.text를 반환
        return response.text
    except Exception as e:
        logger.error(f"Failed to handle message: {e}")
        return json.dumps({"error": str(e)})

def getStatus():
    url = "http://localhost"
    try:
        status = requests.get(url + '/printer/objects/query?print_stats')
        logger.info("Printer Stats : ", status)
        return status.text
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return json.dumps({"error": str(e)})