from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class RoleBasedLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name="Manager").exists():
            return "/manager/documents/"

        return "/documents/"
