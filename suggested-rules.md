# Suggested Rule Types for Deimos Router

This document contains suggested rule types that could be valuable additions to the deimos-router project, based on common routing needs and use cases.

## Currently Implemented Rules

- **TaskRule** - Route based on explicit task metadata
- **CodeRule** - Route based on code detection (binary: code vs not-code)
- **CodeLanguageRule** - Route based on specific programming language detected
- **NaturalLanguageRule** - Route based on natural language detected (e.g., English, Spanish)
- **AutoTaskRule** - Automatically detect tasks from message content using LLM
- **MessageLengthRule** - Route based on message length (short/medium/long) ✅ **IMPLEMENTED**

## Suggested New Rule Types

### 1. ConversationContextRule ✅ **IMPLEMENTED**
- **Purpose**: Route based on conversation history length or context
- **Use cases**: New conversations vs ongoing discussions with lots of context
- **Parameters**: `new_threshold`, `deep_threshold`, `new_model`, `developing_model`, `deep_model`
- **Example**: First message → onboarding model, long conversations → context-aware model

### 2. TimeBasedRule
- **Purpose**: Route based on time of day, day of week, or date ranges
- **Use cases**: Peak hours → load balancing, off-hours → expensive models
- **Parameters**: `time_mappings` (time ranges → models)
- **Example**: Business hours → fast response, nights → powerful analysis

### 3. UserRule
- **Purpose**: Route based on user identity, role, or subscription tier
- **Use cases**: Premium users → better models, internal users → experimental models
- **Parameters**: `user_mappings`, `role_mappings`
- **Example**: Free tier → basic model, premium → advanced model

### 4. ContentComplexityRule
- **Purpose**: Route based on estimated complexity (technical depth, domain expertise needed)
- **Use cases**: Simple questions → basic model, expert-level → specialized model
- **Parameters**: `complexity_mappings` with LLM-based complexity assessment
- **Example**: "What is 2+2?" → simple, "Explain quantum entanglement" → complex

### 5. DomainRule
- **Purpose**: Route based on subject domain (medical, legal, technical, creative, etc.)
- **Use cases**: Domain-specific models or specialized routing
- **Parameters**: `domain_mappings` with LLM-based domain detection
- **Example**: Medical questions → medical-trained model, legal → legal model

### 6. SentimentRule
- **Purpose**: Route based on emotional tone (frustrated, happy, urgent, casual)
- **Use cases**: Urgent requests → fast response, frustrated users → empathetic model
- **Parameters**: `sentiment_mappings`
- **Example**: Angry tone → customer service model, casual → friendly model

### 7. LoadBalancingRule
- **Purpose**: Route based on current system load or model availability
- **Use cases**: Distribute load across multiple equivalent models
- **Parameters**: `model_pool`, `load_strategy` (round-robin, least-loaded, etc.)
- **Example**: Distribute requests across multiple GPT-4 instances

### 8. CostOptimizationRule
- **Purpose**: Route based on estimated cost vs. request importance
- **Use cases**: Budget management, cost-aware routing
- **Parameters**: `cost_thresholds`, `budget_mappings`
- **Example**: High-priority users → expensive model, batch processing → cheap model

### 9. FileTypeRule
- **Purpose**: Route based on attached file types or content
- **Use cases**: Image analysis → vision model, documents → text model
- **Parameters**: `file_type_mappings`
- **Example**: PDF uploads → document analysis model, images → vision model

### 10. ResponseLatencyRule
- **Purpose**: Route based on required response speed
- **Use cases**: Real-time chat → fast model, batch analysis → thorough model
- **Parameters**: `latency_mappings`
- **Example**: Interactive chat → sub-second model, research → comprehensive model

## Priority Recommendations

The most immediately useful rules to implement would be:

1. **UserRule** - Essential for multi-tenant applications with different service tiers
2. **LoadBalancingRule** - Critical for production deployments with multiple model instances
3. **ConversationContextRule** - Valuable for chat applications with ongoing conversations
4. **TimeBasedRule** - Useful for cost optimization and load management
5. **ContentComplexityRule** - Sophisticated routing based on actual request complexity

## Implementation Notes

- All rules should follow the existing pattern with `evaluate()` method returning `Decision` objects
- Rules should be composable and work well in rule chains
- Consider LLM-based detection for subjective classifications (complexity, domain, sentiment)
- Include comprehensive test suites for each rule type
- Provide example usage files demonstrating practical configurations
