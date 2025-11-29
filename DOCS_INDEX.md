# Documentation Index - PixelCraft Bloom

Welcome! This index helps you find the right documentation for your needs.

---

## 🚀 Getting Started

**New to the project?** Start here:

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (5 minutes)
   - 5-minute local setup
   - 3-command Docker setup
   - Essential commands reference
   - Print-friendly quick lookup

2. **[OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)** (30 minutes)
   - Detailed setup instructions
   - Architecture explanation
   - Configuration options
   - Troubleshooting guide

3. **[README.md](README.md)** (ongoing reference)
   - Project overview
   - Technology stack
   - Feature descriptions
   - API documentation

---

## 📚 Detailed Guides

### For Daily Development: RUNBOOK.md

Use [RUNBOOK.md](RUNBOOK.md) for:
- Daily development workflows
- Running and monitoring services
- Testing procedures (unit, integration, smoke tests)
- Common operational tasks
- Extensive troubleshooting (8+ scenarios with solutions)
- Performance optimization tips
- Emergency procedures

**Topics covered**:
- How to start services and verify they work
- How to check logs and diagnose problems
- How to run tests and validate functionality
- How to handle common issues
- Performance expectations and tuning

### For First-Time Setup: OLLAMA_SETUP_GUIDE.md

Use [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) for:
- Understanding Ollama architecture
- Installing and configuring Ollama
- Pulling and managing models
- Docker Compose configuration
- Detailed troubleshooting
- Performance tuning
- Advanced multi-model setups

**Topics covered**:
- Why we use Ollama (local models)
- How Ollama works in the system
- Setting up on macOS, Linux, Windows
- Configuration options and trade-offs
- Known issues and how to fix them
- Performance recommendations

### For Quick Lookup: QUICK_REFERENCE.md

Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for:
- Commands you need right now
- Configuration you need to check
- Files you need to edit
- Quick troubleshooting fixes
- Print as a reference card

**Sections**:
- Essential commands
- Configuration reference
- Troubleshooting quick fixes
- File locations
- Common patterns

---

## 🔍 Finding Answers

### "How do I set up the project?"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) **OR** [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)

### "How do I fix [problem]?"
→ [RUNBOOK.md](RUNBOOK.md) Troubleshooting section

### "What are the available commands?"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) Essential Commands section

### "How do I configure Ollama?"
→ [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)

### "What's new in this version?"
→ [RELEASE_NOTES.md](RELEASE_NOTES.md)

### "What was done in this session?"
→ [SESSION_SUMMARY.md](SESSION_SUMMARY.md)

### "What are the API endpoints?"
→ [README.md](README.md) Backend API section

### "How do I deploy to production?"
→ [README.md](README.md) Production Deployment section

### "How do I run tests?"
→ [RUNBOOK.md](RUNBOOK.md) Testing and Validation section

### "What's using all my memory?"
→ [RUNBOOK.md](RUNBOOK.md) Troubleshooting > Memory Issues

### "Why is my chat endpoint slow?"
→ [RUNBOOK.md](RUNBOOK.md) Troubleshooting > Slow Model Responses
OR [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) Performance Tuning

---

## 📊 Documentation Overview

| Document | Purpose | Audience | Length |
|----------|---------|----------|--------|
| **[README.md](README.md)** | Project overview, API docs, deployment | Everyone | 22KB |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Commands, config, quick lookups | Daily users | 8KB |
| **[OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)** | Deep dive on Ollama setup | Setup/troubleshooting | 16KB |
| **[RUNBOOK.md](RUNBOOK.md)** | Daily operations, testing, troubleshooting | Developers/DevOps | 20KB |
| **[RELEASE_NOTES.md](RELEASE_NOTES.md)** | Version info, migration guide | Release management | 10KB |
| **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** | What was accomplished this session | Project management | 12KB |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Original setup guide (legacy) | Reference | 8KB |

**Total documentation**: ~96KB (2500+ lines)

---

## 🎯 Use Cases

### "I'm a new developer"
1. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 5 minutes
2. Follow setup instructions (local or Docker)
3. Bookmark [RUNBOOK.md](RUNBOOK.md) for daily reference

### "I need to fix something"
1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) Troubleshooting section
2. If not solved, go to [RUNBOOK.md](RUNBOOK.md) Troubleshooting
3. If still stuck, check [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) Known Issues

### "I'm deploying to production"
1. Review [README.md](README.md) Production Deployment section
2. Check [RELEASE_NOTES.md](RELEASE_NOTES.md) for current version info
3. Plan for 24GB+ memory if using multiple models
4. Set up monitoring per [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)

### "I'm working on a feature"
1. Start services using [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Check logs using [RUNBOOK.md](RUNBOOK.md) "Checking Logs"
3. Test using [RUNBOOK.md](RUNBOOK.md) "Testing and Validation"

### "I need to understand the architecture"
1. Read [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) Architecture section
2. Review [README.md](README.md) for overall system
3. Check [RELEASE_NOTES.md](RELEASE_NOTES.md) for design decisions

---

## 🔗 Quick Links

### Setup Commands
```bash
# Local development (5 minutes)
ollama serve &
ollama pull mistral &
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload &
npm run dev

# Docker Compose (3 commands)
docker compose up -d
sleep 60  # Wait for Ollama
curl http://localhost:8000/api/models | jq .
```

### Key Files
- **Backend config**: `backend/app/config.py`
- **Models config**: `backend/app/models/config.py`
- **Environment**: `backend/.env` (copy from `.env.example`)
- **Docker setup**: `docker-compose.yml`

### Important Directories
- **Frontend**: `src/`
- **Backend**: `backend/app/`
- **Models**: `backend/app/models/`
- **API routes**: `backend/app/routes/`
- **Tests**: `backend/tests/`

---

## 📋 Checklist: First 30 Minutes

- [ ] Read this index (you are here)
- [ ] Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) Quick Start section (5 min)
- [ ] Choose setup: local OR Docker Compose
- [ ] Follow setup instructions (10 min)
- [ ] Run API test: `curl http://localhost:8000/api/models`
- [ ] Bookmark [RUNBOOK.md](RUNBOOK.md) for reference
- [ ] Join development workflow

---

## 🆘 Need Help?

**Step 1: Check the right doc**
- Troubleshooting? → [RUNBOOK.md](RUNBOOK.md)
- Configuration? → [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)
- Quick command? → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- API help? → [README.md](README.md)

**Step 2: Search the doc**
- Use Ctrl+F / Cmd+F to search for keywords
- Example: "timeout" or "memory" or "restart"

**Step 3: Still stuck?**
- Check GitHub issues: https://github.com/codesleeps/pixelcraft-bloom/issues
- Review logs: `docker compose logs backend`
- Join development discussion

---

## 📝 Documentation Style

All documentation is:
- **Clear**: Written for beginners and experts
- **Complete**: Covers setup, config, troubleshooting
- **Practical**: Includes commands and examples
- **Organized**: Hierarchical structure with navigation
- **Searchable**: Use Ctrl+F / Cmd+F effectively
- **Maintained**: Updated with code changes

---

## 🔄 Documentation Maintenance

These docs are maintained alongside code:
- Check git commit messages for related changes
- Update docs when changing configuration
- Report doc issues like code bugs
- Suggest improvements to existing docs

---

## Version Information

- **Current Version**: 1.1.0
- **Released**: 2025-01-29
- **Status**: Stable for single-model development
- **Documentation**: Complete and comprehensive

For version history, see [RELEASE_NOTES.md](RELEASE_NOTES.md).

---

**Last Updated**: 2025-01-29

---

## Quick Navigation

```
Documentation Index (you are here)
├─ QUICK_REFERENCE.md ────→ 5-minute reference card
├─ OLLAMA_SETUP_GUIDE.md ──→ Detailed Ollama setup
├─ RUNBOOK.md ─────────────→ Daily operations & troubleshooting
├─ README.md ───────────────→ Project overview & API docs
├─ RELEASE_NOTES.md ────────→ Version info & migration
├─ SESSION_SUMMARY.md ──────→ What was accomplished
└─ SETUP_GUIDE.md ──────────→ Legacy setup guide

For detailed troubleshooting:
└─ RUNBOOK.md > Troubleshooting section
   ├─ Chat endpoint issues
   ├─ Service startup problems
   ├─ Memory/performance issues
   └─ Network connectivity

For architecture understanding:
└─ OLLAMA_SETUP_GUIDE.md > Architecture Overview
   ├─ Service connectivity diagram
   ├─ Model lifecycle explanation
   └─ Timeout handling details
```

---

**Ready to get started?** Go to [QUICK_REFERENCE.md](QUICK_REFERENCE.md)!

