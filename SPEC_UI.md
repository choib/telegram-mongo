# 🤖 Telegram UI & Interaction Specification (SPEC_UI.md)

This document defines the user interface, interaction patterns, and message formatting rules for the Telegram bot.

## 1. Interaction Flow
The bot follows a non-blocking, agentic interaction pattern:
1. **User Input**: Bot immediately shows 'typing' status.
2. **Thinking Phase**: Bot sends a "thinking" message (e.g., `💭 관련 정보를 검색하고 있습니다...`).
3. **Progress Updates**: The thinking message is updated in real-time as the agent moves through the graph nodes (Analyze -> Retrieval -> Combine).
4. **Final Response**: The thinking message is replaced by the actual AI response.

## 2. Formatting Rules (MarkdownV2)
Telegram's `MarkdownV2` is strict and requires specific escaping. The bot uses `src/agentic_handlers.py:format_response_with_markdown` to automate this.

### 2.1 Standard Mappings
- `### Header` -> `*Bold Text*`
- `**Bold**` -> `*Bold*`
- `*Italic*` -> `_Italic_`
- `[text](url)` -> Preserved and escaped.

### 2.2 Character Escaping
The following characters MUST be escaped with a backslash if they are not part of a markdown entity:
`_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`

## 3. Advanced UI Features

### 3.1 Progress Animation
Managed by `stream_agent_workflow`. The UI updates as following nodes execute:
- `analyze`: 🔍 Understanding context...
- `retrieval`: 📚 Searching...
- `combine`: ✍️ Crafting response...

### 3.2 Intelligent Message Splitting
To handle responses exceeding Telegram's 4,096 character limit:
- **Logic**: Splits by double newlines (paragraphs) where possible.
- **Safety**: Each part is processed by `safe_truncate` to ensure no trailing backslashes or unclosed markdown tags (bold/italic/code) exist before the split.
- **Delivery**: The first part replaces the thinking message; subsequent parts are sent as new messages.

### 3.3 Confidence & Supplement Questions
When AI confidence is below the `CONFIDENCE_THRESHOLD` (default 85%):
- Append a localized warning (e.g., `⚠️ *참고: 이 답변의 신뢰 점수가 낮습니다*`).
- Append 2-3 AI-generated follow-up questions to clarify the user's situation.

## 4. Commands Registry
- `/start`: Greeting and personality-specific onboarding message.
- `/user_id`: Returns the user's numeric ID (for debugging/persistence).
- `/clear_memory`: Wipes conversation history.

## 5. Error Handling
- **User-Facing**: Sends a localized error emoji and message (e.g., 😿).
- **Graceful Recovery**: Uses `hybrid_text_chat_handler` to fall back to a non-agentic LLM call if the LangGraph execution fails.
