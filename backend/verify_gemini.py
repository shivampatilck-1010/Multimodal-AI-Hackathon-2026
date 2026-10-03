import os
import sys
from dotenv import load_dotenv
from app.config import get_settings
from app.tutor.providers.llm import GeminiLLMProvider

def main():
    print("API key detected: ", end="")
    if os.path.exists(".env"):
        load_dotenv(".env")
    settings = get_settings()
    key = settings.gemini_api_key
    if key:
        print("YES")
    else:
        print("NO")
        sys.exit(0)

    print("Gemini client initialized: ", end="")
    try:
        if hasattr(key, "get_secret_value"):
            k = key.get_secret_value()
        else:
            k = key
        provider = GeminiLLMProvider(api_key=k, model=settings.gemini_chat_model, timeout_seconds=10.0)
        print("YES")
    except Exception as e:
        print("NO")
        print("Init Error:", e)
        sys.exit(0)

    print("Gemini request succeeded: ", end="")
    try:
        provider.generate(
            system_prompt="Say hi",
            user_prompt="Hello",
        )
        print("YES")
    except Exception as e:
        print("NO")
        inner = getattr(e, "__cause__", e)
        if inner and "503" in str(inner):
             print("Gemini service unavailable (503)")
        else:
             print(f"Error type: {type(inner).__name__ if inner else type(e).__name__}")
             print(f"Details: {str(inner) if inner else str(e)}")

if __name__ == "__main__":
    main()
