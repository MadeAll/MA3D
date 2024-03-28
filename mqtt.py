from awscrt import mqtt, io
from awsiot import mqtt_connection_builder
import api_handler
import threading
import time

# 로그 설정
logger = None

# AWS IoT Core 설정 (환경에 맞게 수정 필요)
endpoint = "a2k61xlc47ga1s-ats.iot.us-east-1.amazonaws.com"
cert = "/home/biqu/MA3D/AWS/L0Xi6p3yoBqG8XWbaGf7.cert.pem"
key = "/home/biqu/MA3D/AWS/L0Xi6p3yoBqG8XWbaGf7.private.key"
root_ca = "/home/biqu/MA3D/AWS/root-CA.crt"
client_id = "L0Xi6p3yoBqG8XWbaGf7"
topic = "L0Xi6p3yoBqG8XWbaGf7"

# 연결 객체 초기화
mqtt_connection = None


# 연결 중단 시 호출될 콜백
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted: {error}")


# 연결 재개 시 호출될 콜백
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(
        f"Connection resumed: return_code: {return_code}, session_present: {session_present}"
    )


# 메시지 수신 시 호출될 콜백
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    message = payload.decode("utf-8")
    logger.info(f"Received message from '{topic}': {message}")
    response = api_handler.main(message)

    # 응답 토픽 정의 (예: {printerID}/res)
    response_topic = topic.replace("/cmd", "/res")
    logger.info(f"Publishing message to '{response_topic}': {response}")
    # 메시지를 {printerID}/res 토픽으로 재전송
    mqtt_connection.publish(
        topic=response_topic, payload=response, qos=mqtt.QoS.AT_LEAST_ONCE
    )


# 타이머를 저장할 전역 변수
timers = []


def publish_status():
    global timers
    logger.info("Get Printer Status")
    message = api_handler.getStatus(logger)
    mqtt_connection.publish(
        topic=topic + "/status", payload=message, qos=mqtt.QoS.AT_LEAST_ONCE
    )

    # 이전 타이머가 있으면 취소
    if timers:
        for timer in timers:
            timer.cancel()
        timers.clear()

    # 새 타이머 생성 및 시작
    timer = threading.Timer(10.0, publish_status)
    timer.start()
    timers.append(timer)


# 프로그램 종료 시 호출될 함수
def cleanup():
    global timers
    for timer in timers:
        timer.cancel()
    logger.info("Cleaned up timers.")


def setup_mqtt_connection():
    global mqtt_connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=key,
        ca_filepath=root_ca,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
    )

    # 연결 시도
    logger.info("Connecting to MQTT broker...")
    connect_future = mqtt_connection.connect()
    connect_future.result()  # 연결 완료까지 대기
    logger.info("Connected to MQTT broker")

    return mqtt_connection


def main(log):
    global logger
    logger = log
    mqtt_connection = setup_mqtt_connection()

    # 토픽 구독
    logger.info(f"Subscribing to topic '{topic}/req' ...")
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=topic + "/req", qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
    )
    subscribe_future.result()  # 구독 완료까지 대기
    logger.info(f"Subscribed to '{topic}/req'")

    publish_status()

    # 연결 종료 처리 예시 (필요에 따라 적절한 종료 조건 추가)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Disconnecting from MQTT broker...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        cleanup()
        logger.info("Disconnected")


if __name__ == "__main__":
    main()
