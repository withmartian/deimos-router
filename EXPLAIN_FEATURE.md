# Explain Feature Documentation

## Overview

The explain feature provides detailed information about how routing decisions are made in the deimos-router system. When enabled, it returns a list of rules and decisions that were used to select the model, making the routing process transparent and debuggable.

## Implementation Details

### Core Components

1. **ExplanationEntry Class** (`src/deimos_router/rules/base.py`)
   - Represents a single step in the routing decision process
   - Contains: `rule_type`, `rule_name`, `rule_trigger`, `decision`
   - Provides `to_dict()` method for JSON serialization

2. **Enhanced Decision Class** (`src/deimos_router/rules/base.py`)
   - Now includes optional `trigger` parameter
   - Tracks what caused a rule to make a specific decision

3. **Updated Rule Base Class** (`src/deimos_router/rules/base.py`)
   - Added `get_rule_type()` method to identify rule types
   - All rule implementations updated to provide trigger information

4. **Enhanced Router Class** (`src/deimos_router/router.py`)
   - New `select_model_with_explanation()` method
   - Tracks explanation entries as rules are evaluated
   - Accumulates explanations through rule chains

5. **Updated Chat API** (`src/deimos_router/chat.py`)
   - Added `explain` parameter to `create()` method
   - Includes explanation in response metadata when requested

## Usage

### Basic Usage

```python
from src.deimos_router.router import Router
from src.deimos_router.rules.task_rule import TaskRule
from src.deimos_router.rules.code_rule import CodeRule

# Create rules
task_rule = TaskRule("my-task-rule", {
    "creative writing": "gpt-4",
    "code review": "gpt-4o"
})

code_rule = CodeRule("my-code-rule", 
                    code="gpt-4o", 
                    not_code="gpt-3.5-turbo")

# Create router
router = Router("my-router", rules=[task_rule, code_rule])

# Get model selection with explanation
request_data = {
    "messages": [{"role": "user", "content": "Write a story"}],
    "task": "creative writing"
}

model, explanation = router.select_model_with_explanation(request_data)
```

### Chat API Usage

```python
from src.deimos_router.chat import chat

response = chat.completions.create(
    messages=[{"role": "user", "content": "Write a poem"}],
    model="deimos/my-router",
    task="creative writing",
    explain=True  # Enable explanation
)

# Access explanation from metadata
if hasattr(response, '_deimos_metadata') and 'explain' in response._deimos_metadata:
    explanation = response._deimos_metadata['explain']
    for entry in explanation:
        print(f"Rule: {entry['rule_name']}, Trigger: {entry['rule_trigger']}, Decision: {entry['decision']}")
```

## Explanation Format

Each explanation entry contains four fields:

- **rule_type**: The class name of the rule (e.g., "TaskRule", "CodeRule")
- **rule_name**: The name given to the rule instance
- **rule_trigger**: What caused the rule to activate (e.g., "creative writing", "code_detected")
- **decision**: The decision made by the rule (model name, "continue", "no_match")

### Example Explanation

```json
[
  {
    "rule_type": "TaskRule",
    "rule_name": "my-task-rule",
    "rule_trigger": "creative writing",
    "decision": "gpt-4"
  }
]
```

### Multi-Rule Example

```json
[
  {
    "rule_type": "TaskRule",
    "rule_name": "my-task-rule",
    "rule_trigger": "unknown_task",
    "decision": "no_match"
  },
  {
    "rule_type": "CodeRule",
    "rule_name": "my-code-rule",
    "rule_trigger": "code_detected",
    "decision": "gpt-4o"
  }
]
```

## Rule-Specific Triggers

### TaskRule Triggers
- Task name (e.g., "creative writing", "code review")
- "None" when no task is provided

### CodeRule Triggers
- "code_detected" when code is found in the message
- "no_code_detected" when no code is found
- "no_content" when messages are empty

### Default Fallback
- "default" for all fields when no rules match

## OpenAI Compatibility

The explain feature is designed to be compatible with OpenAI's chat completions API:

1. **Non-breaking**: The `explain` parameter is optional (defaults to `False`)
2. **Metadata approach**: Explanation is stored in `_deimos_metadata` to avoid interfering with standard response fields
3. **Standard response**: Callers expecting standard OpenAI responses are unaffected

## Testing

Run the explain feature tests:

```bash
python -m pytest tests/test_explain_feature.py -v
```

Run the example demonstration:

```bash
python example_explain_feature.py
```

## Benefits

1. **Transparency**: See exactly how routing decisions are made
2. **Debugging**: Identify why certain models are selected
3. **Optimization**: Understand rule effectiveness and ordering
4. **Compliance**: Audit trail for model selection decisions
5. **Development**: Easier to test and validate routing logic

## Future Enhancements

Potential improvements to the explain feature:

1. **Performance metrics**: Include timing information for rule evaluation
2. **Confidence scores**: Add confidence levels for decisions
3. **Alternative paths**: Show what would happen with different inputs
4. **Rule statistics**: Track rule usage patterns over time
5. **Visual debugging**: Generate flowcharts of decision paths
