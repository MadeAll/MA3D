import requests
import json
import base64
import mqtt
from PIL import Image
from io import BytesIO

logger = None
localhost = "http://localhost"


def main(message):
    try:
        message_dict = json.loads(message)  # 메시지 문자열을 딕셔너리로 변환
        res = {}  # 응답을 위한 딕셔너리 초기화

        if message_dict.get("method") == "CUSTOM":
            if message_dict.get("url") == "getStatus":
                res["message"] = (
                    getStatus()
                )  # getStatus 함수의 결과를 res 딕셔너리에 할당
                res["topic"] = (
                    mqtt.topic + "/status"
                )  # mqtt 모듈의 topic 변수와 "/status"를 결합하여 토픽 설정
            elif message_dict.get("url") == "uploadFile":
                body = message_dict.get("body")
                if body:
                    download_url = body.get("url")
                    filename = body.get("name")
                    res["message"] = uploadFile(download_url, filename)
                    res["topic"] = mqtt.topic + "/res"  # 응답을 위한 토픽 설정
                else:
                    res["message"] = json.dumps(
                        {"error": "Missing 'body' with 'url' and 'name'"}
                    )
                    res["topic"] = mqtt.topic + "/res"
        elif message_dict.get("method") == "GET":
            res["message"] = request_GET(message_dict.get("url"))
            res["topic"] = mqtt.topic + "/res"
        return json.dumps(res)  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})


def getStatus():
    try:
        stat = requests.get(localhost + "/printer/objects/query?print_stats")
        stat = stat.json()  # 응답을 JSON 딕셔너리로 변환
        # 필요한 데이터 추출
        print_stats = stat.get("result", {}).get("status", {}).get("print_stats", {})
        status = print_stats.get("state")
        filename = print_stats.get("filename")
        print_duration = print_stats.get("print_duration")

        temp = requests.get(localhost + "/api/printer")
        temp = temp.json()  # 응답을 JSON 딕셔너리로 변환
        # 필요한 데이터 추출
        temp_stats = temp.get("temperature", {})
        nozzle_temp = temp_stats.get("tool0").get("actual")
        nozzle_target = temp_stats.get("tool0").get("target")
        bed_temp = temp_stats.get("bed").get("actual")
        bed_target = temp_stats.get("bed").get("target")

        print = requests.get(localhost + "/server/files/metadata?filename=" + filename)
        print = print.json()  # 응답을 JSON 딕셔너리로 변환
        # 필요한 데이터 추출
        file_stats = print.get("result", {})
        estimated_time = file_stats.get("estimated_time")

        # 스냅샷 이미지 가져오기 및 처리
        snapshot_response = requests.get(localhost + "/webcam/?action=snapshot")
        if snapshot_response.status_code == 200:
            img = Image.open(BytesIO(snapshot_response.content))
            img_resized = img.resize(
                (300, int((img.height / img.width) * 300))
            )  # 가로 400px 비율 유지하여 리사이즈
            buffered = BytesIO()
            img_resized.save(buffered, format="JPEG")
            snapshot_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        else:
            snapshot_base64 = None  # 이미지를 가져오지 못한 경우

        # 새로운 딕셔너리 생성
        extracted_data = {
            "status": status,
            "filename": filename,
            "print_duration": print_duration,
            "estimated_time": estimated_time,
            "nozzle_temp": nozzle_temp,
            "nozzle_target": nozzle_target,
            "bed_temp": bed_temp,
            "bed_target": bed_target,
            "snapshot": snapshot_base64,
        }

        return json.dumps(extracted_data)  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})


def uploadFile(download_url, filename):
    try:
        # 파일 저장 경로 설정
        save_path = f"/home/biqu/printer_data/gcodes/{filename}"

        # Firebase Storage에서 파일 다운로드
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            # 로컬에 파일 저장
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            # 성공 메시지 반환
            return json.dumps(
                {
                    "success": True,
                    "message": "File successfully downloaded",
                    "filename": filename,
                }
            )
        else:
            # 다운로드 실패 시 오류 메시지 반환
            return json.dumps(
                {
                    "success": False,
                    "error": "Failed to download file from Firebase Storage",
                }
            )
    except Exception as e:
        # 예외 발생 시 오류 메시지 반환
        return json.dumps({"error": str(e)})


def request_GET(url):
    try:
        response = requests.get(localhost + url)
        response = response.json()  # 응답을 JSON 딕셔너리로 변환
        return json.dumps(response)  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})
