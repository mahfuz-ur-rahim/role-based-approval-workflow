from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class GroupRequiredMixin(UserPassesTestMixin):
    """
    Base mixin for group-based access control.
    Subclasses must define `required_groups`.
    """

    required_groups: list[str] = []

    def test_func(self):
        user = self.request.user # type: ignore

        if not user.is_authenticated:
            return False

        # Superusers always pass
        if user.is_superuser:
            return True

        return user.groups.filter(name__in=self.required_groups).exists()


class EmployeeRequiredMixin(GroupRequiredMixin):
    required_groups = ["Employee", "Manager", "Admin"]


class ManagerRequiredMixin(GroupRequiredMixin):
    required_groups = ["Manager", "Admin"]


class AdminRequiredMixin(GroupRequiredMixin):
    required_groups = ["Admin"]


class ApproverRequiredMixin(GroupRequiredMixin):
    """
    Allows Manager or Admin users to approve/reject documents.
    Self-approval must be enforced at the view level.
    """

    required_groups = ["Manager", "Admin"]
