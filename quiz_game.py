"""게임 전체 흐름(메뉴, 기능 선택, 저장/불러오기, 종료)을 관리하는 QuizGame 클래스."""

import json
import os
import random
from pathlib import Path

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_text
from quiz import Quiz

LINE = "=" * 40


class QuizGame:
    """퀴즈 게임 전체를 관리한다."""

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)  # 10단계: 데이터 파일 위치
        self.quizzes: list[Quiz] = get_default_quizzes()
        # 최고 점수 정보. 아직 한 번도 풀지 않았으면 None으로 구분한다.
        self.best_score: int | None = None
        self.best_correct = 0
        self.best_total = 0
        self.is_running = True

        # 메뉴 = (화면에 보일 이름, 실행할 메서드) 목록.
        self.menu = [
            ("퀴즈 풀기", self.play_quiz),
            ("퀴즈 추가", self.add_quiz),
            ("퀴즈 목록", self.list_quizzes),
            ("점수 확인", self.show_score),
            ("종료", self.exit_game),
        ]

    # ------------------------------------------------------------------
    # 메인 루프와 메뉴
    # ------------------------------------------------------------------
    def run(self) -> None:
        """저장된 데이터를 불러온 뒤, 메뉴를 반복해서 보여 주고 선택한 기능을 실행한다."""
        print(LINE)
        print("        🎯 나만의 퀴즈 게임 🎯")
        print(LINE)
        self.load_state()  # 10단계

        try:
            while self.is_running:
                self.show_menu()
                choice = ask_int("선택: ", 1, len(self.menu))
                _title, action = self.menu[choice - 1]
                action()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 또는 입력 스트림 종료 → 비정상 종료 대신 저장 후 안내하고 종료
            print("\n\n⚠️ 입력이 중단되었습니다. 데이터를 저장하고 안전하게 종료합니다.")
            self.save_state()  # 10단계

    def show_menu(self) -> None:
        print()
        print(LINE)
        print("        🎯 나만의 퀴즈 게임 🎯")
        print(LINE)
        for number, (title, _action) in enumerate(self.menu, start=1):
            print(f"{number}. {title}")
        print(LINE)

    # ------------------------------------------------------------------
    # 1. 퀴즈 풀기
    # ------------------------------------------------------------------


    def play_quiz(self) -> None:
        """풀 문제 수를 고르게 한 뒤, 퀴즈를 무작위 순서로 출제하고 결과를 보여 준다."""
        if not self.quizzes:
            print("\n📭 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        available = len(self.quizzes)
        print(f"\n등록된 퀴즈는 {available}개입니다.")
        total = ask_int(f"몇 문제를 풀까요? (1-{available}): ", 1, available)

        # random.sample: 원본 목록은 그대로 두고, 겹치지 않게 total개를 무작위 순서로 뽑는다.
        selected = random.sample(self.quizzes, total)
        correct_count = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제, 랜덤 출제)")

        for number, quiz in enumerate(selected, start=1):  # 정해진 목록을 순회 → for
            if self.ask_one_question(quiz, number):
                correct_count += 1

        score = self.calculate_score(correct_count, total)
        self.show_result(score, correct_count, total)


    def ask_one_question(self, quiz: Quiz, number: int) -> bool:
        """문제 하나를 출제하고 정답이면 True를 돌려준다."""
        print("\n" + "-" * 40)
        quiz.display(number)
        user_answer = ask_int(f"정답 입력 (1-{Quiz.CHOICE_COUNT}): ", 1, Quiz.CHOICE_COUNT)

        if quiz.is_correct(user_answer):
            print("✅ 정답입니다!")
            return True
        print(f"❌ 오답입니다. 정답은 {quiz.answer}번 ({quiz.correct_choice_text()}) 입니다.")
        return False

    @staticmethod
    def calculate_score(correct: int, total: int) -> int:
        """정답 수를 100점 만점 점수로 환산한다."""
        return round(correct / total * 100)

    def show_result(self, score: int, correct: int, total: int) -> None:
        """결과를 출력하고 최고 점수를 갱신한다."""
        print("\n" + LINE)
        print(f"🏆 결과: {total}문제 중 {correct}문제 정답! ({score}점)")
        if self.update_best_score(score, correct, total):
            print("🎉 새로운 최고 점수입니다!")
        else:
            print(f"📈 현재 최고 점수: {self.best_score}점")
        print(LINE)

    def update_best_score(self, score: int, correct: int, total: int) -> bool:
        """이번 점수가 최고 점수보다 높으면 갱신하고 True를 돌려준다."""
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            self.best_correct = correct
            self.best_total = total
            self.save_state()  # 10단계: 최고 점수가 바뀌면 바로 파일에 기록
            return True
        return False

    # ------------------------------------------------------------------
    # 2. 퀴즈 추가
    # ------------------------------------------------------------------
    def add_quiz(self) -> None:
        """문제, 선택지 4개, 정답 번호를 입력받아 새 퀴즈를 등록한다."""
        print("\n📌 새로운 퀴즈를 추가합니다.\n")
        question = ask_text("문제를 입력하세요: ")

        choices: list[str] = []
        while len(choices) < Quiz.CHOICE_COUNT:
            choice = ask_text(f"선택지 {len(choices) + 1}: ")
            if choice in choices:  # 같은 선택지가 두 번 들어가면 문제가 성립하지 않음
                print("⚠️ 이미 입력한 선택지입니다. 다른 내용을 입력하세요.")
                continue
            choices.append(choice)

        answer = ask_int(f"정답 번호 (1-{Quiz.CHOICE_COUNT}): ", 1, Quiz.CHOICE_COUNT)

        self.quizzes.append(Quiz(question, choices, answer))
        if self.save_state():  # 10단계: 추가한 퀴즈를 파일에 저장
            print(f"\n✅ 퀴즈가 추가되었습니다! (현재 총 {len(self.quizzes)}개)")
        else:
            print("\n⚠️ 퀴즈는 추가했지만 파일 저장에 실패했습니다. 종료 시 다시 저장을 시도합니다.")

    # ------------------------------------------------------------------
    # 3. 퀴즈 목록
    # ------------------------------------------------------------------
    def list_quizzes(self) -> None:
        """등록된 퀴즈의 문제 목록을 번호와 함께 보여 준다."""
        if not self.quizzes:
            print("\n📭 등록된 퀴즈가 없습니다.")
            return

        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)\n")
        print("-" * 40)
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"[{number}] {quiz.question}")
        print("-" * 40)

    # ------------------------------------------------------------------
    # 4. 점수 확인
    # ------------------------------------------------------------------
    def show_score(self) -> None:
        """최고 점수를 보여 준다. 아직 풀지 않았다면 안내한다."""
        if self.best_score is None:
            print("\n📭 아직 퀴즈를 풀지 않았습니다. 먼저 퀴즈를 풀어 보세요!")
            return
        print(
            f"\n🏆 최고 점수: {self.best_score}점 "
            f"({self.best_total}문제 중 {self.best_correct}문제 정답)"
        )

    # ------------------------------------------------------------------
    # 5. 종료
    # ------------------------------------------------------------------
    def exit_game(self) -> None:
        self.save_state()  # 10단계
        print("\n👋 게임을 종료합니다. 다음에 또 만나요!")
        self.is_running = False

    # ------------------------------------------------------------------
    # 10단계: 파일 저장 / 불러오기 (state.json)
    # ------------------------------------------------------------------
    def to_state(self) -> dict:
        """현재 게임 상태를 JSON으로 저장할 dict로 만든다."""
        return {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "best_correct": self.best_correct,
            "best_total": self.best_total,
        }

    def save_state(self) -> bool:
        """state.json에 UTF-8로 저장한다. 성공하면 True.

        임시 파일에 먼저 쓴 뒤 os.replace로 바꿔치기한다.
        저장 도중 프로그램이 끊겨도 기존 state.json이 반쯤 쓰인 채로 깨지지 않게 하기 위함이다.
        """
        temp_path = self.state_path.with_name(self.state_path.name + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(self.to_state(), file, ensure_ascii=False, indent=4)
            os.replace(temp_path, self.state_path)
            return True
        except OSError as error:  # 권한 없음, 디스크 가득 참 등
            print(f"⚠️ 데이터 저장에 실패했습니다: {error}")
            return False

    def load_state(self) -> None:
        """state.json을 불러온다. 없거나 손상되었으면 기본 데이터로 시작한다."""
        if not self.state_path.exists():
            print(f"📂 저장된 데이터가 없어 기본 퀴즈 {len(self.quizzes)}개로 시작합니다.")
            self.save_state()
            return

        try:
            with open(self.state_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.apply_state(data)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError):
            self.recover_from_broken_file()
            return
        except OSError as error:  # 파일은 있지만 읽을 수 없는 경우(권한 등)
            print(f"⚠️ 데이터 파일을 읽지 못했습니다({error}). 기본 퀴즈로 시작합니다.")
            self.reset_to_default()
            return

        best_text = "기록 없음" if self.best_score is None else f"{self.best_score}점"
        print(f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고점수 {best_text})")

    def apply_state(self, data: dict) -> None:
        """JSON에서 읽은 dict를 검사하고 게임 상태에 반영한다. 형식이 틀리면 예외가 난다."""
        if not isinstance(data, dict):
            raise ValueError("최상위 데이터가 dict가 아닙니다.")

        raw_quizzes = data["quizzes"]
        if not isinstance(raw_quizzes, list):
            raise ValueError("quizzes는 리스트여야 합니다.")
        quizzes = [Quiz.from_dict(item) for item in raw_quizzes]

        best_score = data.get("best_score")
        best_correct = data.get("best_correct", 0)
        best_total = data.get("best_total", 0)
        if best_score is not None:
            for value in (best_score, best_correct, best_total):
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError("점수 정보는 정수여야 합니다.")
            if not 0 <= best_score <= 100:
                raise ValueError("best_score는 0~100 사이여야 합니다.")

        # 모든 검사를 통과한 뒤에 한꺼번에 반영 → 절반만 반영되는 일을 막는다.
        self.quizzes = quizzes
        self.best_score = best_score
        self.best_correct = best_correct if best_score is not None else 0
        self.best_total = best_total if best_score is not None else 0

    def recover_from_broken_file(self) -> None:
        """손상된 파일을 백업해 두고 기본 데이터로 복구한다."""
        backup_path = self.state_path.with_name(self.state_path.name + ".broken")
        print("⚠️ 데이터 파일이 손상되어 기본 퀴즈 데이터로 복구합니다.")
        try:
            os.replace(self.state_path, backup_path)
            print(f"   (손상된 파일은 {backup_path.name} 으로 보관했습니다.)")
        except OSError:
            pass  # 백업에 실패해도 게임은 계속 진행한다.
        self.reset_to_default()

    def reset_to_default(self) -> None:
        """기본 퀴즈와 빈 점수 기록으로 초기화하고 저장한다."""
        self.quizzes = get_default_quizzes()
        self.best_score = None
        self.best_correct = 0
        self.best_total = 0
        self.save_state()