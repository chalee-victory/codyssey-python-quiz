"""게임 전체 흐름(메뉴, 기능 선택, 저장/불러오기, 종료)을 관리하는 QuizGame 클래스."""

import json
import os
import random
from datetime import datetime
from pathlib import Path

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_int_or_command, ask_text, ask_yes_no
from quiz import Quiz

LINE = "=" * 40


class QuizGame:
    """퀴즈 게임 전체를 관리한다."""

    HINT_COMMAND = "h"  # 퀴즈 풀이 중 힌트를 볼 때 입력하는 명령어

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        self.quizzes: list[Quiz] = get_default_quizzes()
        # 최고 점수 정보. 아직 한 번도 풀지 않았으면 None으로 구분한다.
        self.best_score: int | None = None
        self.best_correct = 0
        self.best_total = 0
        # 11-4: 모든 게임 기록. 각 항목은 {"played_at", "total", "correct", "hints_used", "score"} dict.
        self.history: list[dict] = []
        self.is_running = True

        # 메뉴 = (화면에 보일 이름, 실행할 메서드) 목록.
        # 메뉴를 추가/변경할 때 이 리스트만 고치면 출력과 실행이 함께 바뀐다.
        self.menu = [
            ("퀴즈 풀기", self.play_quiz),
            ("퀴즈 추가", self.add_quiz),
            ("퀴즈 목록", self.list_quizzes),
            ("점수 확인", self.show_score),
            ("퀴즈 삭제", self.delete_quiz),
            ("게임 기록", self.show_history),  # 11-4
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
        self.load_state()

        try:
            while self.is_running:
                self.show_menu()
                choice = ask_int("선택: ", 1, len(self.menu))
                _title, action = self.menu[choice - 1]
                action()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 또는 입력 스트림 종료 → 비정상 종료 대신 저장 후 안내하고 종료
            print("\n\n⚠️ 입력이 중단되었습니다. 데이터를 저장하고 안전하게 종료합니다.")
            self.save_state()

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
        hinted_correct_count = 0  # 힌트를 보고 맞힌 문제 수 (점수 절반 인정)
        hints_used = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제, 랜덤 출제)")
        print(f"💡 정답 입력 칸에 '{self.HINT_COMMAND}'를 입력하면 힌트를 볼 수 있어요. (맞히면 점수 절반)")

        for number, quiz in enumerate(selected, start=1):  # 정해진 목록을 순회 → for
            is_correct, used_hint = self.ask_one_question(quiz, number)
            if used_hint:
                hints_used += 1
            if is_correct:
                correct_count += 1
                if used_hint:
                    hinted_correct_count += 1

        score = self.calculate_score(correct_count, hinted_correct_count, total)
        self.show_result(score, correct_count, total, hints_used)
        self.record_history(score, correct_count, total, hints_used)  # 11-4
        self.save_state()  # 11-4: 최고 점수·기록을 바로 파일에 반영

    def ask_one_question(self, quiz: Quiz, number: int) -> tuple[bool, bool]:
        """문제 하나를 출제한다. (정답 여부, 힌트 사용 여부)를 돌려준다."""
        print("\n" + "-" * 40)
        quiz.display(number)
        used_hint = False

        while True:  # 힌트를 본 뒤에는 같은 문제의 답을 다시 받아야 하므로 반복
            user_input = ask_int_or_command(
                f"정답 입력 (1-{Quiz.CHOICE_COUNT}, 힌트: {self.HINT_COMMAND}): ",
                1,
                Quiz.CHOICE_COUNT,
                {self.HINT_COMMAND},
            )
            if user_input != self.HINT_COMMAND:
                break
            if not quiz.has_hint():
                print("🙅 이 문제에는 힌트가 없습니다.")
                continue
            print(f"💡 힌트: {quiz.hint}")
            used_hint = True

        if quiz.is_correct(user_input):
            if used_hint:
                print("✅ 정답입니다! (힌트 사용으로 점수 절반 인정)")
            else:
                print("✅ 정답입니다!")
            return True, used_hint
        print(f"❌ 오답입니다. 정답은 {quiz.answer}번 ({quiz.correct_choice_text()}) 입니다.")
        return False, used_hint

    @staticmethod
    def calculate_score(correct: int, hinted_correct: int, total: int) -> int:
        """100점 만점 점수로 환산한다.

        힌트 없이 맞힌 문제는 1문제, 힌트를 보고 맞힌 문제는 0.5문제로 계산한다.
        예) 5문제 중 4문제 정답(그중 1문제 힌트 사용) → (3 + 0.5) / 5 × 100 = 70점
        """
        earned = (correct - hinted_correct) + hinted_correct * 0.5
        return round(earned / total * 100)

    def show_result(self, score: int, correct: int, total: int, hints_used: int = 0) -> None:
        """결과를 출력하고 최고 점수를 갱신한다."""
        print("\n" + LINE)
        print(f"🏆 결과: {total}문제 중 {correct}문제 정답! ({score}점)")
        if hints_used:
            print(f"💡 힌트 사용: {hints_used}회")
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
            return True
        return False

    def record_history(self, score: int, correct: int, total: int, hints_used: int) -> None:
        """11-4: 이번 게임 결과를 기록 목록에 추가한다."""
        self.history.append(
            {
                "played_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total": total,
                "correct": correct,
                "hints_used": hints_used,
                "score": score,
            }
        )

    # ------------------------------------------------------------------
    # 2. 퀴즈 추가
    # ------------------------------------------------------------------
    def add_quiz(self) -> None:
        """문제, 선택지 4개, 정답 번호, 힌트(선택)를 입력받아 새 퀴즈를 등록한다."""
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
        hint = input("힌트 (없으면 Enter): ").strip()  # 힌트는 선택 입력

        self.quizzes.append(Quiz(question, choices, answer, hint))
        if self.save_state():
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
    # 5. 퀴즈 삭제 (보너스)
    # ------------------------------------------------------------------
    def delete_quiz(self) -> None:
        """목록에서 번호를 골라 퀴즈를 삭제하고 파일에 반영한다."""
        if not self.quizzes:
            print("\n📭 삭제할 퀴즈가 없습니다.")
            return

        self.list_quizzes()
        number = ask_int(f"삭제할 퀴즈 번호 (1-{len(self.quizzes)}, 취소: 0): ", 0, len(self.quizzes))
        if number == 0:
            print("↩️ 삭제를 취소했습니다.")
            return

        target = self.quizzes[number - 1]
        if not ask_yes_no(f"'{target.question}' 퀴즈를 삭제할까요? (y/n): "):
            print("↩️ 삭제를 취소했습니다.")
            return

        self.quizzes.pop(number - 1)
        self.save_state()
        print(f"🗑️ 퀴즈를 삭제했습니다. (남은 퀴즈 {len(self.quizzes)}개)")

    # ------------------------------------------------------------------
    # 6. 게임 기록 (보너스 11-4)
    # ------------------------------------------------------------------
    def show_history(self) -> None:
        """지금까지의 모든 게임 기록을 보여 준다."""
        if not self.history:
            print("\n📭 아직 게임 기록이 없습니다.")
            return

        print(f"\n📜 게임 기록 (총 {len(self.history)}회)\n")
        print("-" * 40)
        for number, record in enumerate(self.history, start=1):
            print(
                f"{number:>3}. {record['played_at']} | "
                f"{record['total']}문제 중 {record['correct']}문제 정답 | "
                f"힌트 {record['hints_used']}회 | {record['score']}점"
            )
        print("-" * 40)
        if self.best_score is not None:
            print(f"🏆 최고 점수: {self.best_score}점")

    # ------------------------------------------------------------------
    # 7. 종료
    # ------------------------------------------------------------------
    def exit_game(self) -> None:
        self.save_state()
        print("\n👋 게임을 종료합니다. 다음에 또 만나요!")
        self.is_running = False

    # ------------------------------------------------------------------
    # 파일 저장 / 불러오기 (state.json)
    # ------------------------------------------------------------------
    def to_state(self) -> dict:
        """현재 게임 상태를 JSON으로 저장할 dict로 만든다."""
        return {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "best_correct": self.best_correct,
            "best_total": self.best_total,
            "history": self.history,  # 11-4
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

        # 11-4: 예전 파일에는 history가 없을 수 있으므로 get으로 꺼낸다.
        history = data.get("history", [])
        if not isinstance(history, list):
            raise ValueError("history는 리스트여야 합니다.")
        required_keys = {"played_at", "total", "correct", "hints_used", "score"}
        for record in history:
            if not isinstance(record, dict) or not required_keys <= record.keys():
                raise ValueError("history 항목 형식이 올바르지 않습니다.")

        # 모든 검사를 통과한 뒤에 한꺼번에 반영 → 절반만 반영되는 일을 막는다.
        self.quizzes = quizzes
        self.history = history
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
        self.history = []
        self.save_state()