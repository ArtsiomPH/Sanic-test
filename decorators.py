from auth import get_current_active_user

from sanic import text

from functools import wraps


def admin_only(wrapped):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if not request.token:
                return text("You are unauthorized.", 401)

            user = await get_current_active_user(request, request.token)
            if user.is_admin:
                result = await func(request, *args, **kwargs)
                return result

            return text("Access denied. You aren't admin", 400)

        return wrapper
    return decorator(wrapped)


def active_user_only(wrapped):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if not request.token:
                return text("You are unauthorized.", 401)

            if request.ctx.current_user:
                result = await func(request, *args, **kwargs)
                return result

        return wrapper
    return decorator(wrapped)

