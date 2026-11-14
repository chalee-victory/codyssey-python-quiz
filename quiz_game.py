"""게임 전체 흐름(메뉴, 기능 선택, 종료)을 관리하는 QuizGame 클래스."""

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_text
from quiz import Quiz

LINE = "=" * 40


class QuizGame:
    """퀴즈 게임 전체를 관리한다."""

    def __init__(self) -> None:
        self.quizzes: list[Quiz] = get_default_quizzes()
        # 최고 점수 정보. 아직 한 번도 풀지 않았으면 None으로 구분한다.
        self.best_score: int | None = None
        self.best_correct = 0
        self.best_total = 0
        self.is_running = True

        # 9단계: 메뉴 = (화면에 보일 이름, 실행할 메서드) 목록.
        # 메뉴를 추가/변경할 때 이 리스트만 고치면 출력과 실행이 함께 바뀐다.
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
        """메뉴를 반복해서 보여 주고, 선택한 기능을 실행한다."""
        try:
            while self.is_running:
                self.show_menu()
                choice = ask_int("선택: ", 1, len(self.menu))
                _title, action = self.menu[choice - 1]  # 9단계: if/elif 대신 표에서 꺼내 실행
                action()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 또는 입력 스트림 종료 → 비정상 종료 대신 안내 후 종료
            print("\n\n⚠️ 입력이 중단되었습니다. 프로그램을 안전하게 종료합니다.")

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
        """저장된 퀴즈를 차례로 출제하고 결과를 보여 준다."""
        if not self.quizzes:
            print("\n📭 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        total = len(self.quizzes)
        correct_count = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제)")

        for number, quiz in enumerate(self.quizzes, start=1):  # 정해진 목록을 순회 → for
            if self.ask_one_question(quiz, number):
                correct_count += 1

        score = self.calculate_score(correct_count, total)
        self.show_result(score, correct_count, total)

    def ask_one_question(self, quiz: Quiz, number: int) -> bool:
        """9단계: 문제 하나를 출제하고 정답이면 True를 돌려준다."""
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
        """9단계: 정답 수를 100점 만점 점수로 환산한다."""
        return round(correct / total * 100)

    def show_result(self, score: int, correct: int, total: int) -> None:
        """9단계: 결과를 출력하고 최고 점수를 갱신한다."""
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
        print(f"\n✅ 퀴즈가 추가되었습니다! (현재 총 {len(self.quizzes)}개)")

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
        print("\n👋 게임을 종료합니다. 다음에 또 만나요!")
        self.is_running = False