import json
from awscrt import mqtt, auth, io
from awsiot import mqtt_connection_builder

import log

logger = log.setup_logger()

# Define your AWS IoT Core parameters here
endpoint = "a2k61xlc47ga1s-ats.iot.us-east-1.amazonaws.com"
cert = "AWS/L0Xi6p3yoBqG8XWbaGf7.cert.pem"
key = "AWS/L0Xi6p3yoBqG8XWbaGf7.private.key"
root_ca = "AWS/root-CA.crt"
client_id = "YOUR_CLIENT_ID"
topic = "topic_req"

# 연결 중단 시 호출될 콜백
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted: {error}")

# 연결 재개 시 호출될 콜백
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info("Connection resumed")

# 메시지 수신 시 호출될 콜백
def on_message_received(topic, payload, **kwargs):
    message = json.loads(payload.decode('utf-8'))
    logger.info(f"Received message from '{topic}': {message}")
    # 메시지 처리 로직 추가

def setup_mqtt_connection():
    # MQTT 연결 설정
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=key,
        ca_filepath=root_ca,
        client_bootstrap=io.ClientBootstrap(io.EventLoopGroup(1), io.DefaultHostResolver(io.EventLoopGroup(1))),
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30)

    # 연결 및 콜백 설정
    mqtt_connection.on_connection_interrupted = on_connection_interrupted
    mqtt_connection.on_connection_resumed = on_connection_resumed
    logger.info("Connecting to MQTT broker...")
    connect_future = mqtt_connection.connect()
    connect_future.result()  # 연결 완료 대기
    logger.info("MQTT connection established.")
    
    return mqtt_connection

def start_mqtt_service():
    mqtt_connection = setup_mqtt_connection()
    # 토픽 구독
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)
    subscribe_future.result()  # 구독 완료 대기
    logger.info(f"Subscribed to {topic}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        logger.info("Disconnected")

if __name__ == "__main__":
    start_mqtt_service()