from awscrt import mqtt, auth, io
from awsiot import mqtt_connection_builder
import requests
import time
import json
import base64

# Define your AWS IoT Core parameters here
endpoint = "a2k61xlc47ga1s-ats.iot.us-east-1.amazonaws.com"
cert = "MA3D/AWS/L0Xi6p3yoBqG8XWbaGf7.cert.pem"
key = "MA3D/AWS/L0Xi6p3yoBqG8XWbaGf7.private.key"
root_ca = "MA3D/AWS/root-CA.crt"
client_id = "YOUR_CLIENT_ID"
topic = "topic_req"

# Callback for connection interruption
def on_connection_interrupted(connection, error, **kwargs):
    print(f"Connection interrupted: {error}")

# Callback for connection resumption
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed")

# Callback for when message is received
def on_message_received(topic, payload, **kwargs):
    message = json.loads(payload.decode('utf-8'))
    
    # Extract method and path from the message
    method = message.get("method").upper()  # GET, POST, PATCH, etc.
    path = message.get("path")  # API endpoint, e.g., /server/info
    
    print(f"Received message from {topic}, {method}, {path}")

    # Construct the Moonraker API URL
    moonraker_url = f"http://localhost{path}"
    
    if method == 'GET':
        response = requests.get(moonraker_url)
    elif method == 'POST':
        response = requests.post(moonraker_url, data=message.get("data", {}))
    elif method == 'DELETE':
        response = requests.delete(moonraker_url)
    elif method == 'SNAPSHOT':
        snapshot_url = 'http://localhost/webcam/?action=snapshot'
        snapshot_response = requests.get(snapshot_url)

        if snapshot_response.status_code == 200:
            encoded_image = base64.b64encode(snapshot_response.content).decode('utf-8')
            mqtt_connection.publish(topic="topic_res", payload=json.dumps({"image": encoded_image}), qos=mqtt.QoS.AT_LEAST_ONCE)
        else:
            print(f"Failed to fetch snapshot, Status code: {snapshot_response.status_code}")
            mqtt_connection.publish(topic="topic_res", payload=json.dumps({"error": "Failed to fetch snapshot"}), qos=mqtt.QoS.AT_LEAST_ONCE)
    
    # Make sure the following block only handles 'GET', 'POST', 'DELETE'
    if method in ['GET', 'POST', 'DELETE']:
        if response.status_code == 200:
            mqtt_connection.publish(topic="topic_res", payload=json.dumps(response.json()), qos=mqtt.QoS.AT_LEAST_ONCE)
        else:
            mqtt_connection.publish(topic="topic_res", payload=json.dumps({"error": response.status_code}), qos=mqtt.QoS.AT_LEAST_ONCE)

# Initialize MQTT connection
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=endpoint,
    cert_filepath=cert,
    pri_key_filepath=key,
    client_bootstrap=client_bootstrap,
    ca_filepath=root_ca,
    client_id=client_id,
    clean_session=False,
    keep_alive_secs=30)

# Connect
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected to AWS IoT Core")

# Subscribe to topic
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic=topic,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received)
subscribe_future.result()
print(f"Subscribed to {topic}")

# Keep the program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected")
