# TuthorIA - Technical Documentation

## Service Communication

### 1. WhatsApp Service → DB Service

**Endpoint:** `POST /api/v1/conversations/messages`

Request:
```json
{
    "user_id": "string",      // WhatsApp number
    "content": "string",      // Message content
    "sender": "string",       // user_id or "assistant"
    "message_type": "text",   // Message type
    "timestamp": "string"     // ISO-8601 format
}
```

Response:
```json
{
    "status": "success",
    "message": "Message stored successfully"
}
```

### 2. WhatsApp Service → OpenAI Service

**Endpoint:** `POST /chat`

Request:
```json
{
    "content": "string",      // Message content
    "user_id": "string",      // WhatsApp number
    "message_type": "text"    // Message type (optional)
}
```

Response:
```json
{
    "response": "string"      // AI generated response
}
```

### 3. OpenAI Service → DB Service

**Endpoint:** `GET /api/v1/conversations/{user_id}`

Parameters:
- `user_id`: string (WhatsApp number)
- `limit`: integer (optional, default: 20)

Response:
```json
{
    "messages": [
        {
            "content": "string",
            "sender": "string",
            "message_type": "text",
            "timestamp": "string"
        }
    ],
    "user_id": "string"
}
```

## Data Models

### 1. Message Model
```python
class Message:
    content: str             # Message content
    user_id: str            # WhatsApp number
    message_type: str       # Default: "text"
    timestamp: datetime     # Message timestamp (optional)
```

### 2. ChatResponse Model
```python
class ChatResponse:
    response: str          # AI generated response
```

## API Endpoints

### WhatsApp Service (Port 8501)

1. `POST /chat`
   - Process messages through the service
   - Returns AI-generated responses
   - Handles message storage

2. `GET /health`
   - Health check endpoint
   - Verifies connections to other services

### OpenAI Service (Port 8502)

1. `POST /chat`
   - Process messages with AI
   - Stores conversation history
   - Returns AI-generated responses

2. `GET /conversations/{user_id}`
   - Retrieve conversation history
   - Supports pagination with limit parameter

3. `GET /health`
   - Health check endpoint
   - Verifies OpenAI API configuration

### DB Service (Port 8000)

1. `POST /api/v1/conversations/messages`
   - Store new messages
   - Creates conversations if needed

2. `GET /api/v1/conversations/{user_id}`
   - Retrieve conversation history
   - Supports pagination

3. `GET /health`
   - Health check endpoint
   - Returns service and database status

## Error Handling

### HTTP Status Codes

- 200: Success
- 400: Bad Request (invalid input)
- 500: Internal Server Error

### Error Response Format
```json
{
    "detail": "Error message"
}
```

## Deployment

### Railway Configuration

Each service has its own `railway.toml`:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheck = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Environment Variables

#### WhatsApp Service
```env
WHATSAPP_VERIFY_TOKEN=token
WHATSAPP_ACCESS_TOKEN=token
WHATSAPP_API_URL=url
OPENAI_SERVICE_URL=http://openai-service:8502
DB_SERVICE_URL=http://db-service:8000/api/v1
```

#### OpenAI Service
```env
OPENAI_API_KEY=your_api_key
DB_SERVICE_URL=http://db-service:8000/api/v1
```

#### DB Service
```env
MONGODB_USER=user
MONGODB_PASSWORD=password
MONGODB_HOST=mongodb.host
```

### Health Checks

Each service implements a `/health` endpoint that checks:
1. Service status
2. External service connections (WhatsApp Service)
3. Database connection (DB Service)
4. OpenAI API configuration (OpenAI Service)

Response format:
```json
{
    "status": "healthy",
    "environment": "production|development",
    "additional_info": {}
}
```
## Development Guidelines

### Message Processing Flow

1. **Message Reception**
   ```python
   # WhatsApp Service
   message = await webhook_handler.process_message(request)
   await store_message(message, is_user=True)
   ```

2. **AI Processing**
   ```python
   # OpenAI Service
   history = await get_conversation_history(user_id)
   response = await process_with_langchain(message, history)
   ```

3. **Response Handling**
   ```python
   # WhatsApp Service
   await store_message(response, is_user=False)
   await send_whatsapp_message(response)
   ```

### Best Practices

1. **Error Handling**
   - Always use try-catch blocks
   - Log errors with context and error details
   - Return appropriate HTTP status codes

2. **Logging**
   - Use structured logging with loguru
   - Include request IDs
   - Log important operations

3. **Message Storage**
   - Always validate message format
   - Include timestamps
   - Handle duplicates

4. **API Responses**
   - Use consistent response format
   - Include status codes
   - Provide meaningful error messages 
