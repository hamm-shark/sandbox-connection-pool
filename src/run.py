import uvicorn

from src.main.app_config import AppSettings, get_settings

if __name__ == "__main__":
    app_settings = get_settings(AppSettings)
    uvicorn.run(
        "src.main.web:create_app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        factory=True,
        workers=2,
    )
