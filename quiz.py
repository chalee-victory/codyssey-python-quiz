"""퀴즈 한 문제를 표현하는 Quiz 클래스."""


class Quiz:
    """문제(question), 선택지 4개(choices), 정답 번호(answer, 1~4), 힌트(hint)를 가진 퀴즈 한 개."""

    CHOICE_COUNT = 4  # 선택지는 항상 4개

    def __init__(self, question: str, choices: list[str], answer: int, hint: str = "") -> None:
        # 잘못된 퀴즈가 만들어지지 않도록 생성 시점에 검사한다.
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 비어 있지 않은 문자열이어야 합니다.")
        if not isinstance(choices, list) or len(choices) != self.CHOICE_COUNT:
            raise ValueError(f"선택지는 {self.CHOICE_COUNT}개여야 합니다.")
        if not all(isinstance(choice, str) and choice.strip() for choice in choices):
            raise ValueError("선택지는 모두 비어 있지 않은 문자열이어야 합니다.")
        # bool은 int의 하위 타입이라 True가 1로 통과하는 것을 막는다.
        if isinstance(answer, bool) or not isinstance(answer, int):
            raise ValueError("정답은 정수(번호)여야 합니다.")
        if not 1 <= answer <= self.CHOICE_COUNT:
            raise ValueError(f"정답은 1~{self.CHOICE_COUNT} 사이 번호여야 합니다.")
        if not isinstance(hint, str):
            raise ValueError("힌트는 문자열이어야 합니다.")

        self.question = question.strip()
        self.choices = [choice.strip() for choice in choices]
        self.answer = answer
        self.hint = hint.strip()  # 빈 문자열이면 "힌트 없음"

    def has_hint(self) -> bool:
        return self.hint != ""

    def display(self, number: int) -> None:
        """문제 번호와 함께 문제·선택지를 출력한다."""
        print(f"[문제 {number}]")
        print(self.question)
        print()
        for index, choice in enumerate(self.choices, start=1):
            print(f"{index}. {choice}")
        print()

    def is_correct(self, user_answer: int) -> bool:
        """사용자가 고른 번호가 정답이면 True를 돌려준다."""
        return user_answer == self.answer

    def correct_choice_text(self) -> str:
        """정답 번호에 해당하는 선택지 문장을 돌려준다."""
        return self.choices[self.answer - 1]

    def to_dict(self) -> dict:
        """JSON으로 저장할 수 있도록 dict로 바꾼다."""
        return {
            "question": self.question,
            "choices": list(self.choices),
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        """dict(JSON에서 읽은 값)로부터 Quiz를 만든다. 형식이 틀리면 예외가 난다."""
        if not isinstance(data, dict):
            raise ValueError("퀴즈 데이터는 dict 형식이어야 합니다.")
        # hint는 나중에 추가된 필드라, 예전 state.json에 없어도 읽을 수 있도록 get으로 꺼낸다.
        return cls(data["question"], data["choices"], data["answer"], data.get("hint", ""))