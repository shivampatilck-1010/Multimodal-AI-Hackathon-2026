"""Top-level Tutor Service."""

import json
import logging
from typing import Dict, Any

from app.config import get_settings
from app.tutor.models import TutorAnswer, Citation
from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.retriever import Retriever
from app.tutor.grounding import EvidenceGate
from app.tutor.providers.llm import LLMProvider
from app.tutor.memory import ConversationMemory
from app.tutor.query_rewriter import rewrite_query
from app.tutor.citations import CitationValidator
from app.tutor.prompts import TUTOR_SYSTEM_PROMPT, TUTOR_RESPONSE_SCHEMA, format_evidence, label_for

logger = logging.getLogger(__name__)

class TutorService:
    def __init__(
        self,
        llm: LLMProvider,
        kb: KnowledgeBase,
    ) -> None:
        self.llm = llm
        self.kb = kb
        self.retriever = Retriever(kb.store, kb.embedder)
        self.validator = CitationValidator(link_template="/courses/{course_id}/sources/{source_id}")
        
        settings = get_settings()
        min_score = settings.grounding_min_score
        if min_score is None:
            min_score = kb.embedder.default_min_score
            
        self.gate = EvidenceGate(min_score=min_score, min_chunks=settings.grounding_min_chunks)
        self.sessions: Dict[str, ConversationMemory] = {}

    def get_memory(self, session_id: str) -> ConversationMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory()
        return self.sessions[session_id]

    def ask(
        self, 
        session_id: str, 
        query: str, 
        level: str = "intermediate",
        course_id: str = "hackathon_course"
    ) -> TutorAnswer:
        memory = self.get_memory(session_id)
        history = memory.get_history()
        
        # 1. Rewrite query if there is history
        standalone_query = rewrite_query(self.llm, query, history)
        logger.info(f"Original: {query} -> Rewritten: {standalone_query}")
        
        # 2. Retrieve
        chunks = self.retriever.retrieve(course_id=course_id, query=standalone_query, top_k=5)
        
        # 3. Grounding evaluation
        decision = self.gate.evaluate(standalone_query, chunks)
        if not decision.sufficient:
            # Ungrounded
            ans = TutorAnswer(
                grounded=False,
                answer="I couldn't find enough information about this in the uploaded course material.",
                citations=[],
                debug_trace={"grounding_decision": decision.reason}
            )
            # Add to memory
            memory.add_user_message(query)
            memory.add_assistant_message(ans.answer)
            return ans

        # 4. Generate answer
        system_prompt = TUTOR_SYSTEM_PROMPT
        context_block = format_evidence(decision.evidence)
        labels_map = {label_for(i): chunk for i, chunk in enumerate(decision.evidence)}
        
        user_prompt = f"STANDALONE QUESTION: {standalone_query}\nEXPLANATION LEVEL: {level}"
        
        try:
            response_text = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context_block,
                conversation_history=history,
                response_schema=TUTOR_RESPONSE_SCHEMA,
                temperature=0.0
            )
            data = json.loads(response_text)
            
            grounded_flag = data.get("grounded", False)
            
            if not grounded_flag:
                ans = TutorAnswer(
                    grounded=False,
                    answer="I couldn't find enough information about this in the uploaded course material.",
                    citations=[],
                    debug_trace={"grounded_flag": False}
                )
            else:
                val_result = self.validator.validate(
                    course_id=course_id,
                    model_output=data,
                    evidence=labels_map
                )
                
                if val_result.answer == "": # Means not grounded due to no citations after validation
                    ans = TutorAnswer(
                        grounded=False,
                        answer="I couldn't find enough information about this in the uploaded course material.",
                        citations=[],
                        debug_trace={"validation": "all citations stripped"}
                    )
                else:
                    ans = TutorAnswer(
                        grounded=True,
                        answer=val_result.answer,
                        citations=val_result.citations,
                        debug_trace={"raw_labels": data.get("cited_sources")}
                    )
                
            memory.add_user_message(query)
            memory.add_assistant_message(ans.answer)
            return ans
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
