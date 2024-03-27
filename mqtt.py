from awscrt import mqtt, io
from awsiot import mqtt_connection_builder
import time
import json
import log

# 로그 설정
logger = log.setup_logger()

# AWS IoT Core 설정 (환경에 맞게 수정 필요)
endpoint = "a2k61xlc47ga1s-ats.iot.us-east-1.amazonaws.com"
cert = "./AWS/L0Xi6p3yoBqG8XWbaGf7.cert.pem"
key = "./AWS/L0Xi6p3yoBqG8XWbaGf7.private.key"
root_ca = "./AWS/root-CA.crt"
client_id = "basicPubSub"
topic = "sdk/test/python"

# 연결 중단 시 호출될 콜백
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted: {error}")

# 연결 재개 시 호출될 콜백
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Connection resumed: return_code: {return_code}, session_present: {session_present}")

# 메시지 수신 시 호출될 콜백
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    message = payload.decode('utf-8')
    logger.info(f"Received message from '{topic}': {message}")

def setup_mqtt_connection():
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=key,
        ca_filepath=root_ca,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed
    )

    # 연결 시도
    logger.info("Connecting to MQTT broker...")
    connect_future = mqtt_connection.connect()
    connect_future.result()  # 연결 완료까지 대기
    logger.info("Connected to MQTT broker")
    
    return mqtt_connection

def main():
    mqtt_connection = setup_mqtt_connection()
    
    # 토픽 구독
    logger.info(f"Subscribing to topic L0Xi6p3yoBqG8XWbaGf7/cmd ...")
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic="L0Xi6p3yoBqG8XWbaGf7/cmd",
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )
    subscribe_future.result()  # 구독 완료까지 대기
    logger.info(f"Subscribed to L0Xi6p3yoBqG8XWbaGf7/cmd")

    # 메시지 발행 (실제 사용 시 필요에 따라 구현)
    # publish_message(mqtt_connection)

    # 연결 종료 처리 예시 (필요에 따라 적절한 종료 조건 추가)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Disconnecting from MQTT broker...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        logger.info("Disconnected")

if __name__ == "__main__":
    main()