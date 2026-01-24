# Confidence Assessment and Supplement Questions Implementation

## Overview
This implementation adds confidence assessment functionality to the judge agent, which asks supplement questions when the confidence score is below 80%.

## Changes Made

### 1. Enhanced JudgingAgent in `src/agents.py`

#### Added Prompts:
- **Confidence Assessment Prompt**: Assesses the confidence level of generated answers (0-100 scale)
- **Supplement Question Generation Prompt**: Generates 1-3 specific questions to clarify ambiguities

#### New Methods:
- `assess_confidence(query, answer, context)`: 
  - Analyzes the generated answer
  - Provides a confidence score (0-100)
  - Returns reasoning for the score
  - Falls back to 70% if parsing fails

- `generate_supplement_questions(query, answer, confidence_assessment)`:
  - Identifies missing/unclear information
  - Generates 1-3 specific supplement questions
  - Provides default questions if generation fails

### 2. Updated Handler in `src/agentic_handlers.py`

#### Key Changes:
- **Confidence Assessment**: After generating the response, the handler now assesses confidence
- **Threshold Check**: If confidence < 80%, supplement questions are generated
- **User Notification**: Low confidence responses include:
  - The confidence score
  - A message explaining the low confidence
  - 1-3 supplement questions to clarify
- **High Confidence Path**: Responses with >=80% confidence work as before

#### Example Output (Low Confidence):
```
[Generated Answer]

🔍 답변의 신뢰도가 75%로 낮습니다.

추가 정보를 제공해주시면 더 정확한 답변을 드릴 수 있습니다:

1. '질문 내용'에 대해 더 자세한 정보를 제공할 수 있는 추가 정보가 있나요?
2. 이 질문에 답하기 위해 더 명확하게 할 수 있는 부분이 있나요?
3. 답변을 더 신뢰할 수 있도록 확인할 수 있는 추가 정보가 있나요?
```

## Technical Details

### Confidence Assessment Logic
1. The LLM self-assesses its confidence in the answer
2. Response is parsed to extract the confidence score
3. Fallback mechanisms ensure the system continues to work if parsing fails

### Supplement Question Generation
1. Based on the query, answer, and confidence assessment
2. Questions are designed to be:
  - Specific
  - Easy to answer
  - Limited to 1-3 questions
3. Default questions provide fallback if generation fails

### Threshold
- **80%**: The confidence threshold for determining when to ask supplement questions
- This threshold can be easily adjusted by changing the comparison in the handler

## Benefits

1. **Improved Transparency**: Users are informed when answers may not be fully reliable
2. **Better Accuracy**: Supplement questions help clarify ambiguities
3. **Iterative Improvement**: Users can provide additional context for better answers
4. **Graceful Degradation**: Fallback mechanisms ensure the system remains functional

## Testing

The implementation includes:
- Syntax validation
- Proper error handling
- Fallback mechanisms for all critical operations
- Logging for debugging and monitoring

## Configuration

The confidence threshold (80%) can be adjusted by modifying the comparison in `src/agentic_handlers.py`:

```python
if confidence_score < 80:  # Change this value to adjust the threshold
```

## Future Enhancements

Potential improvements:
- Adjustable threshold via configuration
- Multiple rounds of supplement questions
- Confidence-based agent selection
- User feedback to improve confidence assessment
