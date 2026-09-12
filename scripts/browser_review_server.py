"""Browser review server for evaluator interactive verification.

Hosts the React single page application and FastAPI backend on http://127.0.0.1:8000.
Supports either SQLite WAL (default) or an ephemeral disposable PostgreSQL 16 instance.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add school_service to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "school_service" / "src"))
sys.path.insert(0, str(root_dir / "services" / "school_service" / "tests"))

import uvicorn
from disposable_postgres import DisposablePostgresCluster, find_pg_bin
from schoolbag.interfaces.http.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Schoolbag Browser Review Server")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    parser.add_argument(
        "--db",
        type=str,
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Database engine to use (default: sqlite)",
    )
    args = parser.parse_args()

    # Ensure static directory points to built web dist
    dist_dir = root_dir / "apps" / "web" / "dist"
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        print(f"[WARN] Web dist directory not found at {dist_dir}.")
        print("[INFO] Please run 'npm run build' in apps/web before opening the browser.")

    os.environ["SCHOOLBAG_STATIC_DIR"] = str(dist_dir)

    pg_cluster = None
    db_url = None

    if args.db == "postgres":
        pg_bin = find_pg_bin()
        if not pg_bin:
            print("[ERROR] PostgreSQL 16 binaries not found in workspace. Reverting to SQLite.")
            args.db = "sqlite"
        else:
            print("[INFO] Initializing disposable ephemeral PostgreSQL 16 cluster...")
            pg_cluster = DisposablePostgresCluster(pg_bin=pg_bin)
            pg_cluster.start()
            db_url = pg_cluster.db_url
            print(f"[INFO] Ephemeral PostgreSQL running at: {db_url}")

    if args.db == "sqlite":
        db_file = root_dir / "schoolbag_dev.db"
        db_url = f"sqlite:///{db_file}"
        print(f"[INFO] Using persistent SQLite WAL database at: {db_file}")

    print("=" * 70)
    print("  SCHOOLBAG (SB-001) - BROWSER REVIEW SERVER")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  Database Engine: {args.db.upper()}")
    print("  Evaluator Mode: Zero Personal Spend (₹0.00), Public Synthetic Data")
    print("  Human Gate: Non-parent actions return HTTP 403 HUMAN_APPROVAL_REQUIRED")
    print("=" * 70)

    app = create_app(db_url=db_url)

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        if pg_cluster:
            print("[INFO] Tearing down ephemeral PostgreSQL cluster...")
            pg_cluster.stop()


if __name__ == "__main__":
    main()
