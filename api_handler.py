import requests
import json
import threading
import time
import os
import base64
from PIL import Image
from io import BytesIO

logger = None
localhost = "http://localhost"


def main(log, topic, message):
    global logger
    logger = log
    try:
        message_dict = json.loads(message)  # 메시지 문자열을 딕셔너리로 변환
        res = {}  # 응답을 위한 딕셔너리 초기화

        # topic 기준으로 명령어를 정리해서 보냄. 이 내용으로 아래 코드를 수정해야함.
        if "/CUSTOM" in topic:
            if "/getStatus" in topic:
                res["message"] = getStatus()
            if "/uploadFile" in topic:
                res["message"] = uploadFile(
                    message_dict.get("filename"), message_dict.get("url")
                )
        elif "/POST" in topic:
            parts = topic.split("/POST")
            if len(parts) > 1:
                path = parts[1]
                logger.debug(f"Calling request_POST with path: {path}")
                res["message"] = request_POST(path)
            else:
                logger.warning("No path found after /POST in topic")
        elif "/GET" in topic:
            parts = topic.split("/GET")
            if len(parts) > 1:
                path = parts[1]
                logger.debug(f"Calling request_GET with path: {path}")
                res["message"] = request_GET(path)
            else:
                logger.warning("No path found after /GET in topic")
        elif "/DELETE" in topic:
            parts = topic.split("/DELETE")
            if len(parts) > 1:
                path = parts[1]
                logger.debug(f"Calling request_DELETE with path: {path}")
                res["message"] = request_DELETE(path)
            else:
                logger.warning("No path found after /DELETE in topic")
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

        klippy_stat = requests.get(localhost + "/server/info")
        klippy_stat = klippy_stat.json()
        if klippy_stat.get("result", {}).get("klippy_state", {}) == "shutdown":
            status = "shutdown"

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


def uploadFile(filename, download_url, timeout=60, max_retries=3):
    result = {}
    retry_count = 0

    def download_task():
        nonlocal result, retry_count
        save_path = f"/home/biqu/printer_data/gcodes/{filename}"

        while retry_count < max_retries:
            try:
                # Firebase Storage에서 파일 다운로드
                response = requests.get(download_url, stream=True, timeout=timeout)
                if response.status_code == 200:
                    # 임시 파일 경로 설정
                    temp_save_path = f"{save_path}.part"

                    # 로컬에 임시 파일로 저장
                    with open(temp_save_path, "wb") as file:
                        start_time = time.time()
                        for chunk in response.iter_content(chunk_size=1024):
                            file.write(chunk)
                            # 시간 초과 체크
                            if time.time() - start_time > timeout:
                                raise TimeoutError("Download timed out")

                    # 임시 파일을 최종 파일로 이동
                    os.rename(temp_save_path, save_path)

                    # 성공 메시지 반환
                    result = {"message": "File successfully downloaded"}
                    return
                else:
                    result = {
                        "error": "Failed to download file",
                        "status_code": response.status_code,
                    }
                    retry_count += 1
            except requests.exceptions.RequestException as e:
                result = {"error": "Network error occurred", "details": str(e)}
                retry_count += 1
            except TimeoutError as e:
                result = {"error": str(e)}
                retry_count += 1
            except Exception as e:
                result = {"error": "An error occurred", "details": str(e)}
                retry_count += 1

            # 재시도 전 대기 시간 추가 (exponential backoff)
            time.sleep(2**retry_count)

        # 최대 재시도 횟수 초과 시 에러 반환
        if retry_count >= max_retries:
            result = {"error": "Max retries exceeded"}

    # 백그라운드에서 다운로드 실행
    download_thread = threading.Thread(target=download_task)
    download_thread.start()

    # 즉시 반환하여 메인 스레드를 블로킹하지 않음
    return json.dumps({"message": "Download started in the background"})


def request_GET(url):
    try:
        response = requests.get(localhost + url)
        response = response.json()  # 응답을 JSON 딕셔너리로 변환
        return json.dumps(response["result"])  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})


def request_POST(url):
    try:
        response = requests.post(localhost + url)
        response = response.json()  # 응답을 JSON 딕셔너리로 변환
        return json.dumps(response["result"])  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})


def request_DELETE(url):
    try:
        response = requests.delete(localhost + url)
        response = response.json()  # 응답을 JSON 딕셔너리로 변환
        return json.dumps(response["result"])  # JSON 문자열로 변환하여 반환
    except Exception as e:
        return json.dumps({"error": str(e)})
