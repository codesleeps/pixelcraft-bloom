# General-purpose models
ollama pull llama2
ollama pull llama3

# Specialized models
ollama pull mistral
ollama pull codellama
```

- **llama2**: Versatile model for chat and general tasks.
- **llama3**: Advanced conversational AI.
- **mistral**: Fast, efficient model for various applications.
- **codellama**: Code generation specialist.

This may take several minutes depending on your internet speed.

### Starting Ollama Server

Ollama runs as a background service. Start it with:

```bash
ollama serve
```

The server will be available at `http://localhost:11434` by default. Keep this running while using PixelCraft Bloom.

### Verification

Test Ollama with a simple command:

```bash
ollama run llama3 "Hello, world!"
```

You should see a response from the model.

## Backend Setup

The backend is built with FastAPI and handles AI agents, database operations, and API endpoints.

### Clone and Navigate

```bash
git clone https://github.com/codesleeps/pixelcraft-bloom.git
cd pixelcraft-bloom/backend
```

### Virtual Environment

Create and activate a Python virtual environment:

```bash
# Create
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   # Required
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   SUPABASE_JWT_SECRET=your-jwt-secret

   # Ollama (if running locally)
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3

   # Optional
   REDIS_URL=redis://localhost:6379/0
   HUGGINGFACE_API_KEY=your-huggingface-key  # For cloud fallback
   ```

   Get Supabase credentials from your [Supabase Dashboard](https://app.supabase.com) > Settings > API.

### Database Setup

If using Supabase, the database is already provisioned. For local PostgreSQL:

1. Install PostgreSQL and create a database.
2. Update `.env` with your local database URL.

Run any pending migrations (if applicable):

```bash
# If migrations exist
python -m alembic upgrade head
```

### Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

## Frontend Setup

The frontend is a React/TypeScript application built with Vite.

### Navigate to Project Root

```bash
cd ..  # From backend/ to project root
```

### Install Dependencies

```bash
npm install
```

### Environment Configuration

Create `.env.local` in the project root:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Model Configuration

Configure AI models for optimal performance across different tasks.

### Model Settings

Edit `backend/app/models/config.py` to define available models:

```python
MODELS = {
    "llama3": {
        "provider": "ollama",
        "model_name": "llama3",
        "capabilities": ["chat", "generation"],
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2048,
        }
    },
    "codellama": {
        "provider": "ollama",
        "model_name": "codellama",
        "capabilities": ["code"],
        "parameters": {
            "temperature": 0.3,
            "max_tokens": 1024,
        }
    }
}
```

### Task-to-Model Mapping

Configure which models handle specific tasks in `backend/app/models/config.py`:

```python
TASK_MODEL_MAPPING = {
    "chat": ["llama3", "mistral"],
    "code": ["codellama"],
    "lead_qualification": ["llama2", "mistral"],
    "content_creation": ["llama3", "llama2"],
}
```

### Testing Models

Test model functionality via API:

```bash
# Test model health
curl http://localhost:8000/api/models/health

# Test specific model
curl -X POST http://localhost:8000/api/models/test \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3", "prompt": "Hello, AI!"}'
```

Or use the frontend ModelTester component at `http://localhost:5173/models/tester`.

## External Services

Configure optional integrations for enhanced functionality.

### CRM Integration (HubSpot)

1. Create a [HubSpot account](https://www.hubspot.com/).
2. Go to Settings > Integrations > Private Apps.
3. Create a new app with CRM permissions.
4. Copy the access token to `.env`:
   ```bash
   CRM_PROVIDER=hubspot
   CRM_API_KEY=your-private-app-token
   ```

### Email Integration (SendGrid)

1. Create a [SendGrid account](https://sendgrid.com/).
2. Generate an API key with Mail Send permissions.
3. Add to `.env`:
   ```bash
   EMAIL_PROVIDER=sendgrid
   EMAIL_API_KEY=your-sendgrid-key
   EMAIL_FROM=noreply@yourdomain.com
   ```

### Calendar Integration (Google Calendar)

1. Create a [Google Cloud project](https://console.cloud.google.com/).
2. Enable Calendar API.
3. Create OAuth credentials or API key.
4. Add to `.env`:
   ```bash
   CALENDAR_PROVIDER=google
   CALENDAR_API_KEY=your-google-api-key
   ```

## Testing

Run comprehensive tests to verify your setup.

### Backend Tests

```bash
cd backend
pytest
```

For coverage report:
```bash
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
npm test
```

For coverage:
```bash
npm run test:coverage
```

### Integration Testing

1. Start both backend and frontend.
2. Create a test lead via the dashboard.
3. Verify AI agents respond correctly.
4. Check real-time updates work (requires Redis).

## Troubleshooting

Common issues and solutions.

### Ollama Issues

**Model not found error:**
```bash
ollama pull llama3
```

**Connection refused:**
- Ensure `ollama serve` is running.
- Check `OLLAMA_HOST` in `.env`.

**Slow responses:**
- Use lighter models like `mistral`.
- Increase system RAM.

### Backend Issues

**Import errors:**
- Ensure virtual environment is activated.
- Reinstall dependencies: `pip install -r requirements.txt`

**Database connection failed:**
- Verify Supabase credentials.
- Check network connectivity.

**WebSocket not working:**
- Ensure Redis is running if using pub/sub.
- Check CORS settings.

### Frontend Issues

**Build errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version.

**API calls failing:**
- Verify `VITE_API_BASE_URL` points to running backend.
- Check browser console for CORS errors.

### Performance Issues

**High memory usage:**
- Reduce model context windows.
- Use smaller models.

**Slow API responses:**
- Enable caching in ModelManager.
- Optimize database queries.

## Production Deployment

Deploy PixelCraft Bloom for production use.

### Frontend Deployment (Vercel)

1. Connect your GitHub repo to [Vercel](https://vercel.com/).
2. Set build settings:
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. Add environment variables:
   - `VITE_API_BASE_URL`: Your backend URL
   - `VITE_SUPABASE_URL`: Production Supabase URL

### Backend Deployment (VPS)

1. Provision a VPS (e.g., DigitalOcean, AWS EC2).
2. Install Python, Nginx, and Certbot.
3. Deploy with systemd:
   ```bash
   # Create service file
   sudo nano /etc/systemd/system/pixelcraft.service
   ```

   Service file content:
   ```ini
   [Unit]
   Description=PixelCraft Bloom API
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/pixelcraft-bloom/backend
   ExecStart=/home/ubuntu/pixelcraft-bloom/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. Configure Nginx:
   ```nginx
   server {
       listen 80;
       server_name your-api-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       # WebSocket support
       location /api/ws {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

5. Enable SSL with Certbot:
   ```bash
   sudo certbot --nginx -d your-api-domain.com