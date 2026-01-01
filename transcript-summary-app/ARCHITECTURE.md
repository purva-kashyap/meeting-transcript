# Code Architecture

## Project Structure

```
transcript-summary-app/
├── app.py                      # Main Flask application (routes/controllers)
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
├── services/                  # Business logic layer (Facade pattern)
│   ├── __init__.py           # Services module
│   ├── zoom_service.py       # Zoom API integration
│   ├── graph_service.py      # Microsoft Graph API integration
│   └── llm_service.py        # LLM/summarization service
├── templates/                 # HTML templates
│   ├── home.html             # Home page
│   ├── meetings.html         # Meetings list page
│   └── summary.html          # Transcript & summary page
└── static/                    # Static files
    └── style.css             # Stylesheet
```

## Architecture Pattern

The application follows a **Facade Pattern** for service layer organization:

### 1. **app.py** - Controller Layer
- Handles HTTP requests/responses
- Routes definition
- Request validation
- Minimal business logic
- Delegates to service layer

### 2. **services/** - Business Logic Layer

#### **ZoomService** (`zoom_service.py`)
Encapsulates all Zoom API interactions:
- `get_user_id(email)` - Get Zoom user ID from email
- `list_recordings(email)` - Get user's recorded meetings
- `get_meeting_transcript(meeting_id)` - Get meeting transcript
- Handles authentication with Zoom API
- Contains mock data for testing

#### **GraphService** (`graph_service.py`)
Encapsulates all Microsoft Graph API interactions:
- `list_meetings(email)` - Get Teams meetings with recordings
- `get_meeting_transcript(meeting_id)` - Get meeting transcript and participants
- `send_chat_message(meeting_id, summary, participants)` - Create chat and send summary
- Uses MSAL ConfidentialClientApplication for authentication
- Implements client credentials flow for application permissions
- Contains mock data for testing

#### **LLMService** (`llm_service.py`)
Encapsulates LLM/AI summarization:
- `generate_summary(transcript)` - Generate meeting summary
- Currently uses mock implementation
- Ready for integration with OpenAI, Azure OpenAI, or other LLM providers

## Benefits of This Architecture

1. **Separation of Concerns**: Clear separation between HTTP handling and business logic
2. **Testability**: Services can be tested independently
3. **Maintainability**: Changes to API integrations are isolated to service files
4. **Reusability**: Services can be used by different routes or other parts of the application
5. **Mock/Real Toggle**: Easy switching between mock and real API calls via `USE_MOCK_DATA` flag
6. **Single Responsibility**: Each service handles one external system

## Adding New Functionality

### To add a new Zoom feature:
1. Add method to `ZoomService` class
2. Add mock data if needed
3. Call the method from your route in `app.py`

### To add a new Teams/Graph feature:
1. Add method to `GraphService` class
2. Add mock data if needed
3. Call the method from your route in `app.py`

### To change summarization logic:
1. Update `LLMService.generate_summary()` method
2. No changes needed to routes

## Configuration

Services are initialized in `app.py` with the mock flag:

```python
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'

zoom_service = ZoomService(use_mock=USE_MOCK_DATA)
graph_service = GraphService(use_mock=USE_MOCK_DATA)
llm_service = LLMService(use_mock=USE_MOCK_DATA)
```

Set `USE_MOCK_DATA=false` in `.env` to use real APIs.

## Authentication Flow

### Microsoft Graph (Application Permissions)
1. Service initializes `ConfidentialClientApplication` with:
   - Client ID
   - Client Secret
   - Tenant ID
2. Acquires token using `acquire_token_for_client()` with scope `https://graph.microsoft.com/.default`
3. Token is used in Authorization header for all Graph API calls
4. Token is cached by MSAL and automatically refreshed

### Zoom (OAuth 2.0)
- Currently using mock implementation
- Real implementation would use OAuth 2.0 authorization code flow or server-to-server OAuth
