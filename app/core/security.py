from fastapi import Depends, HTTPException, status

# Placeholder for actual user model and token handling
class User:
    def __init__(self, username: str = "testuser", email: str = "test@example.com", active: bool = True):
        self.username = username
        self.email = email
        self.active = active

async def get_current_user():
    # In a real app, you'd decode a token here and fetch the user
    return User()

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
