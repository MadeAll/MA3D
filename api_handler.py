import requests
import logging
import json

logger = logging.getLogger(__name__)


def main(message):
    url = "http://localhost/"
    try:
        # message가 딕셔너리이므로 직접 접근
        if message["method"] == "GET":
            response = requests.get(url + message["url"])
        # 여기서 JSON 대신 response.text를 반환
        return response.text
    except Exception as e:
        logger.error(f"Failed to handle message: {e}")
        return json.dumps({"error": str(e)})
