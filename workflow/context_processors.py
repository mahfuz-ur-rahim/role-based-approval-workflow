def role_flags(request):
    user = request.user

    if not user.is_authenticated:
        return {
            "is_employee": False,
            "is_manager": False,
            "is_admin": False,
        }

    groups = set(user.groups.values_list("name", flat=True))

    return {
        "is_employee": "Employee" in groups or "Manager" in groups or "Admin" in groups,
        "is_manager": "Manager" in groups or "Admin" in groups,
        "is_admin": "Admin" in groups or user.is_superuser,
    }
