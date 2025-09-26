# Cross-Border Tax Consultant

A minimal-yet-production-ready AI web application that acts as a cross-border tax consultant. The app uses conversational AI to gather information, ask clarifying questions, and provide structured tax guidance for international tax situations.

## ⚠️ Important Disclaimer

This application provides general information only and is not legal or tax advice. Always consult a qualified tax professional for specific guidance on your tax situation.

## Features

- **Conversational Interface**: Natural chat-based interaction with streaming responses
- **Multi-Phase Flow**: Systematic information gathering through intake, clarifications, and final suggestions
- **Case File Management**: Real-time tracking of user information and conversation state
- **Message Editing**: Edit previous messages to explore different scenarios (truncates conversation after edit)
- **Safety & Compliance**: Built-in protection against collecting sensitive identifiers
- **International Coverage**: Handles common cross-border tax scenarios (US↔Canada, US↔EU, etc.)
- **Mobile Responsive**: Works on desktop and mobile devices

## Tech Stack

### Backend
- **FastAPI**: High-performance API framework
- **Google Gemini AI**: Advanced language model for tax consultation
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **React + TypeScript**: Modern UI framework with type safety
- **Vite**: Fast build tool and dev server
- **TanStack Query**: Data fetching and streaming
- **React Markdown**: Rich text rendering for AI responses

### Tooling
- **Backend**: `ruff` (linting) + `black` (formatting)
- **Frontend**: `eslint` + `prettier`

## Quick Start

### 🐳 Docker (Recommended)

The easiest way to run the entire application:

#### Prerequisites
- Docker and Docker Compose
- Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

#### Setup & Run
```bash
git clone <your-repo-url>
cd cross-border-tax

# Setup environment (choose one):
# Windows Command Prompt:
setup.bat

# Windows PowerShell:
setup.ps1

# Unix/Linux/Mac:
make setup

# Edit .env and add your GEMINI_API_KEY

# Start the application
docker-compose up -d

# Or for development with hot reload
docker-compose -f docker-compose.dev.yml up -d
```

**Access the application:**
- **Production**: http://localhost:3000
- **Development**: http://localhost:5173
- **API**: http://localhost:8000

#### Docker Commands

**Using Make (Unix/Linux/Mac):**
```bash
make help          # Show all available commands
make up            # Start in production mode
make dev           # Start in development mode
make down          # Stop the application
make logs          # Show logs
make clean         # Remove all containers and images
```

**Direct Docker Compose (All platforms):**
```bash
docker-compose up -d                           # Start production
docker-compose -f docker-compose.dev.yml up   # Start development
docker-compose down                            # Stop application
docker-compose logs -f                         # Show logs
docker-compose ps                              # Show status
```

### 🔧 Manual Setup (Alternative)

#### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

#### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd cross-border-tax
```

#### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
python -m app.main
```

The backend will start at `http://localhost:8000`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start at `http://localhost:5173`

#### 4. Open the Application

Navigate to `http://localhost:5173` in your browser to start using the tax consultant.

## Usage Flow

### 1. Intake Phase
The AI will gather basic information:
- Countries/jurisdictions involved
- Tax residency status
- Income sources
- Tax year
- Foreign assets
- Filing status

### 2. Clarifications Phase
The AI asks targeted follow-up questions based on your situation to understand:
- Specific cross-border issues
- Tax treaty implications
- Potential compliance requirements
- Risk factors

### 3. Final Suggestions
After sufficient information is gathered, the AI provides:
- **Key Issues**: Main tax considerations identified
- **Suggested Actions**: Recommended next steps
- **Documents to Gather**: Paperwork you'll likely need
- **Forms Involved**: Tax forms that may be required (marked as "likely")
- **Risks & Questions**: Areas requiring professional attention

### 4. Message Editing Feature
You can edit any of your previous messages to explore different scenarios:
- **Hover** over any of your messages to see the edit button (✏️)
- **Click** the edit button to modify your response
- **Save** your changes to continue the conversation from that point
- All messages after the edited message will be removed
- The AI will respond based on the new conversation flow

## API Endpoints

- `POST /session/create` - Create new consultation session
- `GET /session/{id}` - Get session details
- `POST /chat` - Send message (streaming response)
- `POST /message/edit` - Edit a previous message (streaming response)
- `POST /session/{id}/force_final` - Request final suggestions

## Development

### 🐳 Docker Development (Recommended)

The easiest way to develop with hot reload and automatic restarts:

```bash
# Start development containers with hot reload
docker-compose -f docker-compose.dev.yml up -d

# View logs (useful for debugging)
docker-compose -f docker-compose.dev.yml logs -f

# Stop development containers
docker-compose -f docker-compose.dev.yml down

# Restart containers (if needed after major changes)
docker-compose -f docker-compose.dev.yml restart
```

**Development URLs:**
- **Frontend**: http://localhost:5173 (with hot reload)
- **Backend**: http://localhost:8000 (with auto-reload)

**Development Features:**
- Frontend: Hot reload on file changes
- Backend: Auto-reload on Python file changes
- Volume mounting: Your code changes are immediately reflected
- Debug logging: Enhanced logging for development

### Manual Development Setup

#### Backend Development

```bash
cd backend

# Install dev dependencies
pip install ruff black

# Lint
ruff check .

# Format
black .

# Run with auto-reload
python -m uvicorn app.main:app --reload
```

#### Frontend Development

```bash
cd frontend

# Lint
npm run lint

# Format
npx prettier --write .

# Build
npm run build
```

## Production Deployment

### 🐳 Docker (Recommended)
```bash
# Build and start in production mode
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Deployment

#### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run build
# Serve the dist/ folder with your preferred static file server
```

### Environment Variables

Create a `.env` file in the root directory:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
SESSION_SECRET=your_secure_session_secret
```

Or copy from the example:
```bash
cp .env.example .env
```

## Security Features

- **Sensitive Data Protection**: Automatically detects and prevents collection of SSN, SIN, etc.
- **Input Sanitization**: All user inputs are validated and sanitized
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Session Management**: Secure session handling without persistent storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting and formatting
5. Test your changes
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. For security issues, please email privately

## Roadmap

- [ ] Persistent session storage (database)
- [ ] User authentication system
- [ ] Document upload and analysis
- [ ] Multi-language support
- [ ] Integration with tax software APIs
- [ ] Advanced reporting features