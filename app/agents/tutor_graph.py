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
    TutorAnalysisSchema,
)
from app.clients import llm
from app.agents.context_builder import TutorContextBuilder

class TutorState(TypedDict):
    problem_id: str

    last_action: str
    current_topic: str
    interview_phase: str

    conversation_summary: str

    requirements_covered: list[str]
    candidate_decisions: list[str]
    candidate_weaknesses: list[str]

    hints_used: int


# use to pass at the time of invocation
# class TutorInput(TypedDict):
#     user_message: str

# use at the run time 
@dataclass
class TutorRuntimeContext:
    session_id: str
    user_message: str


class TutorGraph:

    def __init__(self):
        self.structured_llm = (
            llm.with_structured_output(
                TutorResponseSchema
            )
        )

        self.analysis_llm = (
            llm.with_structured_output(
                TutorAnalysisSchema
            )
        )

        self.context_builder = TutorContextBuilder()

        self.checkpointer = InMemorySaver()

        self.graph = self._builder()


    def _builder(self):

        graph = StateGraph(
            state_schema=TutorState,
            # input_schema=TutorInput,
            output_schema=TutorState,
            context_schema=TutorRuntimeContext,
        )

        graph.add_node(
            "analyze_candidate",
            self.analyze_candidate,
        )
        graph.add_node(
            "tutor_node",
            self.tutor_node,
        )

        graph.add_edge(
            START,
            "analyze_candidate",
        )

        graph.add_edge(
            "analyze_candidate",
            "tutor_node"
        )

        graph.add_edge(
            "tutor_node",
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
            ("system", ANALYZE_CANDIDATE_SYSTEM_PROMPT),
            (
                "human",
                """
                Candidate's latest message:

                {user_message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=json.dumps(
                context["problem"],
                indent=2,
            ),
            architecture=json.dumps(
                context.get("architecture"),
                indent=2,
            ),
            interview_phase=context["interview_phase"],
            current_topic=context["current_topic"],
            conversation_summary=context["conversation_summary"],
            requirements_covered=context["requirements_covered"],
            candidate_decisions=context["candidate_decisions"],
            candidate_weaknesses=context["candidate_weaknesses"],
            user_message=context["user_message"],
        )

        result = self.analysis_llm.invoke(messages)

        return {
            **state,

            "last_action": result.action,
            "current_topic": result.topic,

            "conversation_summary": (
                result.conversation_summary
            ),

            "requirements_covered": self._merge_unique(
                state["requirements_covered"],
                result.requirements_covered,
            ),

            "candidate_decisions": self._merge_unique(
                state["candidate_decisions"],
                result.candidate_decisions,
            ),

            "candidate_weaknesses": self._merge_unique(
                state["candidate_weaknesses"],
                result.candidate_weaknesses,
            ),
        }

    
    def tutor_node(
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
                TUTOR_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Candidate's latest message:

                {user_message}

                The candidate analysis determined:

                Action:
                {action}

                Topic:
                {topic}

                Generate the interviewer response.
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
            interview_phase=context["interview_phase"],
            current_topic=context["current_topic"],
            conversation_summary=context["conversation_summary"],
            requirements_covered=context["requirements_covered"],
            candidate_decisions=context["candidate_decisions"],
            candidate_weaknesses=context["candidate_weaknesses"],
            hints_used=context["hints_used"],
            user_message=runtime.context.user_message,
            action=state["last_action"],
            topic=state["current_topic"],
        )

        result = self.structured_llm.invoke(messages)

        return {
            **state,

            # Whatever response fields your
            # TutorResponseSchema contains
            "current_topic": result.topic,

            "conversation_summary": result.conversation_summary,

            "requirements_covered": self._merge_unique(
                state["requirements_covered"],
                result.requirements_covered,
            ),

            "candidate_decisions": self._merge_unique(
                state["candidate_decisions"],
                result.candidate_decisions,
            ),

            "candidate_weaknesses": self._merge_unique(
                state["candidate_weaknesses"],
                result.candidate_weaknesses,
            ),
        }
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

        existing_state = self.graph.get_state(config)

        if not existing_state.values:

            if problem_id is None:
                raise ValueError(
                    "problem_id is required for a new session"
                )

            input_state = {
                "problem_id": problem_id,
                "current_topic": "REQUIREMENTS",
                "interview_phase": "REQUIREMENTS",
                "conversation_summary": "",
                "requirements_covered": [],
                "candidate_decisions": [],
                "candidate_weaknesses": [],
                "hints_used": 0,
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

    
tutor = TutorGraph()