QUESTION_TYPE_MODIFIER = {
    "FOLLOW_UP": 0,
    "VALIDATION": 0,
    "PROBE": 0,
    "CHALLENGE": 1,
    "TRADEOFF": 1,
    "EDGE_CASE": 1,
    "FAILURE_SCENARIO": 1,
    "DEEP_DIVE": 1,
    "ESTIMATION": 1,
}


class DifficultyController:

    def calculate(
        self,
        state: dict,
        topic: str,
        question_type: str,
    ) -> int:

        profile = state.get(
            "skill_profile",
            {},
        )

        skill = profile.get(
            topic,
            {},
        )

        score = skill.get(
            "score",
            3.0,
        )

        confidence = skill.get(
            "confidence",
            0.0,
        )

        current = state.get(
            "current_difficulty",
            2,
        )

        # Candidate is clearly strong
        if (
            score >= 4.2
            and confidence >= 0.6
        ):
            base = current + 1

        # Candidate is clearly weak
        elif (
            score <= 2.0
            and confidence >= 0.6
        ):
            base = current - 1

        else:
            base = current

        modifier = QUESTION_TYPE_MODIFIER.get(
            question_type,
            0,
        )

        return max(
            1,
            min(
                5,
                base + modifier,
            ),
        )