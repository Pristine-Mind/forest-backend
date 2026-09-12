from rest_framework import permissions


class IsCommitteeChair(permissions.BasePermission):
    """Full access for committee chairs and superusers."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_committee_chair())


class IsDFOViewer(permissions.BasePermission):
    """Read-only access for DFO viewers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_dfo_viewer()
            and request.method in permissions.SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS


class IsMember(permissions.BasePermission):
    """Base permission for authenticated members."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_member_user() or request.user.is_committee_chair())
        )


class IsSubCommitteeMember(permissions.BasePermission):
    """Sub-committee members get scoped access; committee officers get full access."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_sub_committee_user() or request.user.is_committee_chair() or request.user.is_dfo_viewer())
        )


class IsReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedReadOnly(permissions.BasePermission):
    """Authenticated users with read-only access."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.method in permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS


class IsChair(permissions.BasePermission):
    """Permission for users with COMMITTEE_CHAIR role."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Allow if user role is COMMITTEE_CHAIR or superuser
        return request.user.is_committee_chair()


class BankTransactionPermission(permissions.BasePermission):
    """
    Bank Transaction permissions:
    - Chair: full access (create, read, update, delete)
    - Secretary and Staff: can create and update, but not delete
    - Others: read-only access
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ["POST", "PUT", "PATCH"]:
            return (
                request.user.is_committee_chair()
                or request.user.is_secretary()
                or request.user.is_staff_user()
            )

        if request.method == "DELETE":
            return request.user.is_committee_chair()

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ["PUT", "PATCH"]:
            return (
                request.user.is_committee_chair()
                or request.user.is_secretary()
                or request.user.is_staff_user()
            )

        if request.method == "DELETE":
            return request.user.is_committee_chair()

        return False
