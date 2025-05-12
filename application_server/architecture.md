```mermaid
graph TB
    %% Define styles
    classDef primary fill:#4285F4,stroke:#2956A8,color:white;
    classDef secondary fill:#34A853,stroke:#23732A,color:white;
    classDef tertiary fill:#FBBC05,stroke:#A67C00,color:black;
    classDef accent fill:#EA4335,stroke:#BB3023,color:white;
    
    %% User interaction
    User([User]):::accent --> |1. Uploads PDF| Streamlit
    
    %% Frontend
    subgraph "Frontend (Streamlit)"
        Streamlit[Streamlit Web App]:::primary
        StreamUI[User Interface]:::primary
        StreamAPI[API Client]:::primary
        
        Streamlit --> StreamUI
        Streamlit --> StreamAPI
    end
    
    %% Backend
    subgraph "Backend (FastAPI)"
        API[FastAPI Server]:::secondary
        Upload[Upload Endpoint]:::secondary
        Status[Status Endpoint]:::secondary
        Reports[Reports Endpoint]:::secondary
        Process[Background Processing]:::secondary
        Storage[File Storage]:::secondary
        
        API --> Upload
        API --> Status
        API --> Reports
        Upload --> Process
        Process --> Storage
    end
    
    %% Core Processing
    subgraph "Core Processing"
        PDFExtractor[PDF Extractor]:::tertiary
        AIAnalyzer[AI Analyzer]:::tertiary
        ReportGen[Report Generator]:::tertiary
        
        Process --> PDFExtractor
        PDFExtractor --> AIAnalyzer
        AIAnalyzer --> ReportGen
        ReportGen --> Storage
    end
    
    %% External Services
    GoogleAI[Google Vertex AI]:::accent
    AIAnalyzer --> |AI Analysis| GoogleAI
    
    %% API Communication
    StreamAPI --> |2. POST /upload/| Upload
    StreamAPI --> |3. GET /status/{job_id}| Status
    StreamAPI --> |5. GET /report/{job_id}| Reports
    Reports --> |6. Return Report| StreamAPI
    
    %% Display to user
    StreamUI --> |4. Show Status| User
    StreamUI --> |7. Display Report| User
```

This diagram visualizes the client-server architecture for the TIBCO Case Audit application, showing the data flow between the Streamlit frontend and FastAPI backend, as well as the core processing components. 