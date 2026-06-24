import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main.web:create_app",
        host="localhost",
        port=8000,
        factory=True,
        workers=2,
    )
