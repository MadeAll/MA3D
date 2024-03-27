import json
from awscrt import mqtt, io
from awsiot import mqtt_connection_builder
import log

logger = log.setup_logger()

def on_message_received(topic, payload, **kwargs):
    logger.info(f"Message received from '{topic}': {payload}")
    # 메시지 처리 로직 추가

def mqtt_connect():
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint = "a2k61xlc47ga1s-ats.iot.us-east-1.amazonaws.com",
        cert_filepath="AWS/L0Xi6p3yoBqG8XWbaGf7.cert.pem",
        pri_key_filepath="AWS/L0Xi6p3yoBqG8XWbaGf7.private.key",
        ca_filepath="AWS/root-CA.crt",
        client_bootstrap=client_bootstrap,
        client_id="test-client",
        clean_session=False,
        keep_alive_secs=30
    )

    logger.info("Connecting to MQTT broker...")
    connect_future = mqtt_connection.connect()
    connect_future.result()  # Wait for connection to complete
    logger.info("MQTT connection established.")

    return mqtt_connection

# 사용 예시
# mqtt_connection = mqtt_connect()
# mqtt_connection.subscribe("your/topic", mqtt.QoS.AT_LEAST_ONCE, on_message_received)
