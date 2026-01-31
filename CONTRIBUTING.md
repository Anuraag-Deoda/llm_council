# Contributing to LLM Council

Thank you for your interest in contributing to LLM Council! This document provides guidelines and information for developers who want to extend or improve the application.

## Development Setup

Follow the [QUICKSTART.md](QUICKSTART.md) guide to set up your development environment.

## Project Architecture

### Backend Architecture

```
backend/app/
├── services/           # Business logic layer
│   ├── llm_service.py           # Unified LLM interface
│   ├── openai_service.py        # OpenAI integration
│   ├── openrouter_service.py    # OpenRouter integration
│   └── council_orchestrator.py  # Core 3-stage orchestration
├── routes/             # API endpoints
│   ├── chat.py         # Chat functionality
│   └── models.py       # Model management
├── database/           # Data persistence
│   └── storage.py      # JSON-based storage
├── config.py           # Configuration management
├── models.py           # Pydantic models
└── main.py            # FastAPI application
```

### Frontend Architecture

```
frontend/
├── app/               # Next.js App Router
│   ├── page.tsx      # Home page
│   └── layout.tsx    # Root layout
├── components/        # React components
│   ├── ChatInterface.tsx    # Main orchestrator
│   ├── MessageList.tsx      # Conversation display
│   ├── TabView.tsx          # Model response tabs
│   ├── StageIndicator.tsx   # Process visualization
│   └── ModelSelector.tsx    # Model configuration
└── lib/
    └── api.ts        # Backend API client
```

## Common Contributions

### Adding a New LLM Provider

1. **Create a service** (e.g., `backend/app/services/anthropic_service.py`):

```python
class AnthropicService:
    async def generate_response(self, model: str, messages: list) -> str:
        # Implementation
        pass

    async def generate_streaming_response(self, model: str, messages: list):
        # Implementation
        pass
```

2. **Update LLMService** (`backend/app/services/llm_service.py`):

```python
def __init__(self):
    self.openai_service = OpenAIService()
    self.openrouter_service = OpenRouterService()
    self.anthropic_service = AnthropicService()  # Add this

def _get_service(self, model_id: str):
    if model_id in settings.anthropic_models:  # Add this
        return self.anthropic_service
    # ... existing code
```

3. **Update configuration** (`backend/app/config.py`):

```python
class Settings(BaseSettings):
    # Add new settings
    anthropic_api_key: str = ""
    anthropic_models: List[str] = ["claude-3-opus-20240229"]
```

### Adding a New Feature

1. **Backend**: Add routes in `backend/app/routes/`
2. **Frontend**: Create components in `frontend/components/`
3. **API Client**: Update `frontend/lib/api.ts`

### Improving the UI

The frontend uses:
- **Tailwind CSS** for styling
- **React Markdown** for rendering
- **TypeScript** for type safety

Example: Adding a dark mode toggle

```tsx
// frontend/components/ThemeToggle.tsx
export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  return (
    <button onClick={() => setDark(!dark)}>
      {dark ? '☀️' : '🌙'}
    </button>
  );
}
```

### Enhancing the Council Process

The orchestration logic is in `backend/app/services/council_orchestrator.py`.

**Example**: Add a Stage 4 for fact-checking

```python
async def _stage4_fact_check(self, final_response: str) -> dict:
    """Stage 4: Fact-check the final response."""
    # Implementation
    pass

async def run_council(self, ...):
    # Existing stages 1-3
    # ...

    # New stage 4
    yield self._encode_chunk(
        StreamChunk(
            type="stage_update",
            stage="fact_check",
            content="Fact-checking final response..."
        )
    )

    fact_check = await self._stage4_fact_check(final_response)
    # ... handle results
```

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Use async/await for I/O operations
- Document functions with docstrings

```python
async def generate_response(
    self,
    model: str,
    messages: list,
    temperature: float = 0.7,
) -> str:
    """
    Generate a response from the model.

    Args:
        model: Model identifier
        messages: List of chat messages
        temperature: Sampling temperature (0-1)

    Returns:
        Generated response text
    """
    # Implementation
```

### TypeScript (Frontend)

- Use functional components with hooks
- Properly type all props and state
- Extract reusable logic into custom hooks
- Keep components focused and single-purpose

```tsx
interface MyComponentProps {
  data: string[];
  onSelect: (item: string) => void;
}

export default function MyComponent({ data, onSelect }: MyComponentProps) {
  // Implementation
}
```

## Testing

### Backend Tests

Create tests in `backend/tests/`:

```python
import pytest
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_generate_response():
    service = LLMService()
    response = await service.generate_response(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert isinstance(response, str)
    assert len(response) > 0
```

Run tests:
```bash
cd backend
pytest
```

### Frontend Tests

Create tests alongside components:

```tsx
// frontend/components/__tests__/TabView.test.tsx
import { render, screen } from '@testing-library/react';
import TabView from '../TabView';

test('renders tabs for each response', () => {
  const responses = [
    { model_id: 'model1', response: 'Response 1', timestamp: Date.now() }
  ];

  render(<TabView responses={responses} />);
  expect(screen.getByText('model1')).toBeInTheDocument();
});
```

## Database Migrations

Currently using JSON storage. To migrate to a real database:

1. **Choose a database** (PostgreSQL, MongoDB, etc.)
2. **Create models** using an ORM (SQLAlchemy, Motor, etc.)
3. **Update storage.py** to use the new database
4. **Create migration scripts**

Example with SQLAlchemy:

```python
# backend/app/database/models.py
from sqlalchemy import Column, String, JSON, DateTime
from .base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    messages = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

## API Documentation

The backend uses FastAPI, which auto-generates OpenAPI docs.

Access at: `http://localhost:8000/docs`

To customize docs:

```python
# backend/app/main.py
app = FastAPI(
    title="LLM Council API",
    description="Extended description here",
    version="2.0.0",
    docs_url="/api/docs",
)
```

## Performance Optimization

### Backend

1. **Caching**: Add Redis for response caching
2. **Rate Limiting**: Use slowapi or similar
3. **Connection Pooling**: Reuse HTTP connections
4. **Batch Processing**: Process multiple queries in parallel

### Frontend

1. **Code Splitting**: Use dynamic imports
2. **Memoization**: Use React.memo for expensive components
3. **Virtual Scrolling**: For long conversation histories
4. **Debouncing**: For search/filter inputs

## Security Considerations

1. **API Keys**: Never commit API keys to git
2. **Input Validation**: Validate all user inputs
3. **Rate Limiting**: Prevent abuse
4. **CORS**: Configure properly for production
5. **Authentication**: Add user authentication for production

## Deployment

### Environment Variables

Production environment should have:

```env
# Backend
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
CORS_ORIGINS=https://yourdomain.com
DATABASE_PATH=/data/conversations.json

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Docker Deployment

```bash
# Build images
docker-compose build

# Run in production mode
docker-compose up -d
```

### Traditional Deployment

**Backend:**
```bash
# Using gunicorn + uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
npm run build
npm start
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Pull Request Guidelines

- Describe what your PR does
- Include screenshots for UI changes
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass
- Keep PRs focused and atomic

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase
- Discussion of design decisions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LLM Council! 🏛️
