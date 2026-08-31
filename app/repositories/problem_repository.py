from app.data.problems import PROBLEMS

class ProblemRepository:

    def get(
        self,
        problem_id: str
    ) -> dict | None:

        return PROBLEMS.get(problem_id)

        