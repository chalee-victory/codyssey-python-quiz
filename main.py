
"""퀴즈 게임 실행 진입점.  실행 방법: python main.py"""

from pathlib import Path

from quiz_game import QuizGame

# 어느 폴더에서 실행하든 항상 "프로젝트 루트(main.py가 있는 폴더)/state.json"을 사용한다.
STATE_FILE = Path(__file__).resolve().parent / "state.json"


def main() -> None:
    game = QuizGame(STATE_FILE)
    game.run()


if __name__ == "__main__":
    main()