from app.shared.dependencies import get_current_user, oauth2_scheme

# Re-export canonical implementation to keep backward compatibility.
# New code should import from app.shared.dependencies directly.
__all__ = ["get_current_user", "oauth2_scheme"]
