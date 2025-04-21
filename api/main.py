# --- api/main.py (ABSOLUTE MINIMAL TEST) ---
import sys
import os # Import os just in case
# Use flush=True to try and force output in logs
print(f"--- START main.py --- PyVersion: {sys.version} ---", flush=True)

try:
    print(f"--- Importing FastAPI ---", flush=True)
    from fastapi import FastAPI
    print(f"--- Imported FastAPI ---", flush=True)

    print(f"--- Creating FastAPI app object ---", flush=True)
    app = FastAPI()
    print(f"--- Created FastAPI app object ---", flush=True)

    @app.get("/ping")
    def ping():
        print(f"--- Handling GET /ping ---", flush=True)
        return {"message": "pong from /ping"}
    print(f"--- Defined GET /ping ---", flush=True)

    # Define root path just to see if it gets defined
    # Vercel routing will likely send "/" to public/index.html anyway
    @app.get("/")
    def read_root():
        print(f"--- Handling GET / ---", flush=True)
        return {"message": "Root of API"}
    print(f"--- Defined GET / ---", flush=True)

    print(f"--- Successfully finished main.py setup ---", flush=True)

except Exception as e:
    print(f"--- ERROR during setup: {type(e).__name__}: {e} ---", flush=True)
    # Try to log traceback as well
    import traceback
    traceback.print_exc()
    print(f"--- END main.py due to ERROR ---", flush=True)
    # Re-raising might be necessary for Vercel to properly log the failure
    raise e

print(f"--- END main.py top-level execution (should only see on startup) ---", flush=True)
