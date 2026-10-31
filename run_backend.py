import uvicorn
import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
os.chdir(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("Starting ANN-DAAN AI FastAPI Service (Jaipur Regional Node)...")
    print("API Docs: http://localhost:8001/docs")
    print("Compliance: FSSAI (Recovery and Distribution of Surplus Food) Regulations 2019")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
