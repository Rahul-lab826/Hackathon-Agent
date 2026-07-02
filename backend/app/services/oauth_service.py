"""
Google OAuth Service — handles the full OAuth 2.0 authorization code flow.
Exchanges auth codes for user info, then creates or updates user records.
"""
import secrets
import urllib.parse
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.config import settings
from app.models.user import AuthProvider
from app.repositories.user_repository import UserRepository
from app.schemas.auth import GoogleUserInfo, TokenPair
from app.services.token_service import TokenService

# In-memory state store (use Redis in production for multi-instance deployments)
_oauth_states: dict[str, str] = {}


class OAuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_service = TokenService(db)

    def get_google_auth_url(self) -> str:
        """
        Generate the Google OAuth authorization URL with a CSRF state token.
        The frontend should redirect the user to this URL.
        """
        state = secrets.token_urlsafe(32)
        _oauth_states[state] = "pending"   # Validate on callback

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def handle_google_callback(
        self,
        code: str,
        state: str,
        request: Request | None = None,
    ) -> TokenPair:
        """
        Complete the Google OAuth flow:
        1. Validate CSRF state
        2. Exchange authorization code for access token
        3. Fetch Google user profile
        4. Find or create user in DB
        5. Return JWT token pair
        """
        # 1. CSRF state check
        if state not in _oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state. Possible CSRF attack.",
            )
        del _oauth_states[state]

        # 2. Exchange code for tokens
        google_user = await self._exchange_code_for_user(code)

        # 3. Find existing user by Google ID or email
        user = await self.user_repo.get_by_google_id(google_user.google_id)

        if user is None:
            # Check if email already registered (merge accounts)
            user = await self.user_repo.get_by_email(google_user.email.lower())

            if user is not None:
                # Link Google ID to existing email account
                user = await self.user_repo.update(
                    user.id,
                    google_id=google_user.google_id,
                    auth_provider=AuthProvider.GOOGLE.value,
                    is_verified=True,
                    avatar_url=user.avatar_url or google_user.picture,
                )
            else:
                # Create brand new Google user
                user = await self.user_repo.create(
                    email=google_user.email.lower(),
                    hashed_password=None,           # No password for OAuth users
                    full_name=google_user.name,
                    auth_provider=AuthProvider.GOOGLE.value,
                    google_id=google_user.google_id,
                    avatar_url=google_user.picture,
                    is_verified=google_user.email_verified,
                )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Contact support.",
            )

        await self.user_repo.update_last_login(user.id)

        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        return await self.token_service.generate_token_pair(
            user, device_info=ua, ip_address=ip
        )

    async def _exchange_code_for_user(self, code: str) -> GoogleUserInfo:
        """
        Exchange OAuth authorization code for an access token,
        then fetch user info from Google's userinfo endpoint.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step A: Exchange code for tokens
            token_response = await client.post(
                settings.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code with Google.",
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token returned by Google.",
                )

            # Step B: Fetch user info
            userinfo_response = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info from Google.",
                )

            return GoogleUserInfo(**userinfo_response.json())
