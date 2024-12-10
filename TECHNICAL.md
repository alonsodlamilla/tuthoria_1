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
    "message_type": "text"    // Message type
}
```

Response:
```json
{
    "response": "string",     // AI generated response
    "timestamp": "string"     // ISO-8601 format
}
```

### 3. OpenAI Service → DB Service

**Endpoint:** `GET /api/v1/conversations/{user_id}`

Parameters:
- `user_id`: string (WhatsApp number)
- `limit`: integer (optional, default: 10)

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
    ]
}
```

## Data Models

### 1. Message Model
```python
class Message:
    content: str             # Message content
    sender: str             # user_id or "assistant"
    timestamp: datetime     # Message timestamp
    message_type: str       # Default: "text"
```

### 2. Conversation Model
```python
class Conversation:
    id: ObjectId           # MongoDB document ID
    user_id: str          # WhatsApp number
    title: str            # Optional, defaults to "Chat with {user_id}"
    participants: List[str] # List of participants
    messages: List[Message] # Conversation messages
    created_at: datetime   # Creation timestamp
    updated_at: datetime   # Last update timestamp
```

## API Endpoints

### WhatsApp Service

1. `GET /whatsapp`
   - Webhook verification for WhatsApp API
   - Query params: `hub.mode`, `hub.verify_token`, `hub.challenge`

2. `POST /whatsapp`
   - Webhook for incoming messages
   - Handles message processing and response

3. `GET /health`
   - Health check endpoint
   - Returns service status

### OpenAI Service

1. `POST /chat`
   - Process messages with AI
   - Returns AI-generated responses

2. `GET /health`
   - Health check endpoint
   - Returns service status

### DB Service

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
- 401: Unauthorized (invalid token)
- 403: Forbidden (invalid verification)
- 404: Not Found
- 500: Internal Server Error
- 503: Service Unavailable

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

Production URLs format:
- Internal: `https://{service-name}.railway.internal`
- External: `https://{service-name}-production.up.railway.app`

### Health Checks

Each service implements a `/health` endpoint that checks:
1. Service status
2. Database connection (if applicable)
3. External service connections

Response format:
```json
{
    "status": "healthy",
    "database": "connected",
    "service": "running"
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