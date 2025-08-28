"""
Production server runner for PsyWiz Backend.
"""

import uvicorn
import argparse
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.config import settings


def main():
    """Main entry point for production server."""
    parser = argparse.ArgumentParser(description="Run PsyWiz Backend Server")
    
    parser.add_argument(
        "--host",
        default=settings.host,
        help=f"Host to bind to (default: {settings.host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port to bind to (default: {settings.port})"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        default=settings.log_level.lower(),
        choices=["critical", "error", "warning", "info", "debug"],
        help=f"Log level (default: {settings.log_level.lower()})"
    )
    
    parser.add_argument(
        "--access-log",
        action="store_true",
        help="Enable access log"
    )
    
    args = parser.parse_args()
    
    # Server configuration
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": args.access_log,
    }
    
    # Development vs Production settings
    if args.reload or settings.debug:
        print("🔧 Running in DEVELOPMENT mode")
        config.update({
            "reload": True,
            "reload_dirs": [str(app_dir / "app")],
        })
    else:
        print("🚀 Running in PRODUCTION mode")
        config.update({
            "workers": args.workers,
            "worker_class": "uvicorn.workers.UvicornWorker",
        })
    
    print(f"🌐 Server starting on http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health Check: http://{args.host}:{args.port}/health")
    
    # Start server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()