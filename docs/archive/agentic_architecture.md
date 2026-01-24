# Agentic Architecture Transformation

## Overview

This document describes the transformation of the Telegram bot from a traditional monolithic architecture to an agentic architecture using Langgraph. The new architecture provides specialized agents that work together to provide better, more context-aware responses.

## Architecture Components

### 1. RAG Agent (Retrieval-Augmented Generation Agent)

**Purpose**: Specialized for legal document retrieval and question answering.

**Responsibilities**:
- Analyze user questions
- Retrieve relevant legal documents from the vector store
- Provide accurate, concise answers based on retrieved documents
- Clearly cite sources

**Key Features**:
- Uses the existing RAG pipeline with Chroma vector store
- Optimized for legal document retrieval
- Provides citations from legal sources

### 2. Web Search Agent

**Purpose**: Retrieve up-to-date information from the web.

**Responsibilities**:
- Search for recent information related to user queries
- Summarize the most relevant results
- Provide sources for verification
- Focus on Korean language results

**Key Features**:
- Integrates with Tavily web search API
- Provides recent, up-to-date information
- Complements the RAG agent with current information

### 3. Memory Agent

**Purpose**: Manage conversation history and context.

**Responsibilities**:
- Maintain concise summaries of conversation history
- Identify key topics and decisions
- Provide context for new questions
- Keep summaries under 200 words

**Key Features**:
- Uses LLM to generate intelligent summaries
- Reduces payload size by summarizing old conversations
- Provides continuity across multiple interactions

### 4. Judging/Orchestration Agent

**Purpose**: Determine which agents to use and how to combine outputs.

**Responsibilities**:
- Analyze user queries
- Determine which agents should be used (RAG, Web Search, or both)
- Decide the order of operations
- Combine results from different agents into coherent responses

**Key Features**:
- Intelligent routing based on query type
- Dynamic agent selection
- Result combination and conflict resolution
- Fallback mechanisms for robustness

## Agent Workflow

The agents work together in a coordinated flow:

```
User Query
    ↓
[Judging Agent] - Determines which agents to use
    ↓
[RAG Agent] - Retrieves legal documents (always used)
    ↓
[Web Search Agent] - Searches web (conditional)
    ↓
[Judging Agent] - Combines results
    ↓
Final Response to User
```

## Benefits of Agentic Architecture

### 1. Modularity
- Each agent has a clear, focused responsibility
- Agents can be updated or replaced independently
- Easier to maintain and debug

### 2. Intelligence
- Agents make decisions about which tools to use
- Dynamic routing based on query analysis
- Context-aware responses

### 3. Scalability
- New agents can be added without changing existing ones
- Workflow can be extended easily
- Better resource utilization

### 4. Robustness
- Fallback mechanisms built-in
- Error handling at each level
- Hybrid approach ensures reliability

### 5. Improved Responses
- Combines multiple information sources
- Better context understanding
- More accurate and comprehensive answers

## Implementation Details

### Langgraph Integration

The architecture uses Langgraph to define the agent workflow:

```python
workflow = Graph()

# Add nodes
workflow.add_node("judge", judge_node)
workflow.add_node("rag", rag_node)
workflow.add_node("web", web_node)
workflow.add_node("combine", combine_node)

# Add edges
workflow.add_edge("judge", "rag")
workflow.add_edge("rag", "combine")
workflow.add_edge("web", "combine")

# Conditional edges
workflow.add_conditional_edges("rag", should_use_web, {...})

# Compile
app = workflow.compile()
```

### Agent Configuration

All agents share a common configuration:
- OllamaClient for LLM access
- TavilyWebSearch for web search
- Configuration from config.py

### Error Handling

Each agent has its own error handling:
- Graceful degradation
- Fallback to simpler approaches
- Comprehensive logging

## Migration Path

### Phase 1: Hybrid Approach (Current)
- Traditional handler as fallback
- Agentic handler as primary
- Automatic switch on failure

### Phase 2: Full Agentic
- Remove traditional handler
- Refine agent logic
- Optimize performance

### Phase 3: Advanced Features
- Add more specialized agents
- Implement agent memory
- Add user preferences

## Performance Considerations

### Payload Optimization
- Memory agent summarizes old conversations
- Only recent messages sent to LLM
- Significant reduction in token usage

### Caching
- Agent graph compiled once and cached
- MongoDB connection reused
- Vector store loaded once

### Parallel Execution
- Web search can run in parallel with RAG
- Conditional execution reduces unnecessary work

## Testing Strategy

### Unit Tests
- Test each agent independently
- Mock external dependencies
- Verify error handling

### Integration Tests
- Test agent workflow end-to-end
- Verify message passing
- Check response quality

### End-to-End Tests
- Test with real Telegram bot
- Verify user experience
- Monitor performance metrics

## Monitoring and Logging

### Key Metrics
- Agent flow (which agents used)
- Response times
- Error rates
- Payload sizes
- Token usage

### Logging
- Agent decisions
- Query analysis
- Response generation
- Error conditions

## Configuration

All configuration is centralized in `config.py`:
- OLLAMA_HOST and OLLAMA_MODEL
- TAVILY_API_KEY
- MONGO_HOST and MONGO_PORT
- BOT_NAME
- EMBED_PATH for RAG

## Future Enhancements

### Potential Additions
1. **User Preference Agent**: Learn user preferences
2. **Translation Agent**: Support multiple languages
3. **Summarization Agent**: Generate concise summaries
4. **Question Analysis Agent**: Better query understanding
5. **Feedback Agent**: Incorporate user feedback

### Advanced Features
- Multi-turn conversation memory
- Personalized responses
- Adaptive learning
- Context switching

## Troubleshooting

### Common Issues

**Agentic handler fails**: Falls back to traditional handler automatically

**Web search fails**: Continues with RAG results only

**RAG retrieval fails**: Uses web search as fallback

**Memory agent fails**: Uses truncated conversation history

### Debugging Tips

1. Check logs for agent decisions
2. Verify MongoDB connection
3. Test each agent independently
4. Monitor payload sizes
5. Check LLM response times

## Conclusion

The agentic architecture transformation provides a more intelligent, flexible, and robust solution for the Telegram bot. By breaking down the monolithic approach into specialized agents, we achieve better responses, improved maintainability, and greater scalability.

---

**Last Updated**: 2024
**Version**: 1.0
**Authors**: Mistral Vibe
