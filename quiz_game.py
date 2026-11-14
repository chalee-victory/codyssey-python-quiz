"""게임 전체 흐름(메뉴, 기능 선택, 종료)을 관리하는 QuizGame 클래스."""

from default_quizzes import get_default_quizzes
from input_utils import ask_int
from quiz import Quiz

LINE = "=" * 40


class QuizGame:
    """퀴즈 게임 전체를 관리한다."""

    MENU_ITEMS = ["퀴즈 풀기", "퀴즈 추가", "퀴즈 목록", "점수 확인", "종료"]

    def __init__(self) -> None:
        self.quizzes: list[Quiz] = get_default_quizzes()
        self.is_running = True

    def show_menu(self) -> None:
        print()
        print(LINE)
        print("        🎯 나만의 퀴즈 게임 🎯")
        print(LINE)
        for number, title in enumerate(self.MENU_ITEMS, start=1):
            print(f"{number}. {title}")
        print(LINE)

    def run(self) -> None:
        """메뉴를 반복해서 보여 주고, 선택한 기능을 실행한다."""
        try:
            while self.is_running:
                self.show_menu()
                choice = ask_int("선택: ", 1, len(self.MENU_ITEMS))

                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    print("\n🚧 퀴즈 추가 기능은 준비 중입니다.")
                elif choice == 3:
                    print("\n🚧 퀴즈 목록 기능은 준비 중입니다.")
                elif choice == 4:
                    print("\n🚧 점수 확인 기능은 준비 중입니다.")
                else:
                    self.exit_game()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 또는 입력 스트림 종료 → 비정상 종료 대신 안내 후 종료
            print("\n\n⚠️ 입력이 중단되었습니다. 프로그램을 안전하게 종료합니다.")

    def play_quiz(self) -> None:
        """저장된 퀴즈를 차례로 출제하고 결과를 보여 준다."""
        if not self.quizzes:
            print("\n📭 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        total = len(self.quizzes)
        correct_count = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제)")

        for number, quiz in enumerate(self.quizzes, start=1):  # 정해진 목록을 순회 → for
            print("\n" + "-" * 40)
            quiz.display(number)
            user_answer = ask_int(f"정답 입력 (1-{Quiz.CHOICE_COUNT}): ", 1, Quiz.CHOICE_COUNT)

            if quiz.is_correct(user_answer):
                correct_count += 1
                print("✅ 정답입니다!")
            else:
                print(f"❌ 오답입니다. 정답은 {quiz.answer}번 ({quiz.correct_choice_text()}) 입니다.")
        score = round(correct_count / total * 100)
        print("\n" + LINE)
        print(f"🏆 결과: {total}문제 중 {correct_count}문제 정답! ({score}점)")
        print(LINE)

    def exit_game(self) -> None:
        print("\n👋 게임을 종료합니다. 다음에 또 만나요!")
        self.is_running = False