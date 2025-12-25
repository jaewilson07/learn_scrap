from fastapi import APIRouter, Request


router = APIRouter()

@router.get("/")
def read_root(request: Request):
    user = request.session.get("user")
    if user:
        return {"message": f"Hello {user.get('name', 'User')}", "user": user}
    return {"message": "Hello World", "login_url": "/login"}
