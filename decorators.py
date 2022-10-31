from signin import *


def admin_only(func):
    async def wrapper(request, *args, **kwargs):
        if not request.token:
            return text("You are unauthorized.", 401)

        user = await get_current_active_user(request, request.token)
        if user.is_admin:
            result = await func(request, *args, **kwargs)
            return result

        return text("Access denied. You aren't admin", 400)

    return wrapper

