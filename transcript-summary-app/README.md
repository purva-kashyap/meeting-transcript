# Meeting Transcript Summary App

A Flask web application that retrieves meeting transcripts from Zoom and Microsoft Teams, generates AI summaries, and allows sharing summaries via Teams chat.

## Features

- **Home Page**: Enter email to retrieve meetings from Zoom or Teams
- **Zoom Integration**: 
  - List recorded Zoom meetings
  - View transcripts and AI-generated summaries
  - Edit summaries
  - Send summaries to Teams chat
- **Teams Integration**:
  - List recorded Teams meetings
  - View transcripts and AI-generated summaries
  - Edit summaries
  - Send summaries to Teams chat with all participants
- **Navigation**: Home and Back buttons on all pages
- **Mock Data**: Pre-configured mock responses for testing without credentials

## Project Structure

```
transcript-summary-app/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── templates/             # HTML templates
│   ├── home.html         # Home page
│   ├── meetings.html     # Meetings list page
│   └── summary.html      # Transcript & summary page
├── static/               # Static files
│   └── style.css        # Stylesheet
└── README.md            # This file
```

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd /Users/purvakashyap/Projects/meeting-transcript/transcript-summary-app
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional for mock testing):
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials when ready
   ```

## Running the App

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Testing with Mock Data

The app comes with pre-configured mock data. You can test all functionality without setting up real API credentials:

### Test Email Addresses:
- `user@example.com` - Has both Zoom and Teams meetings
- `test@test.com` - Has limited meetings

### Test Flow:

1. **Home Page**:
   - Enter one of the test email addresses
   - Click "Get Zoom Meetings" or "Get Teams Meetings"

2. **Meetings List**:
   - View the list of recorded meetings
   - Click "View Transcript & Summary" on any meeting

3. **Summary Page**:
   - View the original transcript
   - See the AI-generated summary
   - Click "Edit Summary" to modify the summary
   - Click "Send in Teams" to simulate sending to Teams chat

## Mock Data Details

### Zoom Meetings:
- **user@example.com**: 
  - Product Planning Session
  - Sprint Retrospective
- **test@test.com**:
  - Client Demo

### Teams Meetings:
- **user@example.com**:
  - Weekly Team Sync
  - Architecture Review
- **test@test.com**:
  - Customer Support Review

## API Endpoints

### Zoom Endpoints:
- `POST /list/zoom/meetings` - Get list of Zoom meetings
  - Body: `{"email": "user@example.com"}`
- `GET /zoom/meeting/<meeting_id>/summary` - Get transcript and summary

### Teams Endpoints:
- `POST /list/teams/meetings` - Get list of Teams meetings
  - Body: `{"email": "user@example.com"}`
- `GET /teams/meeting/<meeting_id>/summary` - Get transcript and summary
- `POST /teams/send-summary` - Send summary to Teams chat
  - Body: `{"meeting_id": "...", "summary": "...", "participants": [...]}`

## Next Steps: Production Setup

When ready to use with real APIs:

1. **Set up Zoom OAuth App**:
   - Create an app at https://marketplace.zoom.us/
   - Add credentials to `.env`

2. **Set up Microsoft Azure App**:
   - Register app in Azure Portal
   - Add application permissions for Microsoft Graph
   - Configure ConfidentialClientApplication
   - Add credentials to `.env`

3. **Replace Mock Functions**:
   - Replace mock API calls in `app.py` with real API calls
   - Implement proper authentication flows
   - Add LLM integration for summary generation

4. **Security Considerations**:
   - Use HTTPS in production
   - Implement proper session management
   - Add user authentication
   - Validate and sanitize all inputs

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **APIs** (Mock): Zoom API, Microsoft Graph API
- **Authentication** (Planned): MSAL (Microsoft Authentication Library)

## License

This is a sample project for demonstration purposes.
