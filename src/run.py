import uvicorn

if __name__ == "main":
    uvicorn.run("src.main.web:create_app", host="localhost", port=8000, factory=True, reload=True)
