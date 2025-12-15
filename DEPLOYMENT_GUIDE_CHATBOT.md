# Chatbot Deployment Guide

This guide provides step-by-step instructions for deploying the production-ready chatbot system with all enhanced features.

## 🚀 Production Deployment Checklist

### 1. Environment Configuration

#### Backend Environment Variables

```bash
# Copy production environment template
cp backend/.env.production backend/.env

# Update with your actual values
SECRET_KEY=your-super-secure-secret-key-here
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/lean_construction
```

#### Frontend Environment Variables

```bash
# Update website/.env.local with production API URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 2. Database Migration

```bash
# Navigate to backend directory
cd backend

# Run Alembic migrations to create chat tables
alembic upgrade head

# Verify tables were created
psql -d lean_construction -c "\dt chat_*"
```

### 3. Install Dependencies

#### Backend Dependencies

```bash
cd backend
pip install -r requirements.txt

# Additional AI service dependencies (optional)
pip install openai anthropic
```

#### Frontend Dependencies

```bash
cd website
npm install
```

### 4. Production Build

#### Backend Production Server

```bash
# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with environment file
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --env-file .env
```

#### Frontend Production Build

```bash
cd website
npm run build
npm start
```

### 5. WebSocket Configuration

For WebSocket support in production:

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api/v1/chat/ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Testing & Validation

### Automated Testing

```bash
# Run the comprehensive test suite
cd backend
python test_chat_implementation.py your-email@example.com your-password

# Expected output:
# 🚀 Starting Chat Implementation Test
# 🔐 Authenticating user...
# ✅ Authentication successful
# 📝 Testing conversation creation...
# ✅ Conversation created with session_id: [uuid]
# 💬 Testing message sending...
# ✅ Message sent successfully
# 📨 Testing message retrieval...
# ✅ Retrieved X messages
# 🎉 All tests passed! Chat implementation is working correctly.
```

### Manual Testing

#### 1. API Endpoint Testing

```bash
# Test conversations endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.yourdomain.com/api/v1/chat/conversations

# Test message sending
curl -X POST https://api.yourdomain.com/api/v1/chat/messages \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"content": "Hello, can you help with lean construction?", "role": "user"}'
```

#### 2. Frontend Testing

1. Navigate to your frontend URL
2. Login with a valid account
3. Open the chat widget (bottom-right corner)
4. Send a message and verify:
   - ✅ Typing indicator appears
   - ✅ AI response is generated
   - ✅ Message history is preserved
   - ✅ No JavaScript errors in console

#### 3. WebSocket Testing

```bash
# Test WebSocket connection
wscat -c ws://api.yourdomain.com/api/v1/chat/ws/test-session?token=YOUR_TOKEN
```

## 📊 Monitoring & Logging

### Application Logs

```bash
# View application logs
tail -f /var/log/lean-construction/app.log

# Monitor real-time logs
journalctl -u lean-construction -f
```

### Health Checks

```bash
# API health check
curl https://api.yourdomain.com/health

# Database connectivity check
curl https://api.yourdomain.com/api/v1/chat/conversations \
     -H "Authorization: Bearer VALID_TOKEN"
```

### Performance Monitoring

```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s "https://api.yourdomain.com/api/v1/chat/conversations"

# curl-format.txt content:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_redirect:    %{time_redirect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n
```

## 🛠 Troubleshooting

### Common Issues

#### 1. CORS Errors

**Problem**: CORS policy blocks requests
**Solution**:

```python
# Check CORS configuration in main.py
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
```

#### 2. Database Connection Issues

**Problem**: Chat tables don't exist
**Solution**:

```bash
# Run migrations
alembic upgrade head

# Check table creation
psql -d lean_construction -c "\dt chat_*"
```

#### 3. AI Service Issues

**Problem**: AI responses not working
**Solution**:

```bash
# Check API keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test AI service directly
python -c "
from app.services.ai_service import ai_service
import asyncio
result = asyncio.run(ai_service.generate_response('test message'))
print(result)
"
```

#### 4. WebSocket Connection Issues

**Problem**: WebSocket connection fails
**Solution**:

```nginx
# Check Nginx WebSocket proxy configuration
location /api/v1/chat/ws/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Performance Optimization

#### Database Optimization

```sql
-- Add indexes for better query performance
CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_chat_conversations_user_id ON chat_conversations(user_id);
```

#### API Rate Limiting

```python
# Add rate limiting middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/chat/messages")
@limiter.limit("10/minute")
async def send_message(request: Request, ...):
    # Your endpoint logic
```

## 📈 Scaling Considerations

### Load Balancing

```nginx
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### Database Scaling

- Use connection pooling
- Consider read replicas for message retrieval
- Implement caching for frequently accessed conversations

### CDN Configuration

```javascript
// Configure CDN for static assets
// In next.config.js
module.exports = {
  assetPrefix:
    process.env.NODE_ENV === "production" ? "https://cdn.yourdomain.com" : "",
};
```

## 🔐 Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS properly configured for production domains
- [ ] Rate limiting implemented
- [ ] Input validation and sanitization
- [ ] JWT token expiration configured
- [ ] Database connection secured
- [ ] API keys stored securely (not in code)
- [ ] WebSocket authentication implemented
- [ ] Error messages don't leak sensitive information
- [ ] Regular security updates applied

## 📞 Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check application logs for errors
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Review and rotate API keys
4. **Annually**: Security audit and penetration testing

### Backup Strategy

```bash
# Database backup
pg_dump lean_construction > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz backend/.env website/.env.local
```

### Monitoring Alerts

Set up alerts for:

- High response times (>2 seconds)
- Error rates (>5%)
- Database connection failures
- WebSocket connection drops
- AI service failures

---

## ✅ Deployment Verification

After completing deployment, verify:

1. ✅ All API endpoints return expected responses
2. ✅ Chat widget loads and displays properly
3. ✅ User authentication works correctly
4. ✅ Messages save to database
5. ✅ AI responses generate successfully
6. ✅ Typing indicators function properly
7. ✅ Error handling displays user-friendly messages
8. ✅ Performance meets acceptable thresholds
9. ✅ Security measures are properly configured
10. ✅ Monitoring and logging are operational

The chatbot system is now production-ready with all enhanced features!
