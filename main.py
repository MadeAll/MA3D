import mqtt
import log


def main():
    logger = log.setup_logger()
    logger.info("Application started")

    try:
        mqtt.main(logger)
        logger.info("Subscribed to MQTT topic")
        # 메인 로직 유지 (예: 무한 루프, 사용자 입력 처리 등)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Application finished")


if __name__ == "__main__":
    main()
