"""
Multi-User Support System for Claude-AGI
=========================================

Manages multiple users with context isolation, user identification,
and privacy preservation between users.
"""

import asyncio
import hashlib
import logging
import secrets
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AuthenticationLevel(Enum):
    """User authentication levels"""
    ANONYMOUS = "anonymous"  # No authentication
    SESSION = "session"  # Session-based (temporary)
    IDENTIFIED = "identified"  # User provided identifier
    AUTHENTICATED = "authenticated"  # Strong authentication
    VERIFIED = "verified"  # Verified identity


@dataclass
class UserSession:
    """Active user session with isolated context"""
    session_id: str
    user_id: str
    authentication_level: AuthenticationLevel
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    conversation_history: deque = field(default_factory=lambda: deque(maxlen=100))
    active_goals: List[str] = field(default_factory=list)
    privacy_settings: Dict[str, bool] = field(default_factory=lambda: {
        'share_data': False,
        'persistent_memory': True,
        'cross_session_learning': True,
        'anonymous_mode': False
    })
    session_metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, timeout_hours: int = 24) -> bool:
        """Check if session has expired"""
        return (datetime.now() - self.last_activity) > timedelta(hours=timeout_hours)

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


@dataclass
class UserIdentity:
    """User identity information"""
    user_id: str
    identifiers: Set[str] = field(default_factory=set)  # email, username, etc.
    authentication_tokens: Dict[str, str] = field(default_factory=dict)
    authentication_level: AuthenticationLevel = AuthenticationLevel.ANONYMOUS
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiUserManager:
    """
    Manages multiple users with context isolation and privacy preservation.

    Key Features:
    - User identification and authentication
    - Session management with context isolation
    - Privacy preservation between users
    - Context switching without data leakage
    - Per-user data access control
    """

    def __init__(self):
        # User identities
        self.identities: Dict[str, UserIdentity] = {}

        # Active sessions
        self.active_sessions: Dict[str, UserSession] = {}

        # Session lookup by user_id
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)

        # Current active session
        self.current_session_id: Optional[str] = None

        # Privacy isolation - user-specific data stores
        self.user_data: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Session expiration settings
        self.session_timeout_hours = 24
        self.cleanup_interval_minutes = 30

    async def create_user(
        self,
        user_id: Optional[str] = None,
        identifiers: Optional[Set[str]] = None,
        authentication_level: AuthenticationLevel = AuthenticationLevel.ANONYMOUS
    ) -> UserIdentity:
        """
        Create a new user identity.

        Args:
            user_id: Optional user ID (generated if not provided)
            identifiers: Set of identifying information (email, username, etc.)
            authentication_level: Initial authentication level

        Returns:
            Created user identity
        """
        # Generate user_id if not provided
        if user_id is None:
            user_id = self._generate_user_id()

        # Check if user already exists
        if user_id in self.identities:
            raise ValueError(f"User {user_id} already exists")

        # Create identity
        identity = UserIdentity(
            user_id=user_id,
            identifiers=identifiers or set(),
            authentication_level=authentication_level
        )

        self.identities[user_id] = identity
        logger.info(f"Created user identity: {user_id} (level: {authentication_level.value})")

        return identity

    async def create_session(
        self,
        user_id: str,
        authentication_level: Optional[AuthenticationLevel] = None
    ) -> UserSession:
        """
        Create a new session for a user.

        Args:
            user_id: User identifier
            authentication_level: Authentication level for this session

        Returns:
            Created session
        """
        # Get or create user identity
        if user_id not in self.identities:
            identity = await self.create_user(
                user_id=user_id,
                authentication_level=authentication_level or AuthenticationLevel.ANONYMOUS
            )
        else:
            identity = self.identities[user_id]

        # Generate session ID
        session_id = self._generate_session_id()

        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            authentication_level=authentication_level or identity.authentication_level
        )

        # Store session
        self.active_sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)

        logger.info(f"Created session {session_id} for user {user_id}")

        return session

    async def switch_to_session(self, session_id: str) -> UserSession:
        """
        Switch context to a different user session.

        Args:
            session_id: Session to switch to

        Returns:
            Activated session

        Raises:
            ValueError: If session doesn't exist or is expired
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Check if expired
        if session.is_expired(self.session_timeout_hours):
            await self.end_session(session_id)
            raise ValueError(f"Session {session_id} has expired")

        # Update activity
        session.touch()

        # Switch context
        old_session = self.current_session_id
        self.current_session_id = session_id

        logger.info(f"Switched context: {old_session} -> {session_id} (user: {session.user_id})")

        return session

    async def get_current_session(self) -> Optional[UserSession]:
        """Get the currently active session"""
        if self.current_session_id is None:
            return None
        return self.active_sessions.get(self.current_session_id)

    async def get_current_user_id(self) -> Optional[str]:
        """Get the currently active user ID"""
        session = await self.get_current_session()
        return session.user_id if session else None

    async def end_session(self, session_id: str):
        """
        End a user session.

        Args:
            session_id: Session to end
        """
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        user_id = session.user_id

        # Remove from active sessions
        del self.active_sessions[session_id]

        # Remove from user's session list
        if user_id in self.user_sessions:
            self.user_sessions[user_id].remove(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

        # Clear current session if this was it
        if self.current_session_id == session_id:
            self.current_session_id = None

        logger.info(f"Ended session {session_id} for user {user_id}")

    async def store_user_data(
        self,
        key: str,
        value: Any,
        user_id: Optional[str] = None
    ):
        """
        Store data for a specific user with privacy isolation.

        Args:
            key: Data key
            value: Data value
            user_id: User ID (defaults to current session's user)
        """
        # Get user_id from current session if not provided
        if user_id is None:
            user_id = await self.get_current_user_id()
            if user_id is None:
                raise ValueError("No active session")

        # Store data with privacy isolation
        self.user_data[user_id][key] = value

        logger.debug(f"Stored data for user {user_id}: {key}")

    async def get_user_data(
        self,
        key: str,
        user_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """
        Retrieve data for a specific user with privacy protection.

        Args:
            key: Data key
            user_id: User ID (defaults to current session's user)
            default: Default value if key not found

        Returns:
            Retrieved data or default
        """
        # Get user_id from current session if not provided
        if user_id is None:
            user_id = await self.get_current_user_id()
            if user_id is None:
                return default

        # Retrieve data with privacy isolation
        return self.user_data[user_id].get(key, default)

    async def check_data_access_permission(
        self,
        requesting_user_id: str,
        target_user_id: str
    ) -> bool:
        """
        Check if requesting user has permission to access target user's data.

        Args:
            requesting_user_id: User requesting access
            target_user_id: User whose data is being accessed

        Returns:
            True if access is permitted
        """
        # Users can always access their own data
        if requesting_user_id == target_user_id:
            return True

        # Check target user's privacy settings
        # Find an active session for target user
        session_ids = self.user_sessions.get(target_user_id, [])
        for session_id in session_ids:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if session.privacy_settings.get('share_data', False):
                    return True

        # Default: deny access
        return False

    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.active_sessions[sid] for sid in session_ids if sid in self.active_sessions]

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if session.is_expired(self.session_timeout_hours):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.end_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get multi-user system statistics"""
        active_sessions = len(self.active_sessions)
        total_users = len(self.identities)

        # Count by authentication level
        auth_levels = defaultdict(int)
        for identity in self.identities.values():
            auth_levels[identity.authentication_level.value] += 1

        # Count sessions by user
        sessions_per_user = {
            user_id: len(sessions)
            for user_id, sessions in self.user_sessions.items()
        }

        return {
            'total_users': total_users,
            'active_sessions': active_sessions,
            'current_session_id': self.current_session_id,
            'authentication_levels': dict(auth_levels),
            'sessions_per_user': sessions_per_user,
            'data_stores_count': len(self.user_data)
        }

    def _generate_user_id(self) -> str:
        """Generate a unique user ID"""
        return f"user_{secrets.token_urlsafe(16)}"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{secrets.token_urlsafe(24)}"


async def demo():
    """Demo multi-user support"""
    manager = MultiUserManager()

    # Create users
    alice_identity = await manager.create_user(
        user_id="alice",
        identifiers={"alice@example.com"},
        authentication_level=AuthenticationLevel.IDENTIFIED
    )

    bob_identity = await manager.create_user(
        user_id="bob",
        identifiers={"bob@example.com"},
        authentication_level=AuthenticationLevel.IDENTIFIED
    )

    print(f"Created users: {alice_identity.user_id}, {bob_identity.user_id}")

    # Create sessions
    alice_session = await manager.create_session("alice")
    bob_session = await manager.create_session("bob")

    print(f"Created sessions: {alice_session.session_id}, {bob_session.session_id}")

    # Switch to Alice's session and store data
    await manager.switch_to_session(alice_session.session_id)
    await manager.store_user_data("favorite_color", "blue")
    print(f"Stored Alice's favorite color")

    # Switch to Bob's session and store different data
    await manager.switch_to_session(bob_session.session_id)
    await manager.store_user_data("favorite_color", "green")
    print(f"Stored Bob's favorite color")

    # Verify privacy isolation
    alice_color = await manager.get_user_data("favorite_color", user_id="alice")
    bob_color = await manager.get_user_data("favorite_color", user_id="bob")

    print(f"\nPrivacy isolation verified:")
    print(f"  Alice's favorite color: {alice_color}")
    print(f"  Bob's favorite color: {bob_color}")

    # Statistics
    stats = await manager.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    asyncio.run(demo())
