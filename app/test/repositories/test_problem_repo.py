from app.repositories.problem_repository import (
    ProblemRepository,
)


repository = ProblemRepository()

# resturn dict of url shortner
problem = repository.get(
    "url-shortener"
)

# return None
problem = repository.get(
    "does_not_exist"
)



print(problem)