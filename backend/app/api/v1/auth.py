"""
Auth API Routes — registration, login, OAuth, token management, logout.
All responses follow consistent JSON structure.
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    GoogleAuthURL,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserProfile
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.services.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Register ──────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Creates a new user account with email and password. "
        "Returns a JWT token pair immediately — no separate login required after registration."
    ),
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = AuthService(db)
    return await service.register(payload, request)


# ─── Login ─────────────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Authenticates a user by email + password. "
        "Returns a JWT access token and a refresh token. "
        "Accounts are locked for 30 minutes after 5 consecutive failed attempts."
    ),
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = AuthService(db)
    return await service.login(payload, request)


# ─── Logout ────────────────────────────────────────────────────────────────────
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout — revoke refresh token",
    description="Revokes the provided refresh token, logging out the current device.",
)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),  # Auth guard — must be logged in
) -> MessageResponse:
    service = AuthService(db)
    return await service.logout(payload.refresh_token)


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout all devices",
    description="Revokes ALL refresh tokens for the current user, logging out every device.",
)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    service = AuthService(db)
    return await service.logout_all_devices(current_user.id)


# ─── Refresh Token ─────────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description=(
        "Exchanges a valid refresh token for a new short-lived access token. "
        "The refresh token itself is NOT rotated."
    ),
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    service = AuthService(db)
    return await service.refresh_token(payload.refresh_token)


# ─── Current User ──────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current authenticated user",
    description="Returns the full profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user


# ─── Google OAuth ──────────────────────────────────────────────────────────────
@router.get(
    "/google",
    response_model=GoogleAuthURL,
    summary="Get Google OAuth URL",
    description=(
        "Returns the Google OAuth authorization URL. "
        "The frontend should redirect the user to this URL to begin the OAuth flow."
    ),
)
async def google_auth_url(db: AsyncSession = Depends(get_db)) -> GoogleAuthURL:
    service = OAuthService(db)
    return GoogleAuthURL(auth_url=service.get_google_auth_url())


@router.get(
    "/google/callback",
    response_model=TokenPair,
    summary="Google OAuth callback",
    description=(
        "Handles the Google OAuth authorization code callback. "
        "Exchanges the code for user info, creates or finds the user, "
        "and returns a JWT token pair."
    ),
)
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = OAuthService(db)
    return await service.handle_google_callback(code=code, state=state, request=request)
