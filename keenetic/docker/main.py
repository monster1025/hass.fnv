import os
import asyncssh
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets
import uvicorn

app = FastAPI(title="Keenetic SSH Controller")
security = HTTPBasic()

# --- КОНФИГУРАЦИЯ ИЗ ENV ---
ROUTER_HOST = os.getenv("ROUTER_HOST", "192.168.1.1")
ROUTER_PORT = int(os.getenv("ROUTER_PORT", "22"))
ROUTER_USER = os.getenv("ROUTER_USER", "admin")

# SSH Auth
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

# API Auth
API_USER = os.getenv("API_USER", "api_user")
API_PASS = os.getenv("API_PASS", "strong_password")

# --- ЖЕСТКИЙ ВАЙТЛИСТ КОМАНД ---
# Разрешены только команды, начинающиеся с этих префиксов
COMMAND_WHITELIST = [
    "ip hotspot host",
    "system configuration save"
]

# Опасные символы, которые запрещены в любой команде
DANGEROUS_CHARS = [";", "|", "&", "$", "`", ">", "<", "\n", "\r", "!"]

class CommandRequest(BaseModel):
    command: str

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, API_USER)
    correct_password = secrets.compare_digest(credentials.password, API_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def validate_command(command: str) -> bool:
    """
    Проверяет команду against жесткий вайтлист.
    """
    if not command or not command.strip():
        return False
    
    command = command.strip()
    
    # 1. Проверка на опасные символы (защита от инъекций)
    for char in DANGEROUS_CHARS:
        if char in command:
            return False
    
    # 2. Проверка по вайтлисту (префикс)
    for allowed_pattern in COMMAND_WHITELIST:
        if command.startswith(allowed_pattern):
            return True
    
    return False

async def execute_ssh_command(command: str):
    # Валидация команды
    if not validate_command(command):
        raise HTTPException(
            status_code=403, 
            detail=f"Command not allowed. Contact administrator to whitelist this command."
        )
    
    connect_kwargs = {
        "host": ROUTER_HOST,
        "port": ROUTER_PORT,
        "username": ROUTER_USER,
        "known_hosts": None
    }

    if SSH_KEY_PATH and os.path.exists(SSH_KEY_PATH):
        connect_kwargs["client_keys"] = [SSH_KEY_PATH]
    elif SSH_PASSWORD:
        connect_kwargs["password"] = SSH_PASSWORD
    else:
        raise HTTPException(status_code=500, detail="SSH Auth not configured (Key or Password required)")

    try:
        async with asyncssh.connect(**connect_kwargs) as conn:
            result = await conn.run(command)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_status
            }
    except asyncssh.Error as exc:
        raise HTTPException(status_code=503, detail=f"SSH Connection failed: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")

@app.post("/run")
async def run_command(request: CommandRequest, username: str = Depends(get_current_user)):
    return await execute_ssh_command(request.command)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/allowed-commands")
async def get_allowed_commands(username: str = Depends(get_current_user)):
    """
    Возвращает список разрешенных паттернов команд.
    """
    return {
        "whitelist": COMMAND_WHITELIST
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)