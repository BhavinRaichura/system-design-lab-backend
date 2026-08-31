PROMPT = """
                You are analyzing a candidate during a
                system design interview.

                Determine what happened in the candidate's
                latest message.

                You must:

                1. Identify the main topic.
                2. Identify new requirements discussed.
                3. Identify architectural decisions made.
                4. Identify weaknesses in the candidate's reasoning.
                5. Decide what the interviewer should do next.

                Action meanings:

                FOLLOW_UP:
                The candidate gave a reasonable answer but
                more information is needed.

                CHALLENGE:
                The candidate made a questionable decision
                or missed an important trade-off.

                HINT:
                The candidate appears stuck and needs guidance.

                CLARIFICATION:
                The candidate is asking the interviewer
                to clarify an ambiguous requirement.

                REQUIREMENT_GATHERING:
                The candidate is asking questions to discover
                requirements or scope.

                EVALUATE:
                The current interview section is sufficiently
                explored and should be evaluated.

                Do not generate the interviewer response.
                Only analyze the candidate's turn.

                Problem:
                {problem}

                Architecture:
                {architecture}

                Current interview phase:
                {interview_phase}

                Current topic:
                {current_topic}

                Previous summary:
                {conversation_summary}

                Requirements already covered:
                {requirements_covered}

                Candidate decisions:
                {candidate_decisions}

                Candidate weaknesses:
                {candidate_weaknesses}

                Candidate's latest message:
                {user_message}
                """