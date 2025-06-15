# Wizard Agent Refactoring Plan

## Current Issues Analysis

### SOLID Principles Violations

#### 1. Single Responsibility Principle (SRP) Violations
- **main.py**: Handles API endpoints, memory management, LLM communication, and database operations
- **MemoryManager**: Manages context, summarization, message processing, and token counting
- **ConversationDB**: Handles all database operations for different entities

#### 2. Open/Closed Principle (OCP) Violations
- Hard-coded dependencies on OpenRouter API
- No abstraction for different LLM providers
- No abstraction for embedding models
- Fixed sentence transformer model

#### 3. Dependency Inversion Principle (DIP) Violations
- Direct dependencies on concrete implementations
- No dependency injection
- Global variables and direct instantiation

#### 4. Interface Segregation Principle (ISP) Violations
- Large interfaces that force clients to depend on unused methods
- No clear separation of concerns in interfaces

#### 5. Liskov Substitution Principle (LSP) Violations
- No clear interfaces to substitute implementations
- No polymorphic behavior

## Proposed Architecture

### 1. Core Domain Layer

#### Interfaces (Abstractions)
```
src/
├── core/
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── llm_provider.py          # LLM provider interface
│   │   ├── embedding_provider.py    # Embedding provider interface
│   │   ├── memory_repository.py     # Memory repository interface
│   │   ├── conversation_repository.py # Conversation repository interface
│   │   ├── user_repository.py       # User repository interface
│   │   └── context_manager.py       # Context manager interface
```

#### Domain Models
```
src/
├── core/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                  # User domain model
│   │   ├── conversation.py          # Conversation domain model
│   │   ├── memory.py                # Memory domain model
│   │   ├── context.py               # Context domain model
│   │   └── message.py               # Message domain model
```

#### Domain Services
```
src/
├── core/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── conversation_service.py  # Conversation orchestration
│   │   ├── memory_service.py        # Memory management
│   │   ├── context_service.py       # Context management
│   │   └── summarization_service.py # Summarization logic
```

### 2. Infrastructure Layer

#### Repositories
```
src/
├── infrastructure/
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── sql_user_repository.py
│   │   ├── sql_conversation_repository.py
│   │   └── sql_memory_repository.py
```

#### External Services
```
src/
├── infrastructure/
│   ├── external/
│   │   ├── __init__.py
│   │   ├── openrouter_llm_provider.py
│   │   ├── sentence_transformer_embedding_provider.py
│   │   └── http_client.py
```

#### Database
```
src/
├── infrastructure/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── connection.py            # Database connection
│   │   └── migrations/              # Alembic migrations
```

### 3. Application Layer

#### Use Cases
```
src/
├── application/
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── process_message_use_case.py
│   │   ├── get_context_use_case.py
│   │   └── summarize_conversations_use_case.py
```

#### DTOs
```
src/
├── application/
│   ├── dtos/
│   │   ├── __init__.py
│   │   ├── message_dto.py
│   │   ├── response_dto.py
│   │   └── context_dto.py
```

### 4. Presentation Layer

#### API Controllers
```
src/
├── presentation/
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── webhook_controller.py
│   │   └── health_controller.py
```

#### Middleware
```
src/
├── presentation/
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── logging_middleware.py
```

### 5. Configuration and Dependency Injection

```
src/
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Application settings
│   ├── container.py                 # Dependency injection container
│   └── logging_config.py            # Logging configuration
```

## Implementation Steps

### Phase 1: Core Interfaces and Models
1. Create abstract interfaces for all external dependencies
2. Define domain models with proper encapsulation
3. Create value objects for complex data structures

### Phase 2: Infrastructure Implementation
1. Implement concrete repository classes
2. Implement external service adapters
3. Refactor database models and connections

### Phase 3: Application Services
1. Implement use cases following CQRS pattern
2. Create DTOs for data transfer
3. Implement application services

### Phase 4: Presentation Layer
1. Create controllers with dependency injection
2. Implement proper error handling
3. Add middleware for cross-cutting concerns

### Phase 5: Configuration and Testing
1. Set up dependency injection container
2. Add comprehensive unit tests
3. Add integration tests
4. Update documentation

## Benefits of This Refactoring

1. **Maintainability**: Clear separation of concerns makes code easier to maintain
2. **Testability**: Dependency injection and interfaces make testing easier
3. **Extensibility**: Easy to add new LLM providers or embedding models
4. **Scalability**: Better structure for handling increased complexity
5. **Reusability**: Components can be reused across different parts of the application

## Migration Strategy

1. **Incremental Refactoring**: Refactor one component at a time
2. **Backward Compatibility**: Maintain existing API during transition
3. **Feature Flags**: Use feature flags to switch between old and new implementations
4. **Comprehensive Testing**: Ensure all functionality works after each refactoring step

## Files to Create

1. Core interfaces and models
2. Infrastructure implementations
3. Application services and use cases
4. Presentation layer controllers
5. Configuration and dependency injection setup
6. Unit and integration tests
7. Updated documentation

## Files to Refactor

1. `main.py` → Split into controllers and use cases
2. `database.py` → Split into repository implementations
3. `database_config.py` → Move to infrastructure/database/models.py
4. Add proper dependency injection and configuration management 