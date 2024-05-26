import requests
import json
import base64
from PIL import Image
from io import BytesIO
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack

logger = None
localhost = "http://localhost"
pcs = {}


def main(log, topic, message, mqtt_connection):
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
        elif "/webrtc" in topic:
            parts = topic.split("/webrtc")
            if len(parts) > 1:
                path = parts[1]
                logger.debug(f"Calling request_webRTC with path: {path}")
                res["message"] = request_webRTC(path, message_dict, mqtt_connection)
            else:
                logger.warning("No path found after /webrtc in topic")

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


def uploadFile(filename, download_url):
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
            return json.dumps({"message": "File successfully downloaded"})
        else:
            # 다운로드 실패 시 오류 메시지 반환
            return json.dumps({"error": "Failed to download file"})
    except Exception as e:
        # 예외 발생 시 오류 메시지 반환
        return json.dumps({"error": str(e)})


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


class WebcamStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.player = MediaPlayer("/dev/video0")

    async def recv(self):
        frame = await self.player.video.recv()
        return frame


async def handle_offer(logger, pc, offer):
    await pc.setRemoteDescription(offer)
    stream = WebcamStreamTrack()
    pc.addTrack(stream)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc.localDescription


def request_webRTC(url, message, mqtt_connection):
    try:
        if url == "/setup":
            data = message
            response = None

            logger.info("Handling WebRTC setup")
            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            # 새로운 RTCPeerConnection 객체 생성
            pc = RTCPeerConnection()
            pcs[data["id"]] = pc

            @pc.on("icecandidate")
            def on_icecandidate(event):
                if event.candidate:
                    candidate_message = json.dumps(
                        {
                            "candidate": event.candidate.candidate,
                            "sdpMid": event.candidate.sdpMid,
                            "sdpMLineIndex": event.candidate.sdpMLineIndex,
                        }
                    )
                    mqtt_connection.publish(
                        topic=f"{data['id']}/req/webrtc/candidate",
                        payload=candidate_message,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                    )

            @pc.on("track")
            def on_track(event):
                logger.info("Track received")

            loop = asyncio.get_event_loop()
            answer = loop.run_until_complete(handle_offer(logger, pc, offer))
            response = json.dumps({"sdp": answer.sdp, "type": answer.type})

            return response  # JSON 문자열로 변환하여 반환
        elif url == "/candidate":
            logger.info("Handling ICE candidate")
            pc = pcs.get(message["id"])
            if pc:
                candidate = RTCIceCandidate(
                    candidate=message["candidate"],
                    sdpMid=message["sdpMid"],
                    sdpMLineIndex=message["sdpMLineIndex"],
                )
                loop = asyncio.get_event_loop()
                loop.run_until_complete(pc.addIceCandidate(candidate))

    except Exception as e:
        return json.dumps({"error": str(e)})
    try:
        if url == "/setup":
            data = message
            response = None

            logger.info("Handling WebRTC setup")
            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            # 새로운 RTCPeerConnection 객체 생성
            pc = RTCPeerConnection()
            pcs[data["id"]] = pc

            @pc.on("icecandidate")
            def on_icecandidate(event):
                if event.candidate:
                    candidate_message = json.dumps(
                        {
                            "candidate": event.candidate.candidate,
                            "sdpMid": event.candidate.sdpMid,
                            "sdpMLineIndex": event.candidate.sdpMLineIndex,
                            "id": data["id"]
                        }
                    )
                    mqtt_connection.publish(
                        topic=f"{data['id']}/res/webrtc/candidate",
                        payload=candidate_message,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                    )

            @pc.on("track")
            def on_track(event):
                logger.info("Track received")

            loop = asyncio.get_event_loop()
            answer = loop.run_until_complete(handle_offer(logger, pc, offer))
            response = json.dumps({"sdp": answer.sdp, "type": answer.type})

            return response  # JSON 문자열로 변환하여 반환
        elif url == "/candidate":
            logger.info("Handling ICE candidate")
            pc = pcs.get(message["id"])
            if pc:
                candidate = RTCIceCandidate(
                    candidate=message["candidate"],
                    sdpMid=message["sdpMid"],
                    sdpMLineIndex=message["sdpMLineIndex"],
                )
                loop = asyncio.get_event_loop()
                loop.run_until_complete(pc.addIceCandidate(candidate))

    except Exception as e:
        return json.dumps({"error": str(e)})
