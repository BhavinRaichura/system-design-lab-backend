# System Design Tutor

An interactive AI-powered system design interview platform where users can design architectures on a collaborative whiteboard, communicate with an AI tutor, and review their interview sessions later.

The backend is designed around **real-time session state, asynchronous persistence, and scalable AWS-native components**.

## 🚀 Architecture

```text
                         ┌──────────────┐
                         │   Frontend   │
                         │  Whiteboard  │
                         └──────┬───────┘
                                │
                         REST / WebSocket
                                │
                                ▼
                         ┌──────────────┐
                         │   FastAPI    │
                         │   Backend    │
                         └──────┬───────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
            ┌─────────┐                  ┌────────────┐
            │  Valkey │                  │ AI Tutor   │
            │Live State│                  │   Layer    │
            └────┬────┘                  └────────────┘
                 │
          Persistence throttle
                 │
                 ▼
            ┌─────────┐
            │   SQS   │
            └────┬────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Persistence      │
        │ Worker           │
        └────────┬─────────┘
                 │
                 ▼
           ┌───────────┐
           │ DynamoDB  │
           │ Persistent│
           │   State   │
           └───────────┘
```

## ✨ Key Features

### Real-time Architecture Sessions

* WebSocket-based communication for live architecture updates.
* Session-specific state maintained in Valkey.
* Version-based event validation to prevent stale events from overwriting newer state.
* Architecture state can be restored from persistent storage.

### Asynchronous Persistence

The system separates **live state management** from durable persistence.

```text
WebSocket
    ↓
Valkey
    ↓
Persistence throttle
    ↓
SQS
    ↓
Persistence Worker
    ↓
DynamoDB
```

This prevents WebSocket requests from waiting on DynamoDB writes.

Multiple architecture changes can occur while the latest state remains available in Valkey. Persistence events are throttled to avoid generating an SQS message for every real-time update.

### Reliable Persistence

SQS provides asynchronous delivery between the API and persistence worker.

The worker:

1. Receives a persistence event.
2. Retrieves the latest state from Valkey.
3. Persists the state to DynamoDB.
4. Deletes the SQS message only after successful persistence.

If DynamoDB fails, the message is not deleted and can be retried after the visibility timeout.

### Version Protection

DynamoDB conditional writes prevent stale or duplicate versions from overwriting newer architecture state.

```text
Stored version    Incoming version    Result
------------------------------------------------
5                 8                   Update
8                 8                   Ignore
8                 5                   Ignore
8                 10                  Update
```

This provides protection against duplicate and out-of-order SQS messages.

## 🗄️ Data Design

The DynamoDB table uses a composite primary key:

```text
Partition Key: session_key
Sort Key:      item_type
```

Example:

```text
SESSION#abc123 | METADATA
SESSION#abc123 | ARCHITECTURE
```

A Global Secondary Index is used to retrieve sessions belonging to a user:

```text
user_sessions_index

Partition Key: user_key
Sort Key:      session_created_at
```

### Session Metadata

```text
session_key
item_type
session_id
user_id
problem_id
status
created_at
user_key
session_created_at
```

### Architecture State

```text
session_key
item_type
nodes
edges
version
updated_at
```

## 🧰 Tech Stack

### Backend

* Python
* FastAPI
* WebSockets
* Pydantic
* Boto3

### AWS

* Amazon DynamoDB
* Amazon SQS
* Amazon EC2 — deployment target
* Amazon ElastiCache for Valkey — deployment target

### Local Development

* Docker
* Docker Compose
* LocalStack
* Valkey

### AI

The AI tutor layer is being integrated as the next major feature and will provide contextual feedback on the user's system design.

## 🏃 Local Development

### Prerequisites

* Python 3.x
* Docker
* Docker Compose
* AWS CLI
* LocalStack

### Start infrastructure

```bash
docker compose up -d
```

### Activate virtual environment

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the backend

```bash
ENVIRONMENT=development \
uvicorn app.main:app --reload
```

## 🧪 Testing

Individual infrastructure components can be tested using the development test modules.

### Test Valkey

```bash
ENVIRONMENT=development \
python3 -m app.test.redis.test_connection
```

### Test SQS

```bash
ENVIRONMENT=development \
python3 -m app.test.sqs.test_connection
```

### Test SQS receive

```bash
ENVIRONMENT=development \
python3 -m app.test.sqs.test_receive
```

### Test persistence worker

```bash
ENVIRONMENT=development \
python3 -m app.test.sqs.test_worker
```

## 🔄 Persistence Flow

A typical architecture update follows this path:

```text
1. User changes architecture
             ↓
2. WebSocket sends event
             ↓
3. Backend validates event version
             ↓
4. Event applied to session state
             ↓
5. Latest state stored in Valkey
             ↓
6. Persistence throttle checked
             ↓
7. SQS persistence event created
             ↓
8. Worker consumes event
             ↓
9. Worker retrieves latest state from Valkey
             ↓
10. DynamoDB conditionally updates state
             ↓
11. SQS message deleted
```

## 🎯 Design Decisions

### Why Valkey?

Valkey provides low-latency access to active interview session state. It acts as the hot state layer while DynamoDB acts as the durable storage layer.

### Why SQS?

Persistence should not block real-time WebSocket operations.

SQS decouples the API from the persistence worker and provides retry behavior when downstream persistence fails.

### Why retrieve state from Valkey inside the worker?

The SQS message represents:

> "This session needs persistence."

It does not represent:

> "Persist exactly this version."

Therefore, the worker retrieves the latest state from Valkey before writing to DynamoDB.

This allows multiple real-time changes to be collapsed into a single persistence operation.

### Why DynamoDB conditional writes?

SQS provides at-least-once delivery, so duplicate messages are possible.

Conditional writes prevent an older version from overwriting a newer version.

## ⚠️ Current Backend Limitations

The current MVP intentionally focuses on the core real-time and persistence architecture.

### WebSocket

* Reconnection handling needs improvement.
* Connection cleanup needs additional handling.
* More comprehensive invalid-event handling is required.

### Valkey

* Session-state TTL needs production-level tuning.
* Additional failure handling is required.

### SQS

* Dead-letter queue is not implemented yet.
* Retry configuration requires production tuning.
* Producer failure handling needs improvement.

### Persistence Worker

* Current worker implementation is minimal.
* Graceful shutdown needs to be added.
* Production-level error handling and monitoring are pending.

### Testing

* Infrastructure integration tests are currently basic.
* Automated unit/integration test coverage needs to be expanded.

### Security

* Authentication and authorization are not implemented in the MVP.

### Observability

* Structured logging, metrics, tracing, and CloudWatch dashboards are planned.

## 🛣️ Roadmap

### Phase 1 — Backend Foundation

* [x] FastAPI backend
* [x] Session APIs
* [x] DynamoDB persistence
* [x] Valkey integration
* [x] WebSocket communication
* [x] SQS integration
* [x] Persistence worker
* [x] Version-based persistence protection
* [x] Persistence throttling

### Phase 2 — AI Tutor

* [ ] Context-aware AI tutor
* [ ] System design requirement analysis
* [ ] Architecture feedback
* [ ] Follow-up interview questions
* [ ] Bottleneck identification
* [ ] Final architecture evaluation

### Phase 3 — Voice Interaction

* [ ] Speech-to-text
* [ ] Text-to-speech
* [ ] Real-time voice interaction

### Phase 4 — Production Deployment

* [ ] EC2 deployment
* [ ] ElastiCache Valkey
* [ ] AWS SQS
* [ ] DynamoDB
* [ ] Production configuration
* [ ] Monitoring and logging

## 📌 Project Status

**Current status: Backend real-time and asynchronous persistence architecture implemented.**

The next major milestone is integrating the **AI system design tutor** with the existing WebSocket-based session infrastructure.
