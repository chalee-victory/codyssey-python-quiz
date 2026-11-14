"""사용자 입력을 안전하게 받기 위한 도우미 함수 모음.

- 입력 앞뒤 공백은 strip()으로 제거한 뒤 처리한다.
- 잘못된 입력이면 안내 메시지를 출력하고 다시 묻는다.
- Ctrl+C(KeyboardInterrupt), EOFError는 여기서 잡지 않고
  QuizGame.run으로 올려 보내 '안전 종료'를 한 곳에서 처리한다.
"""


def ask_int(prompt: str, min_value: int, max_value: int) -> int:
    """min_value~max_value 범위의 정수를 입력받아 반환한다."""
    range_message = f"⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요."

    while True:  # 몇 번 만에 올바른 값이 들어올지 모르므로 while 사용
        raw = input(prompt).strip()

        if raw == "":
            print("⚠️ 입력이 비어 있습니다. 숫자를 입력하세요.")
            continue

        try:
            value = int(raw)
        except ValueError:  # "abc"처럼 숫자로 바꿀 수 없는 경우
            print(range_message)
            continue

        if not min_value <= value <= max_value:  # 메뉴 9, 정답 0 같은 범위 밖 숫자
            print(range_message)
            continue

        return value