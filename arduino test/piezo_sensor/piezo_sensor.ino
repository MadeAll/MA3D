// 피에조 센서를 A0 포트에 연결
const int PIEZO_PIN = A0;
// 내장 LED 핀 정의
const int LED_PIN = 13;

void setup() {
  // 시리얼 통신 초기화 (9600 baud rate)
  Serial.begin(9600);
  // LED 핀을 출력으로 설정
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  // 피에조 센서에서 아날로그 값 읽기
  int piezoValue = analogRead(PIEZO_PIN);

  // 시리얼 모니터에 값 출력
  Serial.print("Piezo Value: ");
  Serial.println(piezoValue);

  // 센서 값이 0보다 크면 LED 켜기, 아니면 끄기
  if (piezoValue > 0) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  // 100ms 딜레이 (너무 빠른 출력 방지)
  delay(25);
}