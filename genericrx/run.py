import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure current directory is in python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    print("Starting GenericRx - Offline-First Medicine Alternative & Cost Audit System...")
    print("Server URL: http://127.0.0.1:8000")
    print("OpenAPI Docs: http://127.0.0.1:8000/docs")
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
