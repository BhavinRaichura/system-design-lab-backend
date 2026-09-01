import json
from typing import TypedDict
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

from app.prompts import (
    ANALYZE_CANDIDATE_SYSTEM_PROMPT,
    TUTOR_SYSTEM_PROMPT,
)

from app.schemas.tutor import (
    TutorResponseSchema,
    InterviewDecisionSchema,
    QuestionPlanSchema,
    QuestionReviewSchema,
    TutorAnalysisSchema,
    TutorState,
)
from app.clients import llm
from app.agents.context_builder import TutorContextBuilder

from app.services.difficulty_controller import (
    DifficultyController,
)

# use at the run time
@dataclass
class TutorRuntimeContext:

    session_id: str
    user_message: str

    architecture_event: dict | None = None


class TutorGraph:

    MAX_QUESTION_RETRIES = 3

    def __init__(self):

        self.analysis_llm = (
            llm.with_structured_output(
                TutorAnalysisSchema
            )
        )

        self.controller_llm = (
            llm.with_structured_output(
                InterviewDecisionSchema
            )
        )

        self.question_planner_llm = (
            llm.with_structured_output(
                QuestionPlanSchema
            )
        )

        self.question_review_llm = (
            llm.with_structured_output(
                QuestionReviewSchema
            )
        )

        self.response_llm = (
            llm.with_structured_output(
                TutorResponseSchema
            )
        )

        self.difficulty_controller = (
            DifficultyController()
        )

        self.context_builder = (
            TutorContextBuilder()
        )

        self.checkpointer = InMemorySaver()

        self.graph = self._builder()

    def _builder(self):

        graph = StateGraph(
            state_schema=TutorState,
            context_schema=TutorRuntimeContext,
        )

        # -----------------------------
        # Nodes
        # -----------------------------

        graph.add_node(
            "analyze_candidate",
            self.analyze_candidate,
        )

        graph.add_node(
            "update_candidate_model",
            self.update_candidate_model,
        )

        graph.add_node(
            "analyze_architecture",
            self.analyze_architecture,
        )

        graph.add_node(
            "interview_controller",
            self.interview_controller,
        )

        graph.add_node(
            "update_phase",
            self.update_phase,
        )

        graph.add_node(
            "clarification_node",
            self.clarification_node,
        )

        graph.add_node(
            "requirement_node",
            self.requirement_node,
        )

        graph.add_node(
            "question_planner",
            self.question_planner,
        )

        graph.add_node(
            "question_reviewer",
            self.question_reviewer,
        )

        graph.add_node(
            "select_best_question",
            self.select_best_question,
        )

        graph.add_node(
            "response_generator",
            self.response_generator,
        )

        graph.add_node(
            "update_evidence",
            self.update_evidence,
        )

        graph.add_node(
            "evaluate",
            self.evaluate,
        )

        # -----------------------------
        # Main flow
        # -----------------------------

        graph.add_edge(
            START,
            "analyze_candidate",
        )

        graph.add_edge(
            "analyze_candidate",
            "update_candidate_model",
        )

        graph.add_edge(
            "update_candidate_model",
            "analyze_architecture",
        )

        graph.add_edge(
            "analyze_architecture",
            "interview_controller",
        )

        # -----------------------------
        # Controller routing
        # -----------------------------

        graph.add_conditional_edges(
            "interview_controller",
            self.route_controller,
            {
                "clarification":
                    "clarification_node",

                "requirement":
                    "requirement_node",

                "question":
                    "question_planner",

                "move_phase":
                    "update_phase",

                "evaluate":
                    "evaluate",
            },
        )

        # -----------------------------
        # Phase transition
        # -----------------------------

        graph.add_edge(
            "update_phase",
            "question_planner",
        )

        # -----------------------------
        # Question generation loop
        # -----------------------------

        graph.add_edge(
            "question_planner",
            "question_reviewer",
        )

        graph.add_conditional_edges(
            "question_reviewer",
            self.route_question_review,
            {
                "retry":
                    "question_planner",

                "accept":
                    "response_generator",

                "select_best":
                    "select_best_question",
            },
        )

        graph.add_edge(
            "select_best_question",
            "response_generator",
        )

        # -----------------------------
        # Response completion
        # -----------------------------

        graph.add_edge(
            "clarification_node",
            "update_evidence",
        )

        graph.add_edge(
            "requirement_node",
            "update_evidence",
        )

        graph.add_edge(
            "response_generator",
            "update_evidence",
        )

        graph.add_edge(
            "update_evidence",
            END,
        )

        # Evaluation ends the interview
        graph.add_edge(
            "evaluate",
            END,
        )

        return graph.compile(
            checkpointer=self.checkpointer
        )


    def _merge_unique(
        self,
        existing: list[str],
        new: list[str]
    ) -> list[str]:
        
        result = list(existing)

        for item in new:
            if item not in result:
                result.append(item)

        return result

    def get_state(self, session_id: str):

        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        return self.graph.get_state(config)

    def debug_checkpointer(self):

        print("STORAGE:")
        print(self.checkpointer.storage)

        print("\nWRITES:")
        print(self.checkpointer.writes)

        print("\nBLOBS:")
        print(self.checkpointer.blobs)


    def analyze_candidate(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                ANALYZE_CANDIDATE_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Architecture:

                {architecture}

                Interview phase:

                {phase}

                Candidate skill profile:

                {skills}

                Previous weaknesses:

                {weaknesses}

                Candidate's latest message:

                {message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            architecture=json.dumps(
                context.get("architecture") or {},
                indent=2,
            ),
            phase=context["interview_phase"],
            skills=json.dumps(
                state.get("skill_profile", {}),
                indent=2,
            ),
            weaknesses=json.dumps(
                state.get(
                    "candidate_weaknesses",
                    [],
                ),
                indent=2,
            ),
            message=runtime.context.user_message,
        )

        result = self.analysis_llm.invoke(
            messages
        )

        analysis_data = result.model_dump()

        return {
            **state,

            "latest_analysis": analysis_data,

            "current_topic": result.topic,

            "candidate_decisions":
                self._merge_unique(
                    state.get(
                        "candidate_decisions",
                        [],
                    ),
                    result.candidate_decisions,
                ),

            "candidate_assumptions":
                self._merge_unique(
                    state.get(
                        "candidate_assumptions",
                        [],
                    ),
                    result.candidate_assumptions,
                ),

            "candidate_strengths":
                self._merge_unique(
                    state.get(
                        "candidate_strengths",
                        [],
                    ),
                    result.candidate_strengths,
                ),

            "candidate_weaknesses":
                self._merge_unique(
                    state.get(
                        "candidate_weaknesses",
                        [],
                    ),
                    result.candidate_weaknesses,
                ),

            "requirements_covered":
                self._merge_unique(
                    state.get(
                        "requirements_covered",
                        [],
                    ),
                    result.requirements_covered,
                ),

            "candidate_summary":
                result.conversation_summary,

            "conversation_summary":
                result.conversation_summary,
        }

    
    def update_candidate_model(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        topic = state.get("current_topic")

        if not topic:
            return state

        profile = dict(
            state.get(
                "skill_profile",
                {},
            )
        )

        existing = dict(
            profile.get(
                topic,
                {
                    "score": 3.0,
                    "confidence": 0.0,
                    "attempts": 0,
                    "strong_concepts": [],
                    "weak_concepts": [],
                },
            )
        )

        attempts = existing["attempts"]

        # --------------------------------
        # Get latest analysis
        # --------------------------------

        analysis = state.get(
            "latest_analysis",
            {},
        )

        reasoning_score = analysis.get(
            "reasoning_score",
            3,
        )

        technical_score = analysis.get(
            "technical_score",
            3,
        )

        confidence = analysis.get(
            "confidence",
            0.5,
        )

        # --------------------------------
        # Combined score
        # --------------------------------

        new_score = (
            reasoning_score * 0.5
            +
            technical_score * 0.5
        )

        # --------------------------------
        # Moving average
        # --------------------------------

        old_score = existing["score"]

        if attempts == 0:

            updated_score = new_score

        else:

            # Recent evidence gets slightly
            # more weight.
            updated_score = (
                old_score * 0.7
                +
                new_score * 0.3
            )

        # --------------------------------
        # Confidence
        # --------------------------------

        old_confidence = existing[
            "confidence"
        ]

        updated_confidence = min(
            1.0,
            (
                old_confidence * 0.7
                +
                confidence * 0.3
            ),
        )

        # --------------------------------
        # Concepts
        # --------------------------------

        strong_concepts = list(
            existing.get(
                "strong_concepts",
                [],
            )
        )

        weak_concepts = list(
            existing.get(
                "weak_concepts",
                [],
            )
        )

        for concept in analysis.get(
            "strong_concepts",
            [],
        ):

            if concept not in strong_concepts:
                strong_concepts.append(
                    concept
                )

        for concept in analysis.get(
            "missing_concepts",
            [],
        ):

            if concept not in weak_concepts:
                weak_concepts.append(
                    concept
                )

        # --------------------------------
        # Save
        # --------------------------------

        profile[topic] = {

            "score": round(
                updated_score,
                2,
            ),

            "confidence": round(
                updated_confidence,
                2,
            ),

            "attempts": attempts + 1,

            "strong_concepts":
                strong_concepts,

            "weak_concepts":
                weak_concepts,
        }

        return {
            **state,
            "skill_profile": profile,
        }


    
    def analyze_architecture(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        architecture = (
            context.get("architecture")
            or {}
        )

        # For the first implementation,
        # preserve the architecture in the context.
        #
        # Later this node can return:
        #
        # architecture_issues
        # missing_components
        # bottlenecks
        # single_points_of_failure
        # architecture_strengths

        return {
            **state,
        }


    def interview_controller(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                INTERVIEW_CONTROLLER_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Interview phase:

                {phase}

                Current topic:

                {topic}

                Candidate skill profile:

                {skills}

                Requirements covered:

                {requirements}

                Candidate weaknesses:

                {weaknesses}

                Candidate decisions:

                {decisions}

                Questions already asked:

                {questions}

                Architecture:

                {architecture}

                Candidate latest message:

                {message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            phase=state["interview_phase"],
            topic=state["current_topic"],
            skills=json.dumps(
                state.get(
                    "skill_profile",
                    {},
                ),
                indent=2,
            ),
            requirements=json.dumps(
                state.get(
                    "requirements_covered",
                    [],
                ),
                indent=2,
            ),
            weaknesses=json.dumps(
                state.get(
                    "candidate_weaknesses",
                    [],
                ),
                indent=2,
            ),
            decisions=json.dumps(
                state.get(
                    "candidate_decisions",
                    [],
                ),
                indent=2,
            ),
            questions=json.dumps(
                state.get(
                    "questions_asked",
                    [],
                ),
                indent=2,
            ),
            architecture=json.dumps(
                context.get(
                    "architecture"
                ) or {},
                indent=2,
            ),
            message=runtime.context.user_message,
        )

        result = self.controller_llm.invoke(
            messages
        )

        return {
            **state,

            "next_decision":
                result.decision,

            "current_action":
                result.action,

            "current_topic":
                result.topic,

            "current_objective":
                result.objective,

            "interview_phase":
                result.next_phase
                if result.next_phase
                else state["interview_phase"],
        }


    def route_controller(
        self,
        state: TutorState,
    ) -> str:

        decision = state["next_decision"]

        if decision == "CLARIFICATION":
            return "clarification"

        if decision == "REQUIREMENT_GATHERING":
            return "requirement"

        if decision == "MOVE_PHASE":
            return "move_phase"

        if decision == "END_INTERVIEW":
            return "evaluate"

        return "question"


    def update_phase(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        return {
            **state,
            "current_topic": state["interview_phase"],
        }


    def question_planner(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                QUESTION_PLANNER_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Phase:

                {phase}

                Topic:

                {topic}

                Action:

                {action}

                Objective:

                {objective}

                Candidate skill:

                {skills}

                Candidate weaknesses:

                {weaknesses}

                Previously asked questions:

                {questions}

                Architecture:

                {architecture}

                Previous planner attempt:

                {previous_attempt}

                Previous reviewer feedback:

                {review_feedback}

                Create ONE question.
                """,
            ),
        ])

        previous_attempt = {}

        candidates = state.get(
            "question_candidates",
            [],
        )

        if candidates:
            previous_attempt = candidates[-1]

        difficulty = (
            self.difficulty_controller.calculate(
                state=state,
                topic=state["current_topic"],
                question_type=state[
                    "current_question_type"
                ],
            )
        )

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            difficulty=difficulty,
            phase=state["interview_phase"],
            topic=state["current_topic"],
            action=state["current_action"],
            objective=state["current_objective"],
            skills=json.dumps(
                state.get(
                    "skill_profile",
                    {},
                ),
                indent=2,
            ),
            weaknesses=json.dumps(
                state.get(
                    "candidate_weaknesses",
                    [],
                ),
                indent=2,
            ),
            questions=json.dumps(
                state.get(
                    "questions_asked",
                    [],
                ),
                indent=2,
            ),
            architecture=json.dumps(
                context.get(
                    "architecture"
                ) or {},
                indent=2,
            ),
            previous_attempt=json.dumps(
                previous_attempt,
                indent=2,
            ),
            review_feedback=state.get(
                "question_review_feedback",
                "",
            ),
        )

        result = self.question_planner_llm.invoke(
            messages
        )

        candidates = list(
            state.get(
                "question_candidates",
                [],
            )
        )

        candidates.append({
            "question": result.question,
            "question_type": result.question_type,
            "topic": result.topic,
            "concept": result.concept,
            "objective": result.objective,
            "difficulty": result.difficulty,
            "reason": result.reason,
            "attempt": (
                state.get(
                    "question_retry_count",
                    0,
                ) + 1
            ),
        })


        return {
            **state,

            "current_difficulty": difficulty,

            "current_question_type":
                result.question_type,

            "current_topic":
                result.topic,

            "current_objective":
                result.objective,

            "current_difficulty":
                result.difficulty,

            "question_candidates":
                candidates,

            "question_retry_count":
                state.get(
                    "question_retry_count",
                    0,
                ) + 1,
        }


    def question_reviewer(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        candidates = state.get(
            "question_candidates",
            [],
        )

        current_question = candidates[-1]

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                QUESTION_REVIEW_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Candidate architecture:

                {architecture}

                Candidate weaknesses:

                {weaknesses}

                Previously asked questions:

                {questions}

                Intended objective:

                {objective}

                Intended difficulty:

                {difficulty}

                Proposed question:

                {question}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            architecture=json.dumps(
                context.get(
                    "architecture"
                ) or {},
                indent=2,
            ),
            weaknesses=json.dumps(
                state.get(
                    "candidate_weaknesses",
                    [],
                ),
                indent=2,
            ),
            questions=json.dumps(
                state.get(
                    "questions_asked",
                    [],
                ),
                indent=2,
            ),
            objective=state[
                "current_objective"
            ],
            difficulty=state[
                "current_difficulty"
            ],
            question=current_question[
                "question"
            ],
        )

        result = self.question_review_llm.invoke(
            messages
        )

        candidates[-1]["review"] = {
            "score": result.score,
            "feedback": result.feedback,
            "relevant": result.relevant,
            "tests_target_concept":
                result.tests_target_concept,
            "appropriate_difficulty":
                result.appropriate_difficulty,
            "not_duplicate":
                result.not_duplicate,
            "does_not_reveal_solution":
                result.does_not_reveal_solution,
            "single_question":
                result.single_question,
        }

        return {
            **state,

            "question_candidates":
                candidates,

            "question_review_feedback":
                result.feedback,
        }


    def route_question_review(
        self,
        state: TutorState,
    ) -> str:

        candidates = state.get(
            "question_candidates",
            [],
        )

        if not candidates:
            return "retry"

        latest = candidates[-1]

        review = latest.get(
            "review",
            {},
        )

        score = review.get(
            "score",
            0,
        )

        # Good enough → stop immediately
        if score >= 0.75:
            return "accept"

        # Maximum 3 attempts reached
        if (
            state.get(
                "question_retry_count",
                0,
            )
            >= self.MAX_QUESTION_RETRIES
        ):
            return "select_best"

        return "retry"


    def select_best_question(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        candidates = state.get(
            "question_candidates",
            [],
        )

        if not candidates:
            return state

        best = max(
            candidates,
            key=lambda candidate: (
                candidate
                .get("review", {})
                .get("score", 0)
            ),
        )

        return {
            **state,

            "selected_question":
                best["question"],

            "current_question_type":
                best["question_type"],

            "current_topic":
                best["topic"],

            "current_objective":
                best["objective"],

            "current_difficulty":
                best["difficulty"],
        }


    def response_generator(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        question = (
            state.get(
                "selected_question"
            )
        )

        if not question:

            candidates = state.get(
                "question_candidates",
                [],
            )

            if candidates:
                question = candidates[-1][
                    "question"
                ]

        if not question:
            raise ValueError(
                "No question selected"
            )

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                TUTOR_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Generate the interviewer response.

                The intended question is:

                {question}

                Topic:

                {topic}

                Action:

                {action}

                Difficulty:

                {difficulty}

                Candidate architecture:

                {architecture}

                Output the question naturally.

                Ask only ONE question.
                """,
            ),
        ])

        messages = prompt.format_messages(
            question=question,
            topic=state[
                "current_topic"
            ],
            action=state[
                "current_action"
            ],
            difficulty=state[
                "current_difficulty"
            ],
            architecture=json.dumps(
                context.get(
                    "architecture"
                ) or {},
                indent=2,
            ),
        )

        result = self.response_llm.invoke(
            messages
        )

        return {
            **state,

            "tutor_response":
                result.response,

            "conversation_summary":
                result.conversation_summary,
        }



    def clarification_node(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an HLD interviewer.

                Answer the candidate's clarification
                using ONLY the problem definition.

                Never invent requirements.

                If the problem intentionally leaves
                something unspecified, tell the candidate
                to make an explicit assumption.
                """,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Candidate:

                {message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            message=runtime.context.user_message,
        )

        result = self.response_llm.invoke(
            messages
        )

        return {
            **state,

            "tutor_response":
                result.response,

            "conversation_summary":
                result.conversation_summary,
        }
    

    def requirement_node(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an HLD interviewer.

                The candidate is gathering requirements.

                Answer based on the provided problem.

                Do not invent requirements.
                """,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Requirements covered:

                {requirements}

                Candidate question:

                {message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            requirements=json.dumps(
                state.get(
                    "requirements_covered",
                    [],
                ),
                indent=2,
            ),
            message=runtime.context.user_message,
        )

        result = self.response_llm.invoke(
            messages
        )

        return {
            **state,

            "tutor_response":
                result.response,

            "conversation_summary":
                result.conversation_summary,
        }
    

    def update_evidence(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        questions = list(
            state.get(
                "questions_asked",
                [],
            )
        )

        evidence = list(
            state.get(
                "evidence",
                [],
            )
        )

        response = state.get(
            "tutor_response",
            "",
        )

        if response:

            questions.append({
                "question": response,
                "topic": state.get(
                    "current_topic"
                ),
                "action": state.get(
                    "current_action"
                ),
                "question_type":
                    state.get(
                        "current_question_type"
                    ),
                "difficulty":
                    state.get(
                        "current_difficulty"
                    ),
            })

            evidence.append({
                "candidate_message":
                    runtime.context.user_message,

                "interviewer_response":
                    response,

                "topic":
                    state.get(
                        "current_topic"
                    ),

                "action":
                    state.get(
                        "current_action"
                    ),

                "difficulty":
                    state.get(
                        "current_difficulty"
                    ),
            })

        return {
            **state,

            "questions_asked":
                questions,

            "evidence":
                evidence,

            "questions_asked_count":
                len(questions),

            # Reset the bounded question loop
            "question_retry_count": 0,

            "question_candidates": [],

            "question_review_feedback": "",

            "selected_question": "",
        }


    def evaluate(
        self,
        state: TutorState,
        runtime: Runtime[TutorRuntimeContext],
    ) -> TutorState:

        context = self.context_builder.build(
            session_id=runtime.context.session_id,
            state=state,
            user_message=runtime.context.user_message,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Evaluate this HLD interview.

                Use observed evidence.

                Do not invent candidate behavior.

                Evaluate:

                - Requirements
                - Capacity planning
                - Architecture
                - Database
                - Caching
                - Scalability
                - Reliability
                - Tradeoffs
                - Communication
                """,
            ),
            (
                "human",
                """
                Problem:

                {problem}

                Architecture:

                {architecture}

                Candidate skill profile:

                {skills}

                Interview evidence:

                {evidence}

                Candidate weaknesses:

                {weaknesses}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            architecture=json.dumps(
                context.get(
                    "architecture"
                ) or {},
                indent=2,
            ),
            skills=json.dumps(
                state.get(
                    "skill_profile",
                    {},
                ),
                indent=2,
            ),
            evidence=json.dumps(
                state.get(
                    "evidence",
                    [],
                ),
                indent=2,
            ),
            weaknesses=json.dumps(
                state.get(
                    "candidate_weaknesses",
                    [],
                ),
                indent=2,
            ),
        )

        result = self.response_llm.invoke(
            messages
        )

        return {
            **state,

            "interview_status":
                "COMPLETED",

            "evaluation": {
                "summary":
                    result.conversation_summary,

                "response":
                    result.response,
            },

            "tutor_response":
                result.response,
        }


    def invoke(
        self,
        session_id: str,
        user_message: str,
        problem_id: str | None = None,
    ):

        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        existing_state = (
            self.graph.get_state(
                config
            )
        )

        if not existing_state.values:

            if problem_id is None:
                raise ValueError(
                    "problem_id is required "
                    "for a new session"
                )

            input_state = {

                "problem_id":
                    problem_id,

                "interview_phase":
                    "REQUIREMENTS",

                "interview_status":
                    "ACTIVE",

                "next_decision":
                    "ASK_QUESTION",

                "current_action":
                    "REQUIREMENT_GATHERING",

                "current_topic":
                    "REQUIREMENTS",

                "current_objective":
                    "Understand the problem requirements",

                "current_question_type":
                    "",

                "current_difficulty":
                    2,

                "selected_question":
                    "",

                "question_retry_count":
                    0,

                "question_candidates":
                    [],

                "candidate_summary":
                    "",

                "candidate_decisions":
                    [],

                "candidate_assumptions":
                    [],

                "candidate_strengths":
                    [],

                "candidate_weaknesses":
                    [],

                "requirements_covered":
                    [],

                "requirements_remaining":
                    [],

                "skill_profile":
                    {},

                "questions_asked":
                    [],

                "evidence":
                    [],

                "hints_used":
                    0,

                "questions_asked_count":
                    0,

                "conversation_summary":
                    "",

                "tutor_response":
                    "",

                "evaluation":
                    None,
            }

        else:

            input_state = {}

        return self.graph.invoke(
            input_state,

            config=config,

            context=TutorRuntimeContext(
                session_id=session_id,
                user_message=user_message,
            ),
        )