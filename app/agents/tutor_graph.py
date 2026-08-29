import json
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.schemas.tutor import TutorResponseSchema
from app.clients import llm

class TutorState(TypedDict):
    problem_id: str

    problem: str
    architecture: dict
    user_message: str

    current_topic: str
    interview_phase: str

    conversation_summary: str

    requirements_covered: list[str]
    candidate_decisions: list[str]
    candidate_weaknesses: list[str]

    hints_used: int

    response: str
    action: str
    topic: str


class TutorGraph:

    def __init__(self):
        self.structured_llm = (
            llm.with_structured_output(
                TutorResponseSchema
            )
        )

        self.checkpointer = InMemorySaver()

        self.graph = self._builder()


    def _builder(self):

        graph = StateGraph(TutorState)

        graph.add_node(
            "tutor_node",
            self.tutor_node,
        )

        graph.add_edge(
            START,
            "tutor_node",
        )

        graph.add_edge(
            "tutor_node",
            END,
        )

        return graph.compile(
            checkpointer=self.checkpointer
        )
    

    def tutor_node(
        self,
        state: TutorState,
    ) -> TutorState:

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an experienced system design interviewer.

                Your job is to conduct a realistic system design
                interview.

                Rules:

                1. Do not immediately provide the complete solution.
                2. Challenge the candidate's architectural decisions.
                3. Ask follow-up questions when more information is needed.
                4. Give a hint when the candidate is stuck.
                5. Identify weaknesses in the candidate's design.
                6. Track what topics and requirements have already
                been discussed.
                7. Avoid repeatedly asking questions that have already
                been answered.
                8. Consider the previous interview context before
                responding.

                Interview problem:
                {problem}

                Current architecture:
                {architecture}

                Interview phase:
                {interview_phase}

                Current topic:
                {current_topic}

                Conversation summary:
                {conversation_summary}

                Requirements already covered:
                {requirements_covered}

                Candidate decisions so far:
                {candidate_decisions}

                Candidate weaknesses identified so far:
                {candidate_weaknesses}

                Hints already used:
                {hints_used}
                """,
            ),
            (
                "human",
                """
                Candidate's latest message:

                {user_message}
                """,
            ),
        ])

        messages = prompt.format_messages(
            problem=state["problem"],
            architecture=json.dumps(
                state["architecture"],
                indent=2,
            ),
            interview_phase=state["interview_phase"],
            current_topic=state["current_topic"],
            conversation_summary=state["conversation_summary"],
            requirements_covered=state["requirements_covered"],
            candidate_decisions=state["candidate_decisions"],
            candidate_weaknesses=state["candidate_weaknesses"],
            hints_used=state["hints_used"],
            user_message=state["user_message"],
        )

        result = self.structured_llm.invoke(messages)

        return {
            **state,
            "response": result.response,
            "action": result.action,
            "topic": result.topic,
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
        state: TutorState,
    ):

        config = {
            "configurable": {
                "thread_id": session_id
            }
        }

        return self.graph.invoke(
            state,
            config=config,
        )

tutor = TutorGraph()