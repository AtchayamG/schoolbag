"""Schoolbag's persistent FastAPI service on Vercel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services/school_service/src'))
from schoolbag.interfaces.http.app import create_app  # noqa: E402

app = create_app()
