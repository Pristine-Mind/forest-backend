from rest_framework import permissions


class IsCommitteeOfficer(permissions.BasePermission):
    """Full access for committee officers and superusers."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_committee_officer())


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
            and (request.user.is_member_user() or request.user.is_committee_officer())
        )


class IsSubCommitteeMember(permissions.BasePermission):
    """Sub-committee members get scoped access; committee officers get full access."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_sub_committee_user() or request.user.is_committee_officer() or request.user.is_dfo_viewer())
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
