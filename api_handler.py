import requests
import json
import base64
from PIL import Image
from io import BytesIO
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack, MediaPlayer

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
        elif "/webrtc" in topic:
            parts = topic.split("/webrtc")
            if len(parts) > 1:
                path = parts[1]
                logger.debug(f"Calling request_webRTC with path: {path}")
                res["message"] = request_webRTC(path, message_dict)
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
        self.player = MediaPlayer(localhost + "/webcam/?action=stream")
        logger.info(
            "MediaPlayer created with source: http://localhost/webcam/?action=stream"
        )

    async def recv(self):
        try:
            frame = await self.player.video.recv()
            if frame is None:
                logger.error("Received frame is None")
            else:
                logger.info("Frame received: %s", frame)
            return frame
        except Exception as e:
            logger.error("Exception in recv: %s", str(e))
            raise


async def handle_offer(logger, pc, offer):
    try:
        logger.info("Setting remote description with offer: %s", offer)
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        )
        logger.info("Remote description set")

        stream = WebcamStreamTrack()
        pc.addTrack(stream)
        logger.info("Added track to RTCPeerConnection")

        logger.info("Creating answer...")
        answer = await pc.createAnswer()
        logger.info("Answer created: %s", answer)

        logger.info("Setting local description...")
        await pc.setLocalDescription(answer)
        logger.info("Local description set with answer: %s", answer)

        await gather_ice_candidates(logger, pc)

        return pc.localDescription
    except Exception as e:
        logger.error("Exception in handle_offer: %s", str(e))
        raise


async def handle_candidate(logger, pc, candidate):
    try:
        logger.info("Adding ICE candidate: %s", candidate)
        ice_candidate = RTCIceCandidate(
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"],
            candidate=candidate["candidate"],
        )
        await pc.addIceCandidate(ice_candidate)
        logger.info("ICE candidate added")
    except Exception as e:
        logger.error("Exception in handle_candidate: %s", str(e))
        raise


async def gather_ice_candidates(logger, pc):
    complete = asyncio.Event()

    @pc.on("icecandidate")
    def on_icecandidate(event):
        if event.candidate is None:
            logger.info("ICE gathering complete")
            complete.set()

    logger.info("Waiting for ICE gathering to complete...")
    await complete.wait()
    logger.info("ICE gathering state is now complete")


pc = None  # 전역 RTCPeerConnection 객체


def request_webRTC(url, message):
    global pc  # 전역 객체 사용
    try:
        logger.info("request_webRTC called with url: %s and message: %s", url, message)

        if url == "/setup":
            data = message
            response = None

            logger.info("Handling WebRTC setup")
            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            logger.info("Created RTCSessionDescription: %s", offer)

            pc = RTCPeerConnection()
            logger.info("Created RTCPeerConnection")

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
                    logger.info("ICE candidate gathered: %s", candidate_message)

            @pc.on("track")
            def on_track(event):
                logger.info("Track received: %s", event)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created and set")
            answer = loop.run_until_complete(handle_offer(logger, pc, offer))
            logger.info("Created answer: %s", answer)

            response = json.dumps({"sdp": answer.sdp, "type": answer.type})
            logger.info("Response created: %s", response)

            return response

        elif url == "/candidate":
            logger.info("Handling ICE candidate")
            data = message

            if not pc:
                raise Exception("No peer connection found")

            candidate = RTCIceCandidate(
                candidate=data["candidate"],
                sdpMid=data["sdpMid"],
                sdpMLineIndex=data["sdpMLineIndex"],
            )
            logger.info("Created RTCIceCandidate: %s", candidate)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created and set")
            loop.run_until_complete(pc.addIceCandidate(candidate))
            logger.info("Added ICE candidate to pc")

            return json.dumps({"message": "ICE candidate added"})

    except Exception as e:
        logger.error("Exception in request_webRTC: %s", str(e))
        return json.dumps({"error": str(e)})

    try:
        logger.info("request_webRTC called with url: %s and message: %s", url, message)

        if url == "/setup":
            data = message
            response = None

            logger.info("Handling WebRTC setup")
            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            logger.info("Created RTCSessionDescription: %s", offer)

            pc = RTCPeerConnection()
            connections[data["printerId"]] = pc  # printerId를 사용하여 pc 저장
            logger.info("Created RTCPeerConnection")

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
                    logger.info("ICE candidate gathered: %s", candidate_message)

            @pc.on("track")
            def on_track(event):
                logger.info("Track received: %s", event)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created and set")
            answer = loop.run_until_complete(handle_offer(logger, pc, offer))
            logger.info("Created answer: %s", answer)

            response = json.dumps({"sdp": answer.sdp, "type": answer.type})
            logger.info("Response created: %s", response)

            return response

        elif url == "/candidate":
            logger.info("Handling ICE candidate")
            data = message

            pc = connections.get(data["printerId"])  # printerId로 pc 조회

            if not pc:
                raise Exception(
                    "No peer connection found for printerId: %s" % data["printerId"]
                )

            candidate = RTCIceCandidate(
                candidate=data["candidate"],
                sdpMid=data["sdpMid"],
                sdpMLineIndex=data["sdpMLineIndex"],
            )
            logger.info("Created RTCIceCandidate: %s", candidate)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created and set")
            loop.run_until_complete(pc.addIceCandidate(candidate))
            logger.info("Added ICE candidate to pc")

            return json.dumps({"message": "ICE candidate added"})

    except Exception as e:
        logger.error("Exception in request_webRTC: %s", str(e))
        return json.dumps({"error": str(e)})
