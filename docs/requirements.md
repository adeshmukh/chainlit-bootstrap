# Project Requirements

## Overview

This project is a Chainlit-based conversational AI application that enables users to upload documents and ask questions about them. The application includes features for document question-answering, PII (Personally Identifiable Information) detection and anonymization, and voice input capabilities.

## Core Features

### 1. Document Question-Answering (QA)
- **Status**: ✅ Implemented
- **Description**: Users can upload text documents and ask questions about their content
- **Implementation**: 
  - Uses LangChain's `ConversationalRetrievalChain` for RAG (Retrieval-Augmented Generation)
  - ChromaDB vector store for document embeddings
  - OpenAI GPT-4o-mini for LLM responses
  - Recursive text splitting with 1000 character chunks and 100 character overlap
- **Current Limitations**:
  - Only supports plain text files (`.txt`)
  - PDF support mentioned but not yet implemented (requires additional libraries like `pypdf`)

### 2. PII Detection and Anonymization
- **Status**: ✅ Implemented
- **Description**: Automatically detects and anonymizes personally identifiable information in both user inputs and AI responses
- **Implementation**:
  - Uses Microsoft Presidio (`presidio-analyzer` and `presidio-anonymizer`)
  - spaCy English model (`en_core_web_sm`) for NLP processing
  - Applied to both user queries and AI-generated answers
- **Purpose**: Ensures privacy and security by preventing PII from being exposed in conversations

### 3. Voice Input
- **Status**: 🚧 Partially Implemented
- **Description**: Support for real-time voice input using microphone
- **Current State**:
  - Chainlit audio chunk handling is implemented (`on_audio_chunk` callback)
  - Placeholder for OpenAI Realtime API integration
  - Currently acknowledges audio input but doesn't process it
- **TODO**: 
  - Integrate OpenAI Realtime API for speech-to-text
  - Implement audio transcription and streaming responses

### 4. Authentication
- **Status**: ✅ Configured
- **Description**: Google OAuth authentication enabled
- **Configuration**: 
  - Set in `chainlit.toml` with `provider = "google"`
  - Requires environment variables: `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`
  - OAuth callback handler in `chainlit_bootstrap/auth.py` allows all authenticated Google users
  - Can be customized to restrict access by domain or other criteria

### 5. File Upload
- **Status**: ✅ Implemented
- **Description**: Users can upload files with messages
- **Configuration**:
  - Accepts all file types (`accept = ["*/*"]`)
  - Maximum 10 files per upload
  - Maximum 10 MB per file
  - Document upload required at chat start (20 MB limit)

### 6. Persistent Sessions
- **Status**: ✅ Enabled
- **Description**: Users can create and switch between different conversation threads
- **Storage**: SQLite database with aiosqlite

## Environment Requirements

### Required Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for LLM and embeddings (required)
- `OAUTH_GOOGLE_CLIENT_ID`: Google OAuth client ID (required for authentication)
- `OAUTH_GOOGLE_CLIENT_SECRET`: Google OAuth client secret (required for authentication)
- `OAUTH_REDIRECT_URI`: OAuth redirect URI for Google authentication (required for authentication)
- `CHAINLIT_AUTH_SECRET`: Secret key for signing authentication tokens (required for authentication). Generate with `chainlit create-secret` or it will be auto-generated (not recommended for production)

### Optional Environment Variables
- `DEFAULT_GAI_MODEL`: LLM model name (default: `gpt-4o-mini`)
- `CHAINLIT_PORT`: Port for Chainlit server (default: `8000`)
- `CHAINLIT_HOST`: Host for Chainlit server (default: `0.0.0.0`)

## Current Limitations and Future Enhancements

### Known Limitations
1. **PDF Support**: Currently only supports plain text files. PDF parsing requires additional implementation.
2. **Voice Input**: Audio processing is not fully functional; needs OpenAI Realtime API integration.
3. **Model Support**: Currently hardcoded to OpenAI models only (though architecture supports others).

### Potential Enhancements
1. Add PDF parsing support using `pypdf` or similar libraries
2. Complete OpenAI Realtime API integration for voice input
3. Support for additional LLM providers (Anthropic, Cohere, etc.)
4. Enhanced PII detection with custom entity types
5. Multi-language support for PII detection
6. Document metadata extraction and indexing
7. Support for multiple document uploads in a single session
8. Export conversation history
9. Advanced retrieval strategies (hybrid search, reranking)

## Project State

- **Version**: 0.1.0
- **Python Version**: 3.12 (required)
- **Status**: Functional core features implemented, voice input pending

