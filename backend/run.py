import argparse
import uvicorn
from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="Run AgentsFlowAI FastAPI backend")
    parser.add_argument("--host", help="Host to bind", default=settings.app_host)
    parser.add_argument("--port", help="Port to bind", type=int, default=settings.app_port)
    parser.add_argument("--reload", help="Enable reload", action="store_true")
    parser.add_argument("--workers", help="Number of workers", type=int, default=1)
    args = parser.parse_args()

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload, workers=args.workers)


if __name__ == "__main__":
    main()
