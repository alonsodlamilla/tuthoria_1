# Chat Service API

A FastAPI-based chat service with MongoDB Atlas integration, providing CRUD operations for managing conversations. Built with modern Python async features and containerized with Docker.

## Features

- 🚀 FastAPI for high-performance async API
- 📦 MongoDB Atlas integration using Motor
- 🔒 Environment-based configuration
- 🐳 Docker and Docker Compose setup
- ✅ Comprehensive test suite
- 📝 Full CRUD operations for conversations
- 🔄 Real-time message management
- 📚 Auto-generated API documentation

## Prerequisites

- Docker and Docker Compose
- MongoDB Atlas account
- Python 3.11+ (for local development)

## Project Structure

```
db-service/
├── Dockerfile
├── README.md
├── config.py
├── database.py
├── main.py
├── models
│   └── conversation.py
├── requirements.txt
├── routes
│   └── conversation.py
└── utils
    └── logging.py
```

## Environment Setup

1. Create a `.env` file in the root directory:

```env
MONGODB_USER=your_username
MONGODB_PASSWORD=your_password
MONGODB_HOST=your_cluster.mongodb.net
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
```

## API Endpoints

### Conversations

- `POST /conversations/` - Create a new conversation
- `GET /conversations/` - List all conversations
- `GET /conversations/{conversation_id}` - Get a specific conversation
- `POST /conversations/{conversation_id}/messages` - Add a message to a conversation
- `DELETE /conversations/{conversation_id}` - Delete a conversation
