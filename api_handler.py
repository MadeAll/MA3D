import requests
import logging
import json

logger = None


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


def getStatus(log):
    global logger
    logger = log
    url = "http://localhost"
    try:
        stat = requests.get(url + "/printer/objects/query?print_stats")
        stat = stat.json()  # 응답을 JSON 딕셔너리로 변환
        logger.info(f"stat: {stat}")
        # 필요한 데이터 추출
        print_stats = stat.get("result", {}).get("status", {}).get("print_stats", {})
        status = print_stats.get("state")
        filename = print_stats.get("filename")
        total_duration = print_stats.get("total_duration")
        print_duration = print_stats.get("print_duration")

        temp = requests.get(url + "/api/printer")
        temp = temp.json()  # 응답을 JSON 딕셔너리로 변환
        # 필요한 데이터 추출
        temp_stats = temp.get("temperature", {})
        nozzle_temp = temp_stats.get("tool0").get("actual")
        nozzle_target = temp_stats.get("tool0").get("target")
        bed_temp = temp_stats.get("bed").get("actual")
        bed_target = temp_stats.get("bed").get("target")

        # 새로운 딕셔너리 생성
        extracted_data = {
            "status": status,
            "filename": filename,
            "total_duration": total_duration,
            "print_duration": print_duration,
            "nozzle_temp": nozzle_temp,
            "nozzle_target": nozzle_target,
            "bed_temp": bed_temp,
            "bed_target": bed_target,
        }

        return json.dumps(extracted_data)  # JSON 문자열로 변환하여 반환
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return json.dumps({"error": str(e)})
