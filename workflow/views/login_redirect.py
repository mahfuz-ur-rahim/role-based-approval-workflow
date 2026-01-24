from django.contrib.auth.views import LoginView
from django.urls import reverse


class RoleBasedLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name__in=["Manager", "Admin"]).exists():
            return reverse("workflow:manager-document-list")

        return reverse("workflow:document-list")
