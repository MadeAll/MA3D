import requests
import logging

logger = logging.getLogger(__name__)

def main(message):
    url = "http://localhost/printer/info"
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        logger.error(f"Failed to get printer info: {e}")
        return json.dumps({"error": str(e)})

# 여기에 더 많은 API 요청 처리 함수 추가...
