# WorkPilot AI — Secure AI Work Orchestration Platform

> **WorkPilot AI** is a multi-agent productivity workspace designed to help individuals and teams understand, plan, and execute work across tasks, organizational knowledge, email, and calendars. It combines LangGraph orchestration, retrieval-augmented generation (RAG), MCP-based integrations, persistent workflow state, and human approval for sensitive actions.
>
> **Project status:** Architecture and implementation blueprint. Update the status badges and feature checklist as each capability is implemented and tested. Targets in this README are proposed acceptance criteria—not measured results.

<!-- Replace OWNER/REPOSITORY with your GitHub details. -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/AI-LangGraph-7C3AED" alt="LangGraph" />
  <img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Integrations-MCP-2563EB" alt="MCP" />
  <img src="https://img.shields.io/badge/Deployment-Docker-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Status-In%20Development-orange" alt="In development" />
</p>

---

## Contents

- [1. Product vision](#1-product-vision)
- [2. Product capabilities](#2-product-capabilities)
- [3. Example workflows](#3-example-workflows)
- [4. Architecture](#4-architecture)
- [5. LangGraph orchestration](#5-langgraph-orchestration)
- [6. RAG architecture](#6-rag-architecture)
- [7. MCP integrations and tools](#7-mcp-integrations-and-tools)
- [8. Advanced API inputs](#8-advanced-api-inputs)
- [9. Database schema](#9-database-schema)
- [10. API design](#10-api-design)
- [11. Security and approval model](#11-security-and-approval-model)
- [12. Evaluation and production targets](#12-evaluation-and-production-targets)
- [13. Observability and cost management](#13-observability-and-cost-management)
- [14. Technology stack](#14-technology-stack)
- [15. Repository structure](#15-repository-structure)
- [16. Local development](#16-local-development)
- [17. Docker deployment](#17-docker-deployment)
- [18. CI/CD](#18-cicd)
- [19. Testing strategy](#19-testing-strategy)
- [20. Roadmap](#20-roadmap)
- [21. Engineering principles](#21-engineering-principles)
- [22. Contributing](#22-contributing)

---

## 1. Product vision

Most productivity tools keep tasks, documents, email, and calendars in separate places. WorkPilot AI aims to connect these systems through a permission-aware AI orchestration layer.

A user can ask for an outcome—such as preparing for a meeting or turning an email commitment into a task—and the platform can:

1. Understand the request and authenticated user's context.
2. Route the request to a specialist agent.
3. Retrieve relevant information and call permitted tools.
4. Build a multi-step plan when the request requires it.
5. Pause for explicit approval before sensitive external actions.
6. Persist workflow progress and recover from interruptions.
7. Return the result with relevant sources and an auditable action history.

### Product principles

- **Outcome-oriented:** organize agents around useful workflows, not just chat personas.
- **Permission-aware:** user and workspace access rules apply to every data and tool operation.
- **Human-controlled:** consequential actions require application-validated approval.
- **Recoverable:** workflows persist state and safely resume after interruption.
- **Measurable:** routing, retrieval, tool execution, latency, and cost are evaluated.
- **Composable:** agents use reusable tools and skills rather than duplicating integrations.

## 2. Product capabilities

| Capability | Description | Implementation status |
|---|---|---|
| Multi-agent routing | Supervisor selects Task, Knowledge, Planning, or Communication agent | Core architecture |
| Task management | Create, list, update, prioritize, and delete tasks | Existing project scope; verify implementation |
| Knowledge assistant | Search uploaded knowledge with RAG and source references | Existing project scope; verify implementation |
| Planning | Turn broad goals into ordered steps and proposed actions | Existing project scope; verify implementation |
| Email assistant | Search, read, summarize, and draft emails | Integration scope |
| Calendar assistant | List events and propose or create calendar events | Integration scope |
| Human approval | Review sensitive actions before execution | Required production capability |
| User memory | Store user preferences separately from chat history | Planned enhancement |
| Scheduled routines | Daily briefing and recurring work preparation | Planned enhancement |
| Observability | Trace agent decisions, tool calls, failures, latency, and cost | Planned enhancement |
| Web dashboard | Chat, tasks, approvals, integrations, and usage views | Planned enhancement |

> Do not mark a capability as complete until it is implemented, tested, and documented in this repository.

## 3. Example workflows

### 3.1 Daily work briefing

```mermaid
flowchart TD
    A[Scheduled trigger or user request] --> B[Load authorized user context]
    B --> C[Read today's calendar]
    B --> D[Retrieve open and overdue tasks]
    B --> E[Summarize relevant unread emails]
    C --> F[Combine work context]
    D --> F
    E --> F
    F --> G[Prioritize and identify conflicts]
    G --> H[Generate briefing with source references]
    H --> I[Display to user]
```

**Expected output:** today's meetings, high-priority tasks, deadlines, relevant email updates, and suggested next actions. The briefing is read-only unless the user separately approves a proposed write action.

### 3.2 Meeting intelligence

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant Graph as LangGraph
    participant Calendar as Calendar tools
    participant Mail as Gmail tools
    participant RAG as RAG service

    User->>API: Prepare me for my next meeting
    API->>Graph: Request + trusted user context
    Graph->>Calendar: Find next authorized event
    Calendar-->>Graph: Event details
    par Gather context
        Graph->>Mail: Search related emails
        Mail-->>Graph: Relevant email content
    and Retrieve knowledge
        Graph->>RAG: Search related documents
        RAG-->>Graph: Ranked chunks + citations
    end
    Graph-->>API: Agenda, context, questions, action items
    API-->>User: Meeting preparation brief
```

### 3.3 Email-to-task automation

1. Search for a relevant email using the authenticated user's Gmail connection.
2. Extract commitments, owners, due dates, and requested actions.
3. Generate proposed tasks with source email references.
4. Show the proposed changes to the user.
5. Validate approval and task ownership on the server.
6. Create tasks idempotently and record the result in the audit trail.

### 3.4 Other useful skills

- `summarize_email`
- `prepare_meeting`
- `research_topic`
- `create_task_from_email`
- `find_schedule_conflicts`
- `draft_follow_up_email`
- `generate_daily_briefing`

Skills are reusable workflow definitions with validated inputs, tool permissions, expected outputs, and evaluation cases.

## 4. Architecture

### 4.1 High-level production architecture

```mermaid
flowchart TB
    U[User / Team Member] --> UI[React or Next.js Workspace]
    UI --> API[FastAPI API Gateway]
    API --> AUTH[Authentication + Workspace Context]
    AUTH --> POLICY[RBAC + Request Policy]
    POLICY --> ORCH[LangGraph Supervisor / Workflow Orchestrator]

    subgraph AGENTS[Specialist Agents]
      TASK[Task Agent]
      KNOW[Knowledge Agent]
      PLAN[Planning Agent]
      COMM[Communication Agent]
    end

    ORCH --> TASK
    ORCH --> KNOW
    ORCH --> PLAN
    ORCH --> COMM

    TASK --> TOOLS[Tool Registry / MCP Clients]
    KNOW --> RAG[RAG Retrieval Service]
    PLAN --> TOOLS
    COMM --> APPROVAL[Approval Gate]
    APPROVAL --> TOOLS

    TOOLS --> MCP[MCP Servers]
    MCP --> TASKDB[Task Service]
    MCP --> GMAIL[Gmail API]
    MCP --> CAL[Google Calendar API]

    RAG --> VDB[(Vector Store)]
    RAG --> DOCDB[(Document Metadata / PostgreSQL)]

    ORCH <--> CHECK[(PostgreSQL Checkpointer)]
    API <--> APPDB[(PostgreSQL Application Data)]
    API --> REDIS[(Redis / Queue - optional)]
    REDIS --> WORKER[Background Workers]
    WORKER --> RAG

    ORCH --> OBS[Tracing / Metrics / Logs]
    API --> OBS
    MCP --> OBS
```

### 4.2 Request lifecycle

```mermaid
flowchart TD
    A[Incoming request] --> B[Authenticate session]
    B --> C[Resolve workspace and permissions]
    C --> D[Validate request and attachments]
    D --> E[Load conversation checkpoint]
    E --> F[Supervisor routes request]
    F --> G[Specialist agent]
    G --> H{Tool needed?}
    H -->|No| N[Compose response]
    H -->|Yes| I[Validate tool and arguments]
    I --> J{Sensitive side effect?}
    J -->|No| K[Authorize and execute]
    J -->|Yes| L[Create approval request]
    L --> M[Wait for authenticated approval]
    M -->|Approved| O[Verify approval, expiry, action hash]
    M -->|Rejected / expired| P[Do not execute]
    O --> Q[Idempotent execution]
    K --> R[Persist result and audit event]
    Q --> R
    P --> R
    R --> N
    N --> S[Return response and citations]
```

### 4.3 Architecture boundaries

| Component | Responsibility | Must not do |
|---|---|---|
| FastAPI | Authentication, request validation, API lifecycle | Trust client-supplied user identity |
| Supervisor | Select agent and coordinate workflow | Bypass application authorization |
| Specialist agents | Reason about a bounded domain and select tools | Directly access secrets or bypass tool policy |
| Policy layer | Enforce user, workspace, and action permissions | Depend only on prompt instructions |
| MCP tools | Execute narrowly scoped external operations | Trust unvalidated LLM arguments |
| RAG service | Retrieve permitted documents and return evidence | Mix tenant data or follow instructions inside documents |
| Checkpointer | Persist graph execution state | Store OAuth secrets or raw credentials |
| Audit service | Record actor, action, decision, and outcome | Log access tokens or sensitive payloads unnecessarily |

## 5. LangGraph orchestration

### 5.1 Specialist agents

| Agent | Responsibilities | Typical tools |
|---|---|---|
| Task Agent | Task CRUD, priorities, deadlines, task search | `create_task`, `list_tasks`, `update_task`, `delete_task` |
| Knowledge Agent | Knowledge search, grounded answers, document summaries | `rag_search`, `get_document_metadata` |
| Planning Agent | Break goals into steps, identify dependencies, propose workflows | Read-only task/calendar search; delegates execution |
| Communication Agent | Email and calendar assistance | `search_emails`, `read_email`, `create_email_draft`, calendar tools |

The Planning Agent should propose and coordinate work. It should not silently execute consequential operations. Execution is delegated to authorized tools and approval-aware workflows.

### 5.2 State design

A simplified conceptual state shape:

```python
from typing import Any, Literal, NotRequired
from typing_extensions import TypedDict
from langgraph.graph import MessagesState

AgentName = Literal["task", "knowledge", "planning", "communication"]
ApprovalStatus = Literal["pending", "approved", "rejected", "expired"]

class WorkPilotState(MessagesState):
    user_request: str
    selected_agent: NotRequired[AgentName]
    result: NotRequired[str]
    approval_status: NotRequired[ApprovalStatus]
    pending_action: NotRequired[dict[str, Any]]
    workflow_id: NotRequired[str]
    error_code: NotRequired[str]
```

**Identity rule:** authenticated `user_id`, workspace membership, and permissions must be derived by trusted server-side code. If user context is passed through graph state, it must be injected by the server—not copied from the request body. Never place OAuth access or refresh tokens in graph state.

### 5.3 Routing strategy

- Use structured output for supervisor decisions.
- Validate the selected agent against an allow-list.
- Ask a clarification question when the request is genuinely ambiguous.
- Set a maximum number of agent/tool iterations.
- Handle tool errors explicitly and avoid infinite agent/tool loops.
- Keep specialist prompts scoped to their domain.
- Treat retrieved documents, email bodies, and tool output as untrusted data, not instructions.

### 5.4 Durable execution

Use a PostgreSQL-backed LangGraph checkpointer for resumable production workflows. Use the same authenticated thread ownership checks when loading or resuming a conversation. A thread ID is a lookup key, not an authorization credential.

## 6. RAG architecture

### 6.1 Ingestion and retrieval pipeline

```mermaid
flowchart TD
    A[PDF / DOCX / TXT / HTML] --> B[File validation and malware checks]
    B --> C[Text extraction]
    C --> D[Cleaning and normalization]
    D --> E[Chunking with metadata]
    E --> F[Embedding generation]
    E --> G[Lexical indexing]
    F --> H[(Vector index)]
    G --> I[(BM25 index)]

    Q[User question] --> J[Query normalization / expansion]
    J --> K[Permission and metadata filters]
    K --> H
    K --> I
    H --> L[Hybrid result fusion]
    I --> L
    L --> M[Reranking]
    M --> N[Context selection]
    N --> O[LLM answer with source references]
```

### 6.2 Recommended retrieval stages

1. **Ingestion:** validate file type, size, ownership, workspace, and access policy.
2. **Parsing:** extract text and preserve useful page, section, and source metadata.
3. **Chunking:** use configurable chunk size and overlap; evaluate rather than assuming one setting is optimal.
4. **Indexing:** create dense embeddings and a lexical BM25 index.
5. **Filtering:** apply workspace and document ACL filters before results are exposed to the model.
6. **Hybrid retrieval:** combine lexical and dense results using a tested fusion strategy such as Reciprocal Rank Fusion.
7. **Reranking:** reorder candidates using a cross-encoder or another evaluated reranker.
8. **Generation:** answer only from evidence when the question requires knowledge grounding.
9. **Citations:** return document IDs and page/section references where available.
10. **Evaluation:** measure retrieval quality and answer faithfulness on a fixed dataset.

### 6.3 RAG response contract

```json
{
  "answer": "The policy allows eligible employees to request leave...",
  "insufficient_evidence": false,
  "sources": [
    {
      "document_id": "doc_123",
      "document_name": "employee_policy.pdf",
      "page": 4,
      "chunk_id": "chunk_456"
    }
  ]
}
```

The example is illustrative. Source identifiers and page references must come from actual indexed documents. If evidence is insufficient, the assistant should say so instead of inventing an answer.

## 7. MCP integrations and tools

MCP provides a consistent interface between agents and external capabilities. The platform can expose separate local MCP servers for internal productivity tools and Google Workspace integrations.

### 7.1 Proposed server boundaries

| MCP server | Example tools | Access type |
|---|---|---|
| `workpilot` | Task CRUD, document metadata, workflow utilities | User/workspace-scoped |
| `google_workspace` | Gmail search/read/draft/send, Calendar list/create/update/delete | OAuth account-scoped |
| Future integrations | Microsoft Graph, Slack/Teams, project tools | Provider- and user-scoped |

### 7.2 Tool risk classification

| Tool operation | Risk | Approval policy |
|---|---|---|
| Search email | Read | Auth + scope check |
| Read email | Read | Auth + scope check |
| Draft email | External draft write | Product policy; approval may be required |
| Send email | Sensitive side effect | Explicit approval required |
| List calendar events | Read | Auth + scope check |
| Create/update calendar event | Sensitive side effect | Explicit approval required |
| Delete calendar event | Destructive side effect | Explicit approval required |
| List tasks | Read | Workspace ownership check |
| Create/update task | Data write | Policy-controlled; approval for consequential changes |
| Delete task | Destructive side effect | Explicit confirmation and authorization |

### 7.3 OAuth and multi-user integration

- Use OAuth 2.0 authorization code flow with secure state validation.
- Request the minimum scopes needed for each capability.
- Encrypt refresh tokens at rest using a managed key or envelope encryption.
- Resolve credentials using the authenticated user and connected provider account.
- Refresh tokens server-side; never send them to the browser or LLM.
- Support revocation, reconnection, and account unlinking.
- Do not use a shared global cache for user-specific credentials or authenticated clients.

## 8. Advanced API inputs

The API should support useful workflow controls while keeping security-sensitive values server-controlled.

### 8.1 Chat request

```json
{
  "message": "Prepare me for my 2 PM project meeting and identify follow-up tasks.",
  "thread_id": "thread_01JEXAMPLE",
  "response_mode": "detailed",
  "output_format": "structured",
  "agent_hint": "planning",
  "timezone": "Asia/Kolkata",
  "locale": "en-IN",
  "include_sources": true,
  "attachments": [
    {
      "file_id": "file_01JEXAMPLE"
    }
  ],
  "context": {
    "workflow_template": "meeting_preparation",
    "priority": "high"
  },
  "client_request_id": "req_01JEXAMPLE"
}
```

### 8.2 Input reference

| Field | Type | Required | Purpose / validation |
|---|---|---:|---|
| `message` | string | Yes | User's request; enforce length limits |
| `thread_id` | string or null | No | Conversation reference; verify ownership |
| `response_mode` | enum | No | `concise`, `balanced`, `detailed` |
| `output_format` | enum | No | `text`, `markdown`, `structured` |
| `agent_hint` | enum or null | No | Optional routing preference; supervisor may override |
| `timezone` | IANA timezone | No | Formatting and scheduling preference; validate |
| `locale` | string | No | Language and regional formatting preference |
| `include_sources` | boolean | No | Include citations for knowledge-grounded answers |
| `attachments` | array | No | Server-issued file IDs, not arbitrary filesystem paths |
| `context` | object | No | Allow-listed workflow parameters only |
| `client_request_id` | string | No | Idempotency/correlation identifier for request handling |

**Never accept these as trusted client inputs:** `user_id`, `workspace_id`, roles, permissions, OAuth tokens, approval status, or an assertion that an action has been approved. The server derives identity and authorization from the authenticated session and persisted records.

### 8.3 Example response

```json
{
  "thread_id": "thread_01JEXAMPLE",
  "workflow_id": "workflow_01JEXAMPLE",
  "status": "waiting_for_approval",
  "selected_agent": "planning",
  "message": "I found three follow-up tasks. Review them before I create them.",
  "data": {
    "proposed_actions": [
      {
        "action_id": "action_01",
        "tool": "create_task",
        "title": "Share project status report",
        "due_date": "2026-11-12"
      }
    ]
  },
  "approval_request_id": "approval_01JEXAMPLE",
  "sources": [],
  "metrics": {
    "duration_ms": 1840
  }
}
```

This is a proposed API contract, not a claim that the current application returns these exact fields.

## 9. Database schema

The following logical schema is a production-oriented starting point. Adjust types, indexes, retention, and relationships to match the implementation and selected providers.

### 9.1 Entity relationship diagram

```mermaid
erDiagram
    USERS ||--o{ WORKSPACE_MEMBERS : joins
    WORKSPACES ||--o{ WORKSPACE_MEMBERS : contains
    USERS ||--o{ OAUTH_CONNECTIONS : connects
    WORKSPACES ||--o{ CONVERSATIONS : owns
    USERS ||--o{ CONVERSATIONS : starts
    CONVERSATIONS ||--o{ MESSAGES : contains
    WORKSPACES ||--o{ TASKS : contains
    USERS ||--o{ TASKS : assigned_to
    WORKSPACES ||--o{ DOCUMENTS : contains
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : splits_into
    USERS ||--o{ APPROVALS : requests
    APPROVALS ||--o{ AUDIT_EVENTS : records
    USERS ||--o{ AUDIT_EVENTS : performs
    CONVERSATIONS ||--o{ WORKFLOWS : tracks
    WORKFLOWS ||--o{ APPROVALS : pauses_for

    USERS {
      uuid id PK
      text email UK
      text display_name
      timestamptz created_at
    }
    WORKSPACES {
      uuid id PK
      text name
      timestamptz created_at
    }
    WORKSPACE_MEMBERS {
      uuid id PK
      uuid workspace_id FK
      uuid user_id FK
      text role
      timestamptz joined_at
    }
    OAUTH_CONNECTIONS {
      uuid id PK
      uuid user_id FK
      text provider
      text provider_account_id
      bytea encrypted_refresh_token
      text scopes
      timestamptz expires_at
    }
    CONVERSATIONS {
      uuid id PK
      uuid workspace_id FK
      uuid user_id FK
      text title
      timestamptz created_at
    }
    MESSAGES {
      uuid id PK
      uuid conversation_id FK
      text role
      jsonb content
      timestamptz created_at
    }
    WORKFLOWS {
      uuid id PK
      uuid conversation_id FK
      text status
      text workflow_type
      jsonb metadata
      timestamptz created_at
    }
    TASKS {
      uuid id PK
      uuid workspace_id FK
      uuid assignee_id FK
      text title
      text status
      text priority
      date due_date
      timestamptz created_at
    }
    DOCUMENTS {
      uuid id PK
      uuid workspace_id FK
      uuid uploaded_by FK
      text filename
      text storage_key
      text access_policy
      text ingestion_status
      timestamptz created_at
    }
    DOCUMENT_CHUNKS {
      uuid id PK
      uuid document_id FK
      integer chunk_index
      text content
      jsonb metadata
      text vector_reference
    }
    APPROVALS {
      uuid id PK
      uuid workflow_id FK
      uuid requested_by FK
      uuid decided_by FK
      text status
      text action_hash
      jsonb action_payload
      timestamptz expires_at
      timestamptz decided_at
    }
    AUDIT_EVENTS {
      uuid id PK
      uuid actor_user_id FK
      uuid approval_id FK
      text event_type
      text resource_type
      text resource_id
      jsonb metadata
      timestamptz created_at
    }
```

### 9.2 PostgreSQL DDL starter

This SQL is a starter schema, not a complete migration. Add migrations, foreign-key policies, indexes, constraints, and tenant-isolation enforcement before production use.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, user_id)
);

CREATE TABLE oauth_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    provider_account_id TEXT NOT NULL,
    encrypted_refresh_token BYTEA NOT NULL,
    encrypted_access_token BYTEA,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, provider, provider_account_id)
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'waiting_for_approval', 'completed', 'failed', 'cancelled')),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    assignee_id UUID REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date DATE,
    source_reference JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type TEXT,
    access_policy JSONB NOT NULL DEFAULT '{}',
    ingestion_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    vector_reference TEXT,
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES users(id),
    decided_by UUID REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired', 'cancelled')),
    action_type TEXT NOT NULL,
    action_hash TEXT NOT NULL,
    action_payload JSONB NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id UUID REFERENCES users(id),
    workspace_id UUID REFERENCES workspaces(id),
    approval_id UUID REFERENCES approvals(id),
    event_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_workspace_status ON tasks(workspace_id, status);
CREATE INDEX idx_tasks_assignee_due ON tasks(assignee_id, due_date);
CREATE INDEX idx_conversations_workspace_user ON conversations(workspace_id, user_id);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX idx_documents_workspace ON documents(workspace_id);
CREATE INDEX idx_approvals_status_expiry ON approvals(status, expires_at);
CREATE INDEX idx_audit_workspace_created ON audit_events(workspace_id, created_at DESC);
```

**Schema notes:**

- Store LangGraph checkpoint data using the supported PostgreSQL checkpointer schema/migrations for the installed package version; do not hand-roll checkpoint tables.
- Consider PostgreSQL Row-Level Security (RLS) for tenant-owned tables, with a trusted transaction-scoped workspace/user context.
- Store provider secrets encrypted using a managed key. The DDL's `BYTEA` column is not encryption by itself.
- Use a vector database or PostgreSQL vector extension for embeddings. `vector_reference` is an abstract pointer in this starter schema.
- Add retention, deletion, export, and backup policies for conversations, documents, tokens, and audit records.

## 10. API design

The following endpoints are a proposed API surface. Keep only implemented endpoints in the live OpenAPI contract.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/ready` | Dependency readiness check |
| POST | `/api/v1/chat` | Submit a message / start or continue a workflow |
| GET | `/api/v1/conversations/{id}` | Get an authorized conversation |
| GET | `/api/v1/workflows/{id}` | Inspect workflow status |
| POST | `/api/v1/approvals/{id}/decision` | Approve or reject a pending action |
| GET | `/api/v1/approvals` | List approvals for current user/workspace |
| GET/POST | `/api/v1/tasks` | List or create tasks |
| PATCH/DELETE | `/api/v1/tasks/{id}` | Update or delete an authorized task |
| POST | `/api/v1/documents` | Upload a document for ingestion |
| GET | `/api/v1/documents/{id}` | Get authorized document metadata/status |
| POST | `/api/v1/integrations/{provider}/connect` | Start provider OAuth connection |
| DELETE | `/api/v1/integrations/{provider}/{id}` | Revoke/unlink a provider connection |
| GET | `/api/v1/usage` | Read authorized usage and cost summaries |

Use consistent error responses with safe public messages and correlation IDs. Do not return stack traces, tokens, or internal provider errors to clients.

## 11. Security and approval model

### 11.1 Security requirements

- Authenticate every non-public API request.
- Resolve user and workspace membership on the server.
- Enforce role and resource-level authorization for every read and write.
- Apply tenant filters to database queries, vector retrieval, and tool execution.
- Keep secrets in a secret manager or encrypted credential store.
- Validate uploaded file type, size, content, and access policy.
- Rate-limit expensive model and integration endpoints.
- Use least-privilege OAuth scopes and support token revocation.
- Redact secrets and sensitive personal data from logs and traces.
- Treat prompts, retrieved documents, emails, and tool outputs as untrusted input.

### 11.2 Approval integrity

An approval record should be bound to:

- Authenticated requesting user and workspace.
- Exact tool name and normalized arguments.
- A cryptographic hash of the approved action payload.
- Approval expiry and current workflow state.
- A unique idempotency key.
- The identity of the approving user and the decision timestamp.

At execution time, the server must re-check permissions, expiry, approval status, action hash, and idempotency state. A model-generated `approved: true` value is never sufficient authorization.

### 11.3 Safe execution lifecycle

```mermaid
stateDiagram-v2
    [*] --> Proposed
    Proposed --> Validating
    Validating --> Rejected: Invalid / unauthorized
    Validating --> Ready: Read-only or policy permits
    Validating --> AwaitingApproval: Sensitive action
    AwaitingApproval --> Approved: Authorized approver accepts
    AwaitingApproval --> Rejected: Approver rejects
    AwaitingApproval --> Expired: Approval timeout
    Approved --> Executing: Revalidate action and idempotency
    Ready --> Executing
    Executing --> Completed: Provider confirms success
    Executing --> RetryableFailure: Transient failure
    RetryableFailure --> Executing: Safe retry
    Executing --> Failed: Permanent failure
    Completed --> [*]
    Rejected --> [*]
    Expired --> [*]
    Failed --> [*]
```

## 12. Evaluation and production targets

The following are **proposed acceptance targets**, not measured project results. Publish actual scores only after running a reproducible evaluation suite and recording the dataset version, model, configuration, and date.

| Area | Metric | Initial target |
|---|---|---:|
| Routing | Correct agent selection | ≥95% |
| Workflow | Successful completion on supported scenarios | ≥90% initially; improve with testing |
| Tool execution | Successful authorized tool calls | ≥98% |
| RAG | Recall@5 | ≥90% |
| RAG | MRR@10 | ≥0.75 |
| RAG | Faithfulness | ≥90% |
| Safety | Unauthorized sensitive actions in test suite | 0 |
| Safety | Approval validation test pass rate | 100% |
| Reliability | Duplicate side effects in retry tests | 0 |
| Retrieval | p95 retrieval latency | ≤1.5 seconds on defined test environment |
| API | p95 latency for simple non-agent health/API operations | Set baseline, then define SLO |
| Operations | Workflow recovery test success | ≥95% |

### 12.1 Evaluation datasets

Create version-controlled datasets for:

- **Routing:** user request, expected agent, ambiguity label, and expected clarification behavior.
- **RAG:** question, expected answer, relevant document/chunk IDs, and answerability label.
- **Tool use:** user request, expected tool, valid argument schema, and expected result.
- **Safety:** unauthorized user, cross-tenant access, prompt injection, destructive actions, expired approvals, altered payloads, and duplicate retries.
- **Workflow recovery:** failure point, checkpoint state, expected resumed step, and duplicate-side-effect assertion.

### 12.2 Evaluation metrics

- Classification accuracy, precision, recall, and confusion matrix for routing.
- Recall@K, Precision@K, MRR, and nDCG for retrieval.
- Faithfulness, answer relevance, and citation correctness for generated answers.
- Tool selection accuracy, argument validity, and execution success for tool use.
- p50/p95/p99 latency, token usage, retries, failure rate, and cost per completed workflow.
- Security tests for tenant isolation, authorization, approval integrity, and replay protection.

## 13. Observability and cost management

Capture one trace per user request and link child spans for:

- Authentication and request validation (without logging secrets).
- Supervisor routing decision and selected agent.
- LLM provider/model, latency, token usage, and retry count.
- Retrieval query, filters, candidate counts, reranking, and source IDs.
- Tool name, sanitized arguments, provider latency, result status, and idempotency key.
- Approval requested/decided/expired events.
- Workflow checkpoint, resume, completion, and failure.

Recommended stack: OpenTelemetry for vendor-neutral traces and metrics; LangSmith where useful for LangGraph-specific debugging and evaluations; Prometheus/Grafana for operational metrics if required. Define retention and redaction policies before enabling production tracing.

### Suggested operational dashboard

| Dashboard panel | What it answers |
|---|---|
| Workflow volume | How many workflows are started and completed? |
| Completion and failure rate | Which workflows fail most often? |
| Agent routing | Are requests routed to the correct specialist? |
| Tool reliability | Which integration or tool fails? |
| Retrieval quality | Are relevant sources being found? |
| Latency | Which stage dominates p95 duration? |
| LLM cost | What is the cost per request and completed workflow? |
| Approval queue | Which actions are waiting, rejected, or expired? |
| Security events | Are there authorization failures or suspicious patterns? |

## 14. Technology stack

| Layer | Technologies |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI, Pydantic, Uvicorn |
| Agent orchestration | LangGraph, LangChain |
| Integrations | MCP, FastMCP, Gmail API, Google Calendar API |
| LLM providers | Configurable provider adapters (for example OpenAI or Groq) |
| RAG | Embeddings, BM25, hybrid retrieval, reranking |
| Relational data | PostgreSQL, SQLAlchemy, Alembic |
| Workflow state | LangGraph PostgreSQL checkpointer |
| Vector storage | Select one supported vector store / pgvector implementation |
| Cache / background jobs | Redis and a worker framework when required |
| Frontend (planned) | React, Next.js, TypeScript |
| Packaging | Docker, Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry |
| Testing | Pytest, HTTPX, evaluation datasets |
| Observability | OpenTelemetry, LangSmith; Prometheus/Grafana where needed |

Use only technologies that are actually present in the implementation when describing the project as completed.

## 15. Repository structure

A suggested repository layout (adapt it to the current codebase):

```text
workpilot-ai/
├── backend/
│   └── src/
│       ├── api/
│       │   ├── main.py
│       │   ├── routes/
│       │   ├── dependencies/
│       │   └── schemas/
│       ├── agents/
│       │   ├── supervisor.py
│       │   ├── task_agent.py
│       │   ├── knowledge_agent.py
│       │   ├── planning_agent.py
│       │   └── communication_agent.py
│       ├── graph/
│       │   ├── state.py
│       │   ├── workflow.py
│       │   ├── routing.py
│       │   └── approval.py
│       ├── rag/
│       │   ├── loader.py
│       │   ├── chunker.py
│       │   ├── embeddings.py
│       │   ├── indexing.py
│       │   ├── retrieval.py
│       │   └── reranker.py
│       ├── mcp/
│       │   ├── client.py
│       │   ├── tool_registry.py
│       │   ├── workpilot_mcp.py
│       │   └── google_mcp.py
│       ├── integrations/
│       │   ├── gmail.py
│       │   └── calendar.py
│       ├── security/
│       │   ├── authentication.py
│       │   ├── authorization.py
│       │   ├── secrets.py
│       │   └── tenant_context.py
│       ├── database/
│       │   ├── models.py
│       │   ├── session.py
│       │   └── migrations/
│       ├── services/
│       │   ├── approval_service.py
│       │   ├── audit_service.py
│       │   └── usage_service.py
│       ├── observability/
│       └── config/
├── frontend/                  # Planned React / Next.js application
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── evaluation/
│   └── fixtures/
├── evals/
│   ├── routing/
│   ├── rag/
│   ├── tool_use/
│   └── workflows/
├── infra/
│   ├── docker/
│   └── deployment/
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── evaluation.md
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .dockerignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE
```

## 16. Local development

### 16.1 Prerequisites

- Python 3.11 or newer.
- Git.
- A supported LLM provider API key.
- PostgreSQL for durable application data and production-like checkpointing.
- Optional Redis if background jobs or caching are enabled.
- Google Cloud OAuth credentials if Gmail/Calendar integrations are enabled.

### 16.2 Clone and create an environment

```bash
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY

python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 16.3 Configure environment variables

Create a local `.env` file based on `.env.example`. Never commit `.env`, OAuth credentials, or token files.

```dotenv
APP_NAME=WorkPilot AI
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

LLM_PROVIDER=groq
LLM_MODEL=your-model-name
LLM_API_KEY=replace-with-your-secret

DATABASE_URL=postgresql+psycopg://workpilot:change-me@localhost:5432/workpilot
REDIS_URL=redis://localhost:6379/0

# Configure OAuth using your provider's registered application.
GOOGLE_CLIENT_ID=replace-me
GOOGLE_CLIENT_SECRET=replace-me
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

# Use a managed secret in deployed environments; this is only a placeholder.
TOKEN_ENCRYPTION_KEY=replace-with-a-secure-key
```

The exact environment variable names must match the application's settings implementation. Do not use the sample values in a real deployment.

### 16.4 Run the API

Use the import path that matches the actual Python package structure. For the suggested layout above:

```bash
uvicorn backend.src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open the FastAPI docs at `http://127.0.0.1:8000/docs` when running locally.

## 17. Docker deployment

### 17.1 Build and run

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

Stop the services:

```bash
docker compose down
```

Remove persisted development volumes only when you intentionally want to delete their data:

```bash
docker compose down -v
```

### 17.2 Example Dockerfile

Adapt the module path and OS dependencies to the repository and packages you actually use.

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

RUN useradd --create-home appuser \
    && mkdir -p /app/backend/data \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "backend.src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 17.3 Example Docker Compose

For local development only; production secrets should be injected by the deployment platform or a secret manager.

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: workpilot
      POSTGRES_USER: workpilot
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U workpilot -d workpilot"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

For a real deployment, pin image versions/digests, configure private networking, TLS, resource limits, backups, health checks, and secret injection. Add a worker service only after the worker entry point has been implemented.

## 18. CI/CD

A GitHub Actions pipeline should validate code before building and publishing a container image.

Recommended pipeline stages:

1. Install dependencies from a locked and reviewed dependency set.
2. Run formatting, linting, and static checks.
3. Run unit and integration tests.
4. Run security and authorization tests.
5. Run a small deterministic evaluation smoke suite.
6. Build the Docker image.
7. Scan dependencies and the container image.
8. Publish immutable commit-tagged images after protected-branch checks.
9. Deploy to staging, run smoke tests, then promote to production with approval.

Example minimal workflow (adjust test commands and package paths):

```yaml
name: WorkPilot AI CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest httpx

      - name: Compile Python files
        run: python -m compileall -q backend

      - name: Run tests
        run: pytest -q

      - name: Build Docker image
        run: docker build -t workpilot-ai:${{ github.sha }} .
```

For publishing to GHCR, add a separate protected-branch job with `packages: write`, use `GITHUB_TOKEN`, and publish both an immutable commit SHA tag and an optional release tag. Do not publish secrets in build arguments or image layers.

## 19. Testing strategy

| Test layer | What to test | Example |
|---|---|---|
| Unit | Pure functions, schemas, routing logic | Invalid route is rejected |
| API | Request validation and response contracts | Missing message returns 422 |
| Agent | Tool selection and bounded behavior | Task request selects Task Agent |
| RAG | Retrieval and citation behavior | Expected document appears in top 5 |
| Integration | Database and provider adapters | OAuth connection lookup is user-scoped |
| Security | Authentication, authorization, tenant isolation | User A cannot read User B's document |
| Approval | Action binding, expiry, approver permissions | Altered action hash cannot execute |
| Idempotency | Retries and duplicate requests | Same key does not send twice |
| Recovery | Checkpoint and workflow resume | Interrupted graph resumes safely |
| Evaluation | Routing, RAG, tool-use benchmark | Regression thresholds are enforced |

### Minimum security test cases

- Unauthenticated requests cannot access protected resources.
- A user cannot access another workspace's task, conversation, document, or approval.
- A client cannot impersonate another user by changing `user_id` in JSON.
- An expired, rejected, or altered approval cannot execute.
- Replaying an already completed action does not duplicate the side effect.
- Prompt injection inside a retrieved document cannot override system or tool policies.
- OAuth credentials never appear in logs, model prompts, or API responses.

## 20. Roadmap

### P0 — Secure and durable foundation

- [ ] Multi-user authentication and authorization.
- [ ] Workspace and tenant isolation across database, RAG, and tools.
- [ ] PostgreSQL application persistence.
- [ ] PostgreSQL-backed LangGraph checkpointer.
- [ ] Approval integrity, expiry, and idempotency.
- [ ] Audit events for tool execution and approvals.
- [ ] Secure OAuth credential storage and revocation.
- [ ] Workflow recovery and retry tests.

### P1 — Intelligence and evaluation

- [ ] Reusable agent skills and workflow templates.
- [ ] User preference memory with user controls.
- [ ] Hybrid retrieval with BM25 and dense search.
- [ ] Reranking and source-grounded answers.
- [ ] Versioned RAG and routing evaluation datasets.
- [ ] Automated evaluation pipeline in CI.
- [ ] LangSmith and/or OpenTelemetry traces.
- [ ] Token, latency, failure, and cost monitoring.
- [ ] Daily briefing and meeting preparation routines.

### P2 — Product experience and scale

- [ ] React/Next.js dashboard.
- [ ] Approval inbox and workflow history.
- [ ] Redis caching and background workers.
- [ ] Model routing and provider fallback.
- [ ] Usage and cost dashboard.
- [ ] Additional integrations such as Microsoft 365.
- [ ] Deployment automation, dashboards, and alerting.

## 21. Engineering principles

1. **Security outside the prompt:** authorization is enforced in trusted application code and tool wrappers.
2. **Least privilege:** each tool receives only the permissions and credentials it needs.
3. **No fabricated outcomes:** agents report tool results, not assumed success.
4. **Idempotent side effects:** retries must not create duplicate external actions.
5. **Persisted state:** interrupted workflows can resume from a durable checkpoint.
6. **Grounded answers:** knowledge responses cite retrieved sources and acknowledge missing evidence.
7. **Observable execution:** every workflow has a traceable lifecycle and sanitized audit events.
8. **Measured improvements:** publish benchmark results with methodology and dataset versions.
9. **Human control:** sensitive actions remain reviewable and revocable.
10. **Incremental delivery:** keep the core system small and add complexity only when supported by a demonstrated requirement.

## 22. Contributing

Contributions are welcome. Before opening a pull request:

1. Create a focused branch.
2. Add or update tests for behavior changes.
3. Run formatting, linting, tests, and relevant evaluations.
4. Update documentation and example environment variables.
5. Ensure no credentials, personal data, or generated secrets are committed.
6. Describe security and migration implications for changes affecting tools, permissions, or data models.

## License

Choose and add a license before distributing this project. Until a license file is added, all rights remain with the copyright holder by default.

---

<p align="center">
  <strong>WorkPilot AI</strong><br />
  <em>Understand work. Plan work. Execute work—securely.</em>
</p>
