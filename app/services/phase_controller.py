PHASE_ORDER = [
    "REQUIREMENTS",
    "CAPACITY_PLANNING",
    "HIGH_LEVEL_DESIGN",
    "DESIGN_REVIEW",
    "DEEP_DIVE",
    "TRADEOFFS",
    "EVALUATION",
]


class PhaseController:

    def can_move_to(
        self,
        current: str,
        target: str,
    ) -> bool:

        try:
            current_index = PHASE_ORDER.index(
                current
            )

            target_index = PHASE_ORDER.index(
                target
            )

            # Only allow moving exactly one
            # phase forward.
            return (
                target_index
                == current_index + 1
            )

        except ValueError:
            return False

    def get_next_phase(
        self,
        current: str,
    ) -> str | None:

        try:
            index = PHASE_ORDER.index(
                current
            )

            if index + 1 >= len(PHASE_ORDER):
                return None

            return PHASE_ORDER[index + 1]

        except ValueError:
            return None