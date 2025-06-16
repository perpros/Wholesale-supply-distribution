from fastapi import Depends, HTTPException, status
from app.models.user import User as UserModel, UserRole
from app.core.security import get_current_user # Existing dependency to get authenticated user

class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role.value}' is not authorized for this action. Requires one of: {[role.value for role in self.allowed_roles]}"
            )
        return current_user

# Specific role dependencies
require_admin_role = RoleChecker([UserRole.ADMIN])
require_supplier_role = RoleChecker([UserRole.SUPPLIER])
require_end_user_role = RoleChecker([UserRole.END_USER])

# Dependency for actions allowed by EITHER End User OR Admin (e.g. cancelling own request vs admin cancelling any)
# This can be handled by checking specific permissions within the endpoint or service,
# or by a more complex dependency if needed. For now, RoleChecker is for specific roles.
# For combined roles, a list can be passed:
require_end_user_or_admin = RoleChecker([UserRole.END_USER, UserRole.ADMIN])

# Example of a permission that needs resource context (e.g. is owner)
# This is often better handled in the service layer or router path operation function directly,
# as dependencies don't easily get path parameters or request body before the main function.
# However, one could write a more complex class-based dependency if desired.

# def require_request_owner(
#     request_id: int, # This would need to come from path
#     current_user: UserModel = Depends(get_current_user),
#     db: Session = Depends(get_db) # If DB access is needed
# ):
#     # ... logic to fetch request and check ownership ...
#     # This pattern is often simpler directly in the endpoint.
#     pass
