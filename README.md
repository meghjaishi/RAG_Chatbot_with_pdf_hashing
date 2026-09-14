# Personal Multi-Document RAG Chatbot

### 🌐 [View Live Frontend Demo](https://meghjaishi.github.io/RAG_Chatbot_with_pdf_hashing/)
A production-oriented Retrieval-Augmented Generation (RAG) application
for asking questions over a collection of PDF documents. The project
evolved from a Streamlit prototype into a FastAPI backend with
JWT-protected endpoints and a React + TypeScript frontend with
token-by-token SSE streaming.

The system includes incremental PDF ingestion using file hashing,
Pinecone vector search, OpenAI embeddings and generation,
conversation-aware query rewriting, context budgeting, structured
logging, retrieval evaluation, and RAGAS-based end-to-end evaluation.

## Features

-   Multi-document PDF ingestion and retrieval
-   Incremental ingestion using SHA/file hashing and a persistent
    manifest
-   Stable chunk metadata and deterministic vector IDs
-   OpenAI `text-embedding-3-large` embeddings
-   Pinecone serverless vector database with cosine similarity
-   LangChain-based document loading, splitting, vector-store
    integration, and retrieval
-   Similarity-score-threshold retrieval
-   Conversation history for follow-up questions
-   Query rewriting for context-dependent questions
-   Context token budgeting before generation
-   Grounded fallback when no relevant documents are retrieved
-   Non-streaming FastAPI `/chat` endpoint
-   Streaming FastAPI `/chat/stream` endpoint using Server-Sent Events
    (SSE)
-   JWT bearer authentication
-   Structured JSON logging with request IDs and timing information
-   React + Vite + TypeScript frontend
-   Token-by-token streaming, automatic scrolling, session-expiration
    handling, and responsive chat UI
-   Original Streamlit frontend retained as an alternative interface
-   Retrieval evaluation with Precision, Recall, Hit Rate, and MRR
-   RAGAS evaluation for faithfulness, answer relevancy, context
    precision, and context recall

## Architecture

``` text
                         PDF Documents
                              |
                              v
                     +------------------+
                     |   ingest.py      |
                     | hashing.py       |
                     +------------------+
                              |
                 Load -> Split -> Embed
                              |
                              v
                    +-------------------+
                    |     Pinecone      |
                    |   Vector Index    |
                    +-------------------+
                              |
                              v
User Question -> Conversation History -> Query Rewriting
                              |
                              v
                    Similarity Retrieval
                              |
                              v
                    Context Token Budget
                              |
                              v
                       RAG Prompt
                              |
                              v
                       OpenAI LLM
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          FastAPI Backend          Streamlit Frontend
          /chat + /chat/stream      Original prototype
                 |
                 v
       React + TypeScript Frontend
       JWT + SSE token streaming
```

The Streamlit application and React/FastAPI application use the same
underlying RAG pipeline. FastAPI provides the production-style API
boundary, while Streamlit remains a useful lightweight interface for
local experimentation and debugging.

## Technology Stack

### Backend and RAG

-   Python 3.12
-   FastAPI
-   LangChain
-   OpenAI
-   Pinecone
-   PyPDF
-   Pydantic
-   Uvicorn

### Authentication

-   PyJWT
-   `pwdlib[argon2]`
-   `python-multipart`
-   OAuth2 password/bearer flow

### Frontends

-   React
-   TypeScript
-   Vite
-   Streamlit

### Evaluation

-   Custom information-retrieval evaluation
-   RAGAS 0.4.x

## Project Structure

A representative project layout is:

``` text
RAG_Chatbot_with_pdf_hashing/
|
|-- api/
|   |-- __init__.py
|   |-- main.py
|   |-- request_context.py
|   `-- auth/
|       |-- __init__.py
|       |-- models.py
|       |-- router.py
|       `-- security.py
|
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |   |-- auth.ts
|   |   |   `-- chat.ts
|   |   |-- components/
|   |   |   |-- LoginForm.tsx
|   |   |   `-- ChatWindow.tsx
|   |   |-- types/
|   |   |   `-- api.ts
|   |   |-- App.tsx
|   |   `-- App.css
|   |-- .env
|   `-- package.json
|
|-- Documents/
|-- app.py
|-- config.py
|-- hashing.py
|-- ingest.py
|-- manifest.json
|-- models.py
|-- prompts.py
|-- rag.py
|-- .env
`-- README.md
```

The exact supporting evaluation/logging file names may vary as the
project evolves.

## RAG Pipeline

The core question-answering flow is:

``` text
Question
   |
   v
Conversation-aware query rewriting
   |
   v
Pinecone retrieval
   |
   v
Similarity threshold filtering
   |
   v
Context selection / token budgeting
   |
   v
Prompt construction
   |
   v
LLM generation
   |
   v
Answer + retrieved document metadata
```

### Retrieval

The Pinecone vector store is exposed through a LangChain retriever using
similarity-score-threshold search.

A typical configuration is:

``` python
self.retriever = self.vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": self.k,
        "score_threshold": self.score_threshold,
    },
)
```

The production configuration uses a small top-k retrieval set (`k=3`)
and a calibrated relevance threshold. During evaluation, a threshold
around `0.65` provided useful separation between supported and unrelated
questions.

> Pinecone's raw cosine scores and LangChain's normalized relevance
> scores are not necessarily numerically identical. Threshold
> calibration should therefore be performed against the score
> representation used by the application.

### Conversation History and Query Rewriting

The application supports follow-up questions by passing previous
user/assistant turns into the RAG pipeline.

For example:

``` text
User: What is reinforcement learning used for?
Assistant: ...

User: How does it differ from supervised learning?
```

The second question can be rewritten using conversation context before
retrieval so that the retriever receives a self-contained search query.

The current question is sent separately from `history`; it is not
duplicated in the history array.

### Context Token Budgeting

Retrieved documents are selected within a context budget before the
final prompt is sent to the model. This prevents an uncontrolled number
of retrieved chunks from consuming the model context window.

### Grounded Abstention

When retrieval produces no sufficiently relevant documents, the
application returns:

``` text
I don't know based on the provided documents.
```

This is intentional. The RAG application should abstain rather than
answer an unsupported question from general model knowledge.

## PDF Ingestion

PDFs are loaded page-by-page and split using
`RecursiveCharacterTextSplitter`.

Representative configuration:

``` python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=SEPARATORS,
)
```

Current text-splitting configuration:

``` text
CHUNK_SIZE = 600
CHUNK_OVERLAP = 200
```

Each chunk receives metadata such as:

``` python
{
    "source_file": pdf_path.name,
    "relative_path": ...,
    "chunk": index,
    "file_hash": file_hash,
}
```

The metadata supports source tracking, evaluation, and deterministic
identification of chunks.

## Incremental Ingestion and PDF Hashing

Re-embedding every PDF on every ingestion run is unnecessary and
expensive. The project therefore hashes documents and maintains a
persistent `manifest.json`.

Conceptually:

``` text
PDF
 |
 v
Calculate file hash
 |
 +---- hash already in manifest and unchanged? ---- Yes ---> Skip
 |
 No
 |
 v
Load PDF
 |
 v
Split into chunks
 |
 v
Generate embeddings
 |
 v
Upload to Pinecone
 |
 v
Update in-memory manifest
 |
 v
Persist manifest.json
```

The manifest passed between hashing functions is an in-memory Python
dictionary. Updating the manifest modifies that dictionary; saving the
manifest serializes the complete dictionary to `MANIFEST_FILE`.

### Deterministic Vector IDs

Uploaded chunks use IDs based on the document hash and chunk position,
for example:

``` python
ids = [
    f"{doc.metadata['file_hash']}_{i}"
    for i, doc in enumerate(documents)
]
```

The human-facing `chunk` metadata is 1-based, while the vector-ID
enumeration may be 0-based.

## FastAPI Backend

The FastAPI layer provides both standard and streaming access to the
same RAG pipeline.

Start the API from the project root:

``` bash
uvicorn api.main:app --reload
```

Typical local address:

``` text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

``` text
http://127.0.0.1:8000/docs
```

### Non-Streaming Chat

``` text
POST /chat
```

The request contains the current question and optional conversation
history.

Conceptually:

``` json
{
  "question": "What is reinforcement learning used for?",
  "history": []
}
```

The response contains the generated answer together with
retrieval/document metadata and timing information.

### Streaming Chat

``` text
POST /chat/stream
```

The endpoint streams SSE events. A token event has the form:

``` text
data: {"event":"token","data":"Reinforcement"}
```

Additional event types can carry completion or metadata information. A
completion event can include fields such as request ID, documents found,
retrieval time, and generation time.

The frontend parses the SSE wrapper first and appends only events where:

``` typescript
event.event === "token"
```

and `event.data` is a string. This prevents metadata or completion
objects from being rendered as `[object Object]`.

## Authentication

The FastAPI endpoints are protected using JWT bearer authentication.

The authentication stack uses:

-   OAuth2 password form login
-   Argon2 password hashing
-   PyJWT
-   Bearer tokens
-   JWT `sub` and `exp` claims

Login endpoint:

``` text
POST /auth/login
```

A successful response has the form:

``` json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

The access token is sent to protected endpoints as:

``` text
Authorization: Bearer <token>
```

The development implementation uses an in-memory test user. For a
deployed multi-user system, this should be replaced by persistent user
storage and an appropriate account-management workflow.

### Session Expiration

The React frontend stores the access token in `sessionStorage`.

When the API returns `401` because a token has expired or is invalid:

1.  the API client removes the stored token;
2.  the chat component reports session expiration to `App.tsx`;
3.  application authentication state is cleared; and
4.  the login form is displayed again.

This keeps browser storage and React state synchronized.

## React Frontend

The final frontend is implemented with React, Vite, and TypeScript.

Start it from the frontend directory:

``` bash
cd frontend
npm install
npm run dev
```

Example frontend environment configuration:

``` env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The FastAPI application must allow the frontend development origins
through CORS.

### Streaming Implementation

The React application uses `fetch()` plus `ReadableStream` instead of
native `EventSource`.

This is intentional because authenticated requests require a custom
`Authorization: Bearer ...` header, which is inconvenient with the
standard browser `EventSource` API.

The stream reader:

1.  reads response bytes;
2.  decodes them with `TextDecoder`;
3.  buffers incomplete SSE frames;
4.  separates events at blank lines;
5.  parses the JSON in each `data:` field;
6.  sends complete `StreamEvent` objects to the UI; and
7.  appends only token-event string data to the assistant message.

### Conversation UX

The final React UI includes:

-   separate user and assistant message bubbles;
-   responsive chat layout;
-   loading/generating state;
-   error display;
-   disabled input while generation is active;
-   automatic scrolling as streamed tokens arrive;
-   conversation history for follow-up questions;
-   JWT login/logout;
-   automatic return to login after session expiration.

## Streamlit Frontend

The project originally used Streamlit as its primary frontend before the
FastAPI + React interface was added.

Run the Streamlit application from the project root:

``` bash
streamlit run app.py
```

The Streamlit interface was important during development because it
provided a fast way to exercise the RAG pipeline without building a
separate web client.

It supports the same general RAG workflow:

``` text
User question
     |
     v
Streamlit session state
     |
     v
Conversation history
     |
     v
RAG pipeline
     |
     +--> retrieval
     +--> prompt construction
     +--> generation
     |
     v
Answer displayed in Streamlit
```

Conversation messages are maintained in Streamlit session state,
allowing follow-up questions to use prior context.

The Streamlit implementation also participates in request-context
logging by assigning a request ID for a user interaction and resetting
the context afterward.

### Why Keep Streamlit?

The React frontend does not make Streamlit obsolete. The two interfaces
serve different purposes.

**Streamlit is useful for:**

-   rapid local experimentation;
-   RAG pipeline debugging;
-   testing retrieval/generation changes;
-   inspecting behavior without running the React development server;
-   demonstrations where a separate API client is unnecessary.

**React + FastAPI is useful for:**

-   clearer frontend/backend separation;
-   API-first architecture;
-   JWT-protected access;
-   custom streaming behavior;
-   richer UI/UX;
-   easier evolution toward a production web application.

Therefore, FastAPI was introduced as an **alternative production-style
interface rather than a replacement for Streamlit**.

## Structured Logging and Request IDs

The API uses structured JSON logging and a `ContextVar` request ID.

A request ID allows logs generated by retrieval, generation, and API
handling to be associated with the same request.

Logged information can include:

-   request ID;
-   retrieval duration;
-   generation duration;
-   number of retrieved documents;
-   model usage;
-   estimated cost;
-   completion status.

This makes debugging and performance analysis significantly easier than
relying on unstructured print statements.

## Evaluation

The project evaluates the RAG system at two different levels:

1.  **information-retrieval evaluation**, which measures whether the
    retriever finds the expected chunks; and
2.  **RAGAS evaluation**, which evaluates properties of the final RAG
    response and supplied contexts.

Keeping both is useful because exact chunk-level labels and semantic
answer-level evaluation measure different things.

### Evaluation Corpus

The evaluation corpus includes three papers:

-   `Deep_RL.pdf` - DeepMind DQN / deep reinforcement learning
-   `Meta_Learning.pdf` - Model-Agnostic Meta-Learning (MAML)
-   `World_Models.pdf` - World Models

A 30-question dataset covers:

-   Deep RL questions;
-   MAML questions;
-   cross-document questions;
-   unsupported questions; and
-   World Models questions.

### Human Chunk Labels

Retrieved chunks were annotated as:

``` text
relevant
partially relevant
irrelevant
```

Two ground-truth interpretations are useful:

``` text
Strict  = relevant only
Lenient = relevant + partially relevant
```

The lenient interpretation is the primary retrieval baseline because
overlapping chunks can make exact chunk-level relevance sparse even when
the retrieved context semantically contains the answer.

### Retrieval Baseline

The recorded lenient baseline was approximately:

  Metric                               Score
  --------------------------------- --------
  Precision@1                         0.3333
  Precision@3                         0.2593
  Recall@1                            0.1481
  Recall@3                            0.2932
  Hit@1                               0.3333
  Hit@3                               0.5556
  MRR                                 0.4444
  Unsupported-question abstention     1.0000

One implementation detail to note when comparing these numbers with
external benchmarks: the current precision calculation divides by the
number of documents actually returned rather than always dividing by the
requested K.

### RAGAS

RAGAS 0.4.x is used for end-to-end evaluation with metrics including:

-   Faithfulness
-   Answer Relevancy
-   Context Precision
-   Context Recall

Example smoke-test results:

  -----------------------------------------------------------------------
  Question      Faithfulness         Answer        Context Context Recall
                                  Relevancy      Precision 
  ----------- -------------- -------------- -------------- --------------
  q01                 0.9231         0.8645         0.5000         1.0000

  q02                 1.0000       \~1.0000         0.5833         1.0000
  -----------------------------------------------------------------------

RAGAS evaluation is substantially slower than the custom retrieval
metrics, so it is currently used as a targeted end-to-end evaluation
rather than as a mandatory full-suite run during every development
iteration.

An important observation from evaluation was that a question could
receive low exact-chunk recall under sparse human labels while RAGAS
still judged the supplied context sufficient to answer it. This
reinforces the value of retaining both retrieval-level and semantic RAG
evaluation.

## Configuration

The application reads configuration from environment variables and
`config.py`.

Typical environment variables include values for:

``` env
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Use the exact variable names defined by your current
`config.py`/authentication configuration if they differ.

**Never commit real API keys or JWT secrets to source control.**

A useful repository pattern is:

``` text
.env
.env.example
```

where `.env` is ignored by Git and `.env.example` documents required
variable names without containing secrets.

## Installation

### Python Environment

From the project root, create/activate your Python environment using
your preferred environment manager.

If the project is managed with `uv`, install/sync the dependencies from
the project configuration/lock file.

For authentication, the project uses packages equivalent to:

``` text
pyjwt
pwdlib[argon2]
python-multipart
```

On macOS, if native dependency compilation incorrectly resolves to an
old Homebrew LLVM/Clang installation, Xcode's compiler can be selected
explicitly when adding dependencies:

``` bash
CC="$(xcrun --find clang)" \
CXX="$(xcrun --find clang++)" \
uv add pyjwt "pwdlib[argon2]" python-multipart
```

### React Dependencies

``` bash
cd frontend
npm install
```

## Running the Application

### 1. Configure Environment Variables

Create the required `.env` files for the backend and frontend.

### 2. Add PDFs

Place documents in:

``` text
Documents/
```

### 3. Run Ingestion

Run the project's ingestion entry point:

``` bash
python ingest.py
```

Unchanged documents can be skipped using the hashing/manifest mechanism.

### 4. Start FastAPI

``` bash
uvicorn api.main:app --reload
```

### 5. Start React

In another terminal:

``` bash
cd frontend
npm run dev
```

Open the local URL reported by Vite.

### Alternative: Start Streamlit

Instead of the React UI, the original frontend can be run with:

``` bash
streamlit run app.py
```

This is particularly useful for local RAG experimentation.

## Development Verification

Before considering the application ready, the following behaviors should
be verified:

-   valid login succeeds;
-   invalid login fails cleanly;
-   `/chat` rejects unauthenticated requests;
-   `/chat` works with a valid JWT;
-   `/chat/stream` rejects unauthenticated requests;
-   `/chat/stream` streams correctly with a valid JWT;
-   invalid/expired JWTs return `401`;
-   the React UI returns to login after session expiration;
-   logout clears the session;
-   token streaming renders text rather than SSE wrapper objects;
-   long answers auto-scroll;
-   follow-up questions use conversation history;
-   unsupported questions abstain;
-   Streamlit can still exercise the RAG pipeline independently.

## Security Notes

The current authentication layer is appropriate for demonstrating
protected API access, but a production deployment should additionally
consider:

-   persistent user storage;
-   user registration/account lifecycle;
-   refresh-token strategy;
-   HTTPS;
-   secure deployment of secrets;
-   rate limiting;
-   authorization/roles where required;
-   token revocation strategy;
-   audit logging;
-   stricter production CORS configuration.

## Current Limitations

-   Authentication currently uses a development-oriented in-memory user
    rather than a persistent user database.
-   RAGAS evaluation is relatively slow and is not run exhaustively on
    every iteration.
-   Human chunk-level ground truth is intentionally limited and can be
    sparse because of overlapping text chunks.
-   Retrieval and generation quality still depend on chunking, threshold
    calibration, embeddings, document quality, and the selected LLM.
-   The React frontend focuses on a clean chat experience rather than a
    full document-management interface.
-   Streamlit and React provide separate UI paths; they are not intended
    to share browser session state.

## Future Improvements

Potential extensions include:

-   persistent user/account database;
-   refresh tokens;
-   role-based authorization;
-   document upload and ingestion from the web UI;
-   source/citation panels in the React frontend;
-   richer Markdown rendering for generated answers;
-   automated evaluation in CI/CD;
-   larger evaluation datasets;
-   reranking or hybrid retrieval;
-   improved retrieval observability;
-   Docker/container deployment;
-   cloud deployment;
-   automated tests for API, authentication, retrieval, and frontend
    behavior.

These are deliberately left as future improvements rather than being
required for the current project to be considered complete.

## Design Evolution

The project intentionally evolved in stages:

``` text
PDF ingestion
     |
     v
Vector retrieval
     |
     v
Basic RAG
     |
     v
Streamlit chatbot
     |
     v
PDF hashing + incremental ingestion
     |
     v
Conversation-aware RAG
     |
     v
FastAPI API
     |
     v
SSE streaming
     |
     v
Structured logging
     |
     v
Retrieval + RAGAS evaluation
     |
     v
JWT authentication
     |
     v
React + TypeScript frontend
     |
     v
Streaming UX + final UI polish
```

This progression keeps the RAG pipeline independent of any single
frontend and demonstrates the transition from a rapid prototype to a
more production-oriented application architecture.

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Meghnath Jaishi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.