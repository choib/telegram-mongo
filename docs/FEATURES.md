# ✨ Key Features

The Korean Law Expert Bot is equipped with several advanced features to ensure high-quality, reliable legal assistance.

## 1. Context-Aware Legal Retrieval
Unlike traditional search, our bot understands the structure of Korean Law.
- **Article Preservation**: The bot avoids breaking up individual Articles (`제N조`) into separate chunks, ensuring that the full context of a legal provision is available to the LLM.
- **Hierarchical Parsing**: It recognizes paragraphs and items within the law, maintaining the relationship between general rules and specific exceptions.

## 2. Confidence Assessment & Clarification
To prevent "hallucinations" or incomplete answers, the bot self-evaluates its responses.
- **Quality Score**: Every answer is assigned a confidence score (0-100%).
- **Automated Clarification**: If the score is low (below 85%), the bot will append 1-3 **Supplement Questions** to the response, asking the user for missing details needed to provide a more accurate legally-sound answer.

## 3. Hybrid Information Retrieval
Combining static law with real-time updates.
- **Local RAG**: Queries the curated corpus of 200+ Korean law files for foundational legal theory and statutes.
- **Tavily Web Search**: Automatically triggers for queries about recent legal news, legislative updates, or specific court cases that may not yet be in the local corpus.

## 4. Professional Legal Formatting
- **Safe Markdown**: All responses are formatted for Telegram's MarkdownV2, featuring clean law names and section headers.
- **Source Citations**: Every answer includes the exact law and revision date (e.g., `대한민국헌법(19880225)`) used for the response.

## 5. Intelligent Conversation History
- **Summarized Memory**: As the conversation grows, the bot automatically summarizes older turns to maintain context without exceeding LLM token limits or slowing down response times.
- **Session Persistence**: Chat history is reliably stored in MongoDB, allowing for long-running legal consultations.
