"""
Agentic architecture for the Telegram bot using Langgraph.
This module defines specialized agents for different tasks.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
import logging

from src.llm_factory import get_llm_client
from rag import ans_retriever
from src.tavily_search import TavilyWebSearch
from config import config

logger = logging.getLogger(__name__)


class AgentConfig:
    """Configuration for agents."""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.web_search = TavilyWebSearch(api_key=config.TAVILY_API_KEY, max_results=3)


# Create agent configuration
agent_config = AgentConfig()


class RAGAgent:
    """
    Retrieval-Augmented Generation (RAG) Agent
    Specialized for legal document retrieval.
    """
    
    def __init__(self):
        self.name = "RAG Agent"
        
    async def retrieve_documents(self, query: str) -> str:
        """
        Only retrieve relevant documents without generating an answer yet.
        This saves one LLM call compared to the original version.
        """
        try:
            # Retrieve relevant documents
            docs = ans_retriever.invoke(query)
            
            if not docs:
                logger.info(f"RAG Retrieval: No documents found for query: '{query}'")
                return "No relevant legal documents found."
            
            logger.info(f"RAG Retrieval: Found {len(docs)} documents for query: '{query}'")
            
            # Format documents for context
            context = "\n\n### Related Legal Documents:\n"
            for i, doc in enumerate(docs, 1):
                # Log a snippet of the retrieved content
                content_snippet = doc.page_content[:200].replace('\n', ' ')
                logger.info(f"Retrieved Doc {i}: {content_snippet}...")
                
                # Use a smaller snippet to speed up the final context processing
                content = doc.page_content[:800]
                context += f"\n{i}. {content}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"RAG Agent retrieval error: {e}")
            return f"Error retrieving legal information: {str(e)}"


class WebSearchAgent:
    """
    Web Search Agent
    Specialized for retrieving up-to-date information from the web.
    """
    def __init__(self):
        self.name = "Web Search Agent"
        
    async def search_and_summarize(self, query: str) -> str:
        try:
            results = await agent_config.web_search.get_search_summary(query)
            return results if results else "No relevant web results found."
        except Exception as e:
            logger.error(f"Web Search Agent error: {e}")
            return f"Web search failed: {str(e)}"


class MemoryAgent:
    """
    Memory Agent
    Manages conversation history and context.
    """
    def __init__(self):
        self.name = "Memory Agent"
        
    async def summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        try:
            # Generate summary quickly for deployment
            prompt = f"Summarize concisely in Korean: {messages}"
            response = ""
            async for chunk in agent_config.llm_client.chat_stream(prompt):
                response += chunk
            return response
        except Exception as e:
            logger.error(f"Memory Agent error: {e}")
            return "Summary failed."


class JudgingAgent:
    """
    Judging Agent with optimized flow decision and confidence assessment.
    """
    def __init__(self):
        self.name = "Judging Agent"
        self.system_prompt = f"""
        You are an orchestration assistant for a {config.ROLE} bot.
        Assign agents: ["RAG"] (for specialized knowledge base), ["WebSearch"] (for current news or general info), or both.
        """

    def fast_route(self, query: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower().strip()
        # Only fast track very simple greetings AND if the query is short
        # Long queries containing greetings are likely legal questions with polite prefixes
        if len(query_lower) < 20 and any(greet in query_lower for greet in ['hello', 'hi', 'greetings', '안녕', '안녕하세요']):
            return {"agents": [], "reasoning": "Heuristic: Simple short greeting"}
        
        # If any "news" or "current" keywords are present, let LLM decide
        if any(now in query_lower for now in ['news', 'recent', 'today', 'latest', 'current', 'update']):
            return None
            
        return None

    async def determine_agent_flow(self, query: str, conversation_context: str = "") -> Dict[str, Any]:
        fast_result = self.fast_route(query)
        if fast_result: 
            logger.info(f"JudgingAgent: Fast-routed: {fast_result['reasoning']}")
            return fast_result
        try:
            logger.info(f"JudgingAgent: Asking LLM for agent flow for query: '{query[:50]}...'")
            prompt = f"Query: {query}\nAgents needed?"
            response = await agent_config.llm_client.chat([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ])
            logger.info(f"JudgingAgent: LLM Response for flow: '{response.strip()}'")
            agents = []
            if "RAG" in response.upper(): agents.append("RAG")
            if "WEBSEARCH" in response.upper(): agents.append("WebSearch")
            
            final_agents = agents if agents else ["RAG", "WebSearch"]
            logger.info(f"JudgingAgent: Final decided agents: {final_agents}")
            return {"agents": final_agents}
        except Exception as e:
            logger.error(f"JudgingAgent error in determination: {e}")
            return {"agents": ["RAG", "WebSearch"]}
            
    async def extract_history_context(self, context: str) -> str:
        """
        Extract key facts, entities, and goals from conversation history.
        """
        if not context or context == "No previous context":
            return ""
            
        try:
            logger.info("JudgingAgent: Extracting key context from history...")
            import asyncio
            prompt = f"""
            Analyze the following conversation history between a user and a {config.ROLE}.
            Extract the most important context needed to understand future questions accurately.
            
            Focus on:
            1. Key entities (people, locations, specific tax forms, laws)
            2. Dates and years mentioned
            3. The user's specific situation or goal
            4. Any constraints or preferences stated by the user
            
            [Conversation History]
            {context}
            
            Output ONLY a concise bulleted list of these key facts in {config.LANGUAGE}.
            If no important context is found, output "No significant context found."
            Do not include any introductory or concluding text.
            """
            
            extraction = ""
            async with asyncio.timeout(60):
                async for chunk in agent_config.llm_client.chat_stream(prompt):
                    extraction += chunk
            
            extraction = extraction.strip()
            logger.info(f"JudgingAgent: Extracted context length: {len(extraction)}")
            return extraction
        except Exception as e:
            logger.error(f"JudgingAgent: Context extraction failed: {e}")
            return ""

    async def analyze_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Step 1 of Two-Step RAG: Use RAG to understand the context of the question correctly.
        """
        try:
            # Step 1a: Extract explicit context from history
            extracted_context = await self.extract_history_context(context)
            
            # Step 1b: Generate an augmented query for better retrieval
            # This makes the query longer and more "verbal" to improve vector match
            logger.info(f"JudgingAgent: Augmenting query: '{query}'")
            augmentation_prompt = f"""
            As a {config.ROLE}, augment the user's question into a more descriptive, verbal, and search-friendly query for a legal/accounting database.
            
            [Relevant Facts from History]
            {extracted_context if extracted_context else "No specific context extracted."}
            
            [Conversation History (Reference)]
            {context if context else "No previous context"}
            
            [User Question]
            {query}
            
            CRITICAL: Use the extracted facts to resolve any ambiguities or pronouns in the user's question. 
            Ensure the augmented query is self-contained and captures the user's full intent as implied by the history.
            
            Output ONLY the augmented query in {config.LANGUAGE}. 
            The output should be a detailed natural language sentence that describes what is being asked in a way that is easy to match against legal documents.
            Do not include any headers or introductory text.
            """
            
            augmented_query = ""
            import asyncio
            try:
                async with asyncio.timeout(90):
                    async for chunk in agent_config.llm_client.chat_stream(augmentation_prompt):
                        augmented_query += chunk
            except asyncio.TimeoutError:
                logger.warning("JudgingAgent: Query augmentation timed out, using original query.")
                augmented_query = query
            
            augmented_query = augmented_query.strip()
            if not augmented_query:
                logger.warning("JudgingAgent: Augmentation returned empty string, using original query.")
                augmented_query = query
            
            logger.info(f"JudgingAgent: Augmented query: '{augmented_query}'")

            # Step 1c: Use the augmented query to retrieve documents for further analysis
            logger.info(f"JudgingAgent: Analyzing query context using augmented query")
            context_docs = ans_retriever.invoke(augmented_query)
            
            doc_context = ""
            if context_docs:
                doc_context = "\n".join([doc.page_content[:500] for doc in context_docs[:3]])
            
            # Step 2: Refine the query based on retrieved context for the second RAG stage
            prompt = f"""
            As a {config.ROLE}, analyze the following user question and conversation history.
            Use the provided legal/accounting context to clarify or rephrase the question if it's ambiguous or uses specific terminology.
            
            [Target Regulations/Context]
            {doc_context}
            
            [Conversation History]
            {context}
            
            [User Question]
            {query}
            
            Output ONLY the clarified or rephrased question in {config.LANGUAGE}. 
            CRITICAL: Do not include any introductory phrases, apologies, or conversational filler like "The user is asking about..." or "Certainly, here is the clarified question:". 
            Your output should be the exact text to be used for retrieval.
            """
            
            analyzed_query = ""
            try:
                async with asyncio.timeout(90): # Use 90s for analysis
                    async for chunk in agent_config.llm_client.chat_stream(prompt):
                        analyzed_query += chunk
            except asyncio.TimeoutError:
                logger.warning("JudgingAgent: Analysis timed out, using original query.")
                analyzed_query = query
            
            analyzed_query = analyzed_query.strip()
            logger.info(f"JudgingAgent: Clarified query: '{analyzed_query}'")
            if not analyzed_query:
                logger.warning("JudgingAgent: Analysis returned empty string, using original query.")
                analyzed_query = query
            
            # Step 3: Judge the quality of the augmented query
            quality_judgment = await self.judge_augmentation_quality(
                original_query=query,
                augmented_query=augmented_query,
                context_docs=context_docs,
                conversation_context=context
            )
            
            return {
                "analyzed_query": analyzed_query,
                "context_docs": context_docs,
                "augmentation_quality": quality_judgment
            }
        except Exception as e:
            logger.error(f"JudgingAgent analysis error: {e}")
            return {"analyzed_query": query, "context_docs": [], "augmentation_quality": {"score": 50, "reasoning": "Error fallback"}}
    
    async def judge_augmentation_quality(self, original_query: str, augmented_query: str, context_docs: List[Any], conversation_context: str) -> Dict[str, Any]:
        """
        Judge the quality of query augmentation.
        
        Returns:
            Dictionary with quality score (0-100) and reasoning
        """
        try:
            # Create a prompt to evaluate the quality of the augmented query
            prompt = f"""
            Evaluate the quality of the following query augmentation for a {config.ROLE} assistant.
            
            Original Query: "{original_query}"
            Augmented Query: "{augmented_query}"
            
            Context from conversation: "{conversation_context[:200]}..."
            
            Context documents retrieved: {len(context_docs) if context_docs else 0} documents
            
            Rate the quality of this augmentation on a scale from 0 to 100:
            - 0-30: Poor quality - the augmented query is vague, missing key information, or doesn't improve retrieval
            - 31-60: Fair quality - the augmented query is somewhat improved but still lacks clarity or important details
            - 61-80: Good quality - the augmented query is significantly improved and captures the intent well
            - 81-100: Excellent quality - the augmented query is perfectly crafted and will yield highly relevant results
            
            Provide only a JSON response with:
            {{
                "score": N,  // integer between 0-100
                "reasoning": "explanation of why the score was given"
            }}
            
            Focus on:
            1. Whether the augmented query captures the user's intent clearly
            2. Whether it resolves ambiguities from the original query
            3. Whether it includes relevant context from the conversation
            4. Whether it's suitable for legal document retrieval
            """
            
            import asyncio
            try:
                async with asyncio.timeout(30):
                    response = await agent_config.llm_client.chat([
                        {"role": "system", "content": "You are a quality judge for query augmentation. Be strict but fair."},
                        {"role": "user", "content": prompt}
                    ])
            except asyncio.TimeoutError:
                logger.warning("JudgingAgent: Quality assessment timed out.")
                return {"score": 50, "reasoning": "Timeout fallback"}
            
            import json, re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {"score": data.get("score", 50), "reasoning": data.get("reasoning", "N/A")}
            return {"score": 50, "reasoning": "Default fallback"}
        except Exception as e:
            logger.error(f"JudgingAgent: Quality assessment failed: {e}")
            return {"score": 50, "reasoning": "Error fallback"}

    async def assess_confidence(self, query: str, answer: str, context: str = "") -> Dict[str, Any]:
        """Fast confidence assessment."""
        try:
            prompt = f"Query: {query}\nAnswer: {answer}\nRate confidence 0-100. Return only JSON: {{\"score\": N, \"reason\": \"str\"}}"
            import asyncio
            try:
                async with asyncio.timeout(15):
                    response = await agent_config.llm_client.chat([
                        {"role": "system", "content": "You are a quality judge. Be strict."},
                        {"role": "user", "content": prompt}
                    ])
            except asyncio.TimeoutError:
                logger.warning("JudgingAgent: Confidence assessment timed out.")
                return {"confidence_score": config.CONFIDENCE_THRESHOLD, "reasoning": "Timeout fallback"}
            import json, re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {"confidence_score": data.get("score", 70), "reasoning": data.get("reason", "N/A")}
            return {"confidence_score": config.CONFIDENCE_THRESHOLD, "reasoning": "Default high"}
        except Exception as e:
            logger.error(f"JudgingAgent: Confidence assessment failed: {e}")
            return {"confidence_score": config.CONFIDENCE_THRESHOLD, "reasoning": "Error fallback"}
    async def generate_supplement_questions(self, query: str, answer: str, confidence_assessment: Dict[str, Any]) -> List[str]:
        """Generate meaningful follow-up questions."""
        try:
            prompt = f"""The user asked: "{query}"
The current answer provided is: "{answer[:500]}..."
The confidence assessment for this answer is: {confidence_assessment.get('reasoning', 'N/A')}

As a {config.ROLE}, suggest 2 specific, short follow-up questions in {config.LANGUAGE} that would help you provide a more precise and accurate answer if the user provides more details.
Do NOT use placeholders. Return only a JSON list of strings.
Example: ["Could you clarify a specific detail?", "Are you asking about a particular standard?"]"""
            
            import asyncio
            try:
                async with asyncio.timeout(90):
                    response = await agent_config.llm_client.chat([
                        {"role": "system", "content": f"You are a helpful {config.ROLE}. Provide specific follow-up questions in a JSON list format."},
                        {"role": "user", "content": prompt}
                    ])
            except asyncio.TimeoutError:
                logger.warning("JudgingAgent: Supplement questions generation timed out.")
                if config.LANGUAGE == 'ko':
                    return ["질문에 대해 좀 더 자세히 설명해 주시겠습니까?", "제가 고려해야 할 구체적인 데이터가 있습니까?"]
                return ["Could you please elaborate on your question?", "Is there any specific data I should consider?"]
            import re, json
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
                return questions[:2] # Ensure only 2 questions
            
            if config.LANGUAGE == 'ko':
                return ["질문에 대해 좀 더 자세히 설명해 주시겠습니까?", "상황에 대한 구체적인 예시를 들어주실 수 있나요?"]
            return ["Could you provide more details about your specific situation?", "What is the primary goal of your inquiry?"]
        except Exception as e:
            logger.error(f"Error generating supplement questions: {e}")
            if config.LANGUAGE == 'ko':
                return ["질문에 대해 좀 더 자세히 설명해 주시겠습니까?", "어떤 구체적인 정보가 필요하신가요?"]
            return ["Could you please elaborate on your question?", "Is there any specific data I should consider?"]

    async def combine_results(self, query: str, rag_result: str, web_result: str, context: str = "") -> str:
        logger.info(f"JudgingAgent: Combining results for query: '{query[:50]}...'")
        prompt = f"""You are a {config.ROLE}. Based on the provided information, please provide an accurate and professional response to the user's latest question in {config.LANGUAGE}.

### [Conversation Context]
{context}

### [Reference Documents]
{rag_result}

### [Web Search Results]
{web_result}

---
### [User's Current Question]
{query}

Provide the most appropriate advice based on relevant regulations or standards. Cite specific regulations or sources where possible. If the information is not sufficiently covered in the provided materials, answer based on your professional knowledge while clearly stating the limitations of your advice.
FORMAT YOUR RESPONSE USING MARKDOWN:
- Use ### headers for sections
- Use **bold** for emphasis and important terms
- Use *italic* for technical terms and definitions
- Use - bullet points for lists
- Use `code` for code, technical terms, regulations, and specific references
- Use [links](url) for references when available"""
        response = ""
        chunk_count = 0
        import asyncio
        try:
            async with asyncio.timeout(90): # Use 90s for combining
                async for chunk in agent_config.llm_client.chat_stream(prompt):
                    response += chunk
                    chunk_count += 1
                    if chunk_count % 50 == 0:
                        logger.info(f"JudgingAgent: Still generating response... ({len(response)} chars)")
        except asyncio.TimeoutError:
            logger.error("JudgingAgent: Response generation timed out.")
            if response:
                response += "\n\n[Response truncated due to timeout]"
            else:
                response = "I'm sorry, I encountered a timeout while generating your response. Please try again or rephrase your question."
        
        logger.info(f"JudgingAgent: Response generation complete. Length: {len(response)} chars")
        return response

async def create_agent_graph():
    """Create optimized parallel graph."""
    from typing import TypedDict
    
    class State(TypedDict):
        query: str
        context: str
        analyzed_query: str
        context_docs: list
        agent_flow: list
        rag_result: str
        web_result: str
        final_response: str
        augmentation_quality: dict
        quality_low: bool  # Flag to indicate if we need clarification
        supplement_questions: list  # Store questions for the clarify node
    
    workflow = StateGraph(State)

    async def analyze_node(state: State) -> Dict[str, Any]:
        logger.info(f"--- Graph Node: ANALYZE ---")
        analysis = await judging_agent.analyze_query(state["query"], state["context"])
        return {
            "analyzed_query": analysis["analyzed_query"],
            "context_docs": analysis["context_docs"],
            "augmentation_quality": analysis["augmentation_quality"]
        }
    
    async def judge_augmentation_node(state: State) -> Dict[str, Any]:
        logger.info(f"--- Graph Node: JUDGE_AUGMENTATION ---")
        quality_score = state.get("augmentation_quality", {}).get("score", 50)
        logger.info(f"Augmentation quality score: {quality_score}")
        
        supplement_questions = []
        quality_low = False
        
        if quality_score < 60:
            logger.info(f"Low quality augmentation detected (score: {quality_score}), preparing to clarify")
            quality_low = True
            supplement_questions = await judging_agent.generate_supplement_questions(
                query=state["query"],
                answer="",
                confidence_assessment={"confidence_score": quality_score, "reasoning": "Low quality augmentation"}
            )
        else:
            logger.info(f"Augmentation quality is acceptable (score: {quality_score})")
        
        return {
            "supplement_questions": supplement_questions,
            "quality_low": quality_low
        }

    async def clarify_node(state: State) -> Dict[str, Any]:
        logger.info("--- Graph Node: CLARIFY ---")
        # Just return an empty response; the handler will append the warning and questions
        return {"final_response": ""}
    
    async def judge_node(state: State) -> Dict[str, Any]:
        logger.info(f"--- Graph Node: JUDGE (Query: '{state['analyzed_query']}') ---")
        judgment = await judging_agent.determine_agent_flow(state["analyzed_query"], state["context"])
        logger.info(f"Agent Flow selected: {judgment['agents']}")
        return {"agent_flow": judgment["agents"]}
    
    async def retrieval_node(state: State) -> Dict[str, Any]:
        logger.info("--- Graph Node: RETRIEVAL ---")
        import asyncio
        tasks = []
        
        # Determine RAG task
        if "RAG" in state["agent_flow"]:
            logger.info("Scheduling RAG retrieval")
            tasks.append(rag_agent.retrieve_documents(state["analyzed_query"]))
        else:
            async def dummy_rag(): return "N/A"
            tasks.append(dummy_rag())
            
        # Determine WebSearch task
        if "WebSearch" in state["agent_flow"]:
            logger.info("Scheduling WebSearch retrieval")
            tasks.append(web_search_agent.search_and_summarize(state["analyzed_query"]))
        else:
            async def dummy_web(): return "N/A"
            tasks.append(dummy_web())
            
        # Execute in parallel
        rag_res, web_res = await asyncio.gather(*tasks)
        return {"rag_result": rag_res, "web_result": web_res}
        
    async def combine_node(state: State) -> Dict[str, Any]:
        logger.info("--- Graph Node: COMBINE ---")
        response = await judging_agent.combine_results(
            state["analyzed_query"], 
            state.get("rag_result", "N/A"), 
            state.get("web_result", "N/A"),
            state["context"]
        )
        return {"final_response": response}

    workflow.add_node("analyze", analyze_node)
    workflow.add_node("judge_augmentation", judge_augmentation_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("combine", combine_node)
    workflow.add_node("clarify", clarify_node)
    
    # Entry to analyze
    workflow.set_entry_point("analyze")
    
    # Flow: analyze -> judge_augmentation
    workflow.add_edge("analyze", "judge_augmentation")
    
    # Conditional edge after judge_augmentation
    def decide_if_clarify(state: State) -> str:
        if state.get("quality_low", False):
            return "clarify"
        return "judge"
        
    workflow.add_conditional_edges(
        "judge_augmentation",
        decide_if_clarify,
        {
            "clarify": "clarify",
            "judge": "judge"
        }
    )
    
    # Remaining paths
    workflow.add_edge("judge", "retrieval")
    workflow.add_edge("retrieval", "combine")
    
    workflow.set_finish_point("combine")
    workflow.set_finish_point("clarify")
    return workflow.compile()


# Create and cache the agent graph
agent_graph = None


async def get_agent_graph():
    """
    Get the agent graph, creating it if necessary.
    
    Returns:
        Compiled agent graph
    """
    global agent_graph
    if agent_graph is None:
        agent_graph = await create_agent_graph()
    return agent_graph


async def run_agent_workflow(query: str, context: str = "") -> Dict[str, Any]:
    """
    Run the agent workflow for a given query.
    
    Args:
        query: User's question
        context: Conversation context
        
    Returns:
        Dictionary with results from the workflow
    """
    graph = await get_agent_graph()
    
    result = await graph.ainvoke({
        "query": query,
        "context": context
    })
    
    return result


async def stream_agent_workflow(query: str, context: str = ""):
    """
    Stream events from the agent workflow for real-time progress updates.
    
    Args:
        query: User's question
        context: Conversation context
        
    Yields:
        Events from the graph execution
    """
    graph = await get_agent_graph()
    
    async for event in graph.astream_events({
        "query": query,
        "context": context
    }, version="v2"):
        yield event



# Global agent instances
rag_agent = RAGAgent()
web_search_agent = WebSearchAgent()
memory_agent = MemoryAgent()
judging_agent = JudgingAgent()


if __name__ == "__main__":
    # Test the agents
    import asyncio
    
    async def test_agents():
        print("Testing agent workflow...")
        
        # Test query
        test_query = "전세권 설정 우선순 positions?"
        
        # Get agent graph
        graph = await create_agent_graph()
        
        # Run workflow
        result = await graph.invoke({
            "query": test_query,
            "context": "Previous conversation about real estate laws"
        })
        
        print(f"Query: {test_query}")
        print(f"Agent Flow: {result.get('agent_flow', [])}")
        print(f"Reasoning: {result.get('reasoning', '')}")
        print(f"Final Response: {result.get('final_response', '')[:200]}...")
        
        print("Agent workflow test completed!")
    
    asyncio.run(test_agents())
