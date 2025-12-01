"""Message service for internal messaging system.

Handles business logic for messaging permissions, auto-approval,
reputation checking, and notification sending.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.db.models import User, Message, MessageRecipient, MessageRequest, AffiliateProfile, AffiliateConnection, Campaign, ProductIntelligence
from app.schemas import MessageType, MessageRequestType, ConnectionType


class MessageService:
    """Service for managing internal messages and permissions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_send_message(self, sender_id: int, recipient_id: int, message_type: MessageType) -> Tuple[bool, str]:
        """Check if a user can send a message to another user."""
        sender = await self.db.get(User, sender_id)
        recipient = await self.db.get(User, recipient_id)

        if not sender or not recipient:
            return False, "User not found"

        if sender.role == "admin":
            return True, ""

        if sender_id == recipient_id:
            return False, "Cannot send message to yourself"

        has_connection = await self._check_connection(sender_id, recipient_id)
        return has_connection, ""

    async def _check_connection(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users have a connection."""
        connection = await self.db.scalar(
            select(AffiliateConnection).where(
                or_(
                    and_(
                        AffiliateConnection.user1_id == user1_id,
                        AffiliateConnection.user2_id == user2_id
                    ),
                    and_(
                        AffiliateConnection.user1_id == user2_id,
                        AffiliateConnection.user2_id == user1_id
                    )
                )
            )
        )
        return connection is not None

    async def get_broadcast_recipients(
        self,
        sender_id: int,
        broadcast_group: str
    ) -> List[int]:
        """Get recipient IDs for a broadcast group."""
        # Get all connections for the sender
        connections = await self.db.execute(
            select(AffiliateConnection).where(
                or_(
                    and_(
                        AffiliateConnection.user1_id == sender_id,
                        AffiliateConnection.status == "accepted"
                    ),
                    and_(
                        AffiliateConnection.user2_id == sender_id,
                        AffiliateConnection.status == "accepted"
                    )
                )
            )
        )
        connections = connections.scalars().all()

        if not connections:
            return []

        # Get connected user IDs
        connected_user_ids = set()
        for conn in connections:
            if conn.user1_id == sender_id:
                connected_user_ids.add(conn.user2_id)
            else:
                connected_user_ids.add(conn.user1_id)

        if not connected_user_ids:
            return []

        # Get user details for filtering
        users_result = await self.db.execute(
            select(User).where(User.id.in_(list(connected_user_ids)))
        )
        users = users_result.scalars().all()

        # Filter by broadcast group
        if broadcast_group == "all_affiliates":
            return [u.id for u in users if u.user_type == "Affiliate"]
        elif broadcast_group == "all_creators":
            return [u.id for u in users if u.user_type == "Creator"]
        elif broadcast_group == "all_connections":
            return [u.id for u in users]
        else:
            return []

    async def create_message(
        self,
        sender_id: int,
        subject: str,
        content: str,
        message_type: MessageType,
        recipient_ids: List[int],
        parent_message_id: Optional[int] = None,
        is_broadcast: bool = False,
        broadcast_group: Optional[str] = None
    ) -> Message:
        """Create a new message."""
        import logging
        import uuid
        logger = logging.getLogger(__name__)

        # Generate unique ID to trace this request
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"=== CREATE MESSAGE [{request_id}] ===")
        logger.info(f"sender_id: {sender_id} (type: {type(sender_id)})")
        logger.info(f"subject: {subject[:100]}")
        logger.info(f"recipient_ids: {recipient_ids}")
        logger.info(f"is_broadcast: {is_broadcast}")

        # CRITICAL: Ensure sender_id is an integer (defend against type issues)
        try:
            sender_id_int = int(sender_id)
            logger.info(f"✓ Converted sender_id to int: {sender_id_int}")
        except (ValueError, TypeError) as e:
            logger.error(f"✗ Failed to convert sender_id to int: {e}")
            raise

        # CRITICAL: Verify the sender exists and log their details
        sender_result = await self.db.execute(
            select(User).where(User.id == sender_id_int)
        )
        sender = sender_result.scalar_one_or_none()
        if sender:
            logger.info(f"✓ Sender verified: ID={sender.id}, Email={sender.email}")
        else:
            logger.error(f"✗ SENDER NOT FOUND with ID: {sender_id_int}")

        # If broadcast with group, expand to actual recipients
        if is_broadcast and broadcast_group and not recipient_ids:
            recipient_ids = await self.get_broadcast_recipients(sender_id_int, broadcast_group)
            logger.info(f"Expanded broadcast recipients: {recipient_ids}")

        logger.info(f"Creating Message object in memory...")
        message = Message(
            sender_id=sender_id_int,  # Use the int version
            subject=subject,
            content=content,
            message_type=message_type,
            parent_message_id=parent_message_id,
            is_broadcast=is_broadcast,
            status="sent"
        )

        logger.info(f"Message object created: sender_id={message.sender_id}")

        self.db.add(message)
        logger.info(f"Message added to session")

        await self.db.flush()
        logger.info(f"Message ID after flush: {message.id}")
        logger.info(f"Message sender_id after flush: {message.sender_id}")

        logger.info(f"Adding {len(recipient_ids)} recipients...")
        for recipient_id in recipient_ids:
            try:
                recipient_id_int = int(recipient_id)
            except (ValueError, TypeError):
                logger.error(f"✗ Invalid recipient_id: {recipient_id}")
                continue

            recipient = MessageRecipient(
                message_id=message.id,
                recipient_id=recipient_id_int,
                status="sent"
            )
            self.db.add(recipient)

        logger.info(f"Committing to database...")
        await self.db.commit()
        logger.info(f"✓ Database committed successfully")

        await self.db.refresh(message)

        logger.info(f"=== MESSAGE STORED IN DB [{request_id}] ===")
        logger.info(f"Message ID: {message.id}")
        logger.info(f"sender_id (DB): {message.sender_id}")
        logger.info(f"Expected sender_id: {sender_id_int}")
        logger.info(f"Match? {message.sender_id == sender_id_int}")
        logger.info(f"Recipients: {recipient_ids}")
        logger.info(f"Subject: {message.subject[:100]}")
        logger.info(f"====================================\n")

        return message

    async def get_inbox(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Message], int, int]:
        """Get user's inbox messages."""
        recipient_query = select(MessageRecipient).where(
            MessageRecipient.recipient_id == user_id,
            MessageRecipient.status != "archived"  # Exclude archived messages
        )

        result = await self.db.execute(recipient_query)
        recipients = result.scalars().all()

        if not recipients:
            return [], 0, 0

        message_ids = [r.message_id for r in recipients]

        messages_query = select(Message).where(
            Message.id.in_(message_ids),
            Message.deleted_at.is_(None)  # Exclude deleted messages
        ).order_by(Message.created_at.desc())

        offset = (page - 1) * per_page
        messages_query = messages_query.offset(offset).limit(per_page)

        result = await self.db.execute(messages_query)
        messages = result.scalars().all()

        unread_count = await self.db.scalar(
            select(func.count()).select_from(MessageRecipient).where(
                and_(
                    MessageRecipient.recipient_id == user_id,
                    MessageRecipient.read_at.is_(None)
                )
            )
        )

        total = await self.db.scalar(
            select(func.count()).select_from(MessageRecipient).where(
                MessageRecipient.recipient_id == user_id
            )
        )

        return list(messages), total or 0, unread_count or 0

    async def get_sent_messages(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Message], int]:
        """Get messages sent by user."""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"=== GET SENT MESSAGES SERVICE ===")
        logger.info(f"Request received for user_id: {user_id}")
        logger.info(f"Type of user_id: {type(user_id)}")

        # CRITICAL: Ensure user_id is an integer (defend against type issues)
        try:
            user_id_int = int(user_id)
            logger.info(f"✓ Converted user_id to int: {user_id_int}")
        except (ValueError, TypeError) as e:
            logger.error(f"✗ Failed to convert user_id to int: {e}")
            return [], 0

        # CRITICAL: Get the actual User object to verify
        user_result = await self.db.execute(
            select(User).where(User.id == user_id_int)
        )
        user = user_result.scalar_one_or_none()
        if user:
            logger.info(f"✓ User found: ID={user.id}, Email={user.email}, FullName={user.full_name}")
        else:
            logger.error(f"✗ USER NOT FOUND with ID: {user_id_int}")

        # Add a filter to ONLY get messages where sender_id EXACTLY matches user_id
        where_clause = and_(
            Message.sender_id == user_id_int,
            Message.deleted_at.is_(None)
        )

        logger.info(f"WHERE clause: sender_id={user_id_int} AND deleted_at IS NULL")
        logger.info(f"Comparison: Message.sender_id == {user_id_int}")

        query = select(Message).where(where_clause).order_by(Message.created_at.desc())

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Log the actual SQL query
        compiled = query.compile(self.db.bind, compile_kwargs={"literal_binds": True})
        logger.info(f"Compiled SQL Query: {compiled}")

        # Execute the query
        result = await self.db.execute(query)
        messages = result.scalars().all()

        logger.info(f"=== QUERY RESULTS ===")
        logger.info(f"Raw result count: {len(messages)}")
        logger.info(f"Type of result: {type(messages)}")

        for i, msg in enumerate(messages):
            msg_sender_id = int(msg.sender_id) if msg.sender_id is not None else None
            logger.info(f"[{i+1}] Message ID: {msg.id}")
            logger.info(f"    - sender_id (from DB): {msg.sender_id} (type: {type(msg.sender_id)})")
            logger.info(f"    - sender_id (as int):  {msg_sender_id} (type: {type(msg_sender_id)})")
            logger.info(f"    - Expected user_id:    {user_id_int} (type: {type(user_id_int)})")
            logger.info(f"    - Match (str)? {msg.sender_id == user_id_int}")
            logger.info(f"    - Match (int)? {msg_sender_id == user_id_int}")
            logger.info(f"    - Subject: {msg.subject[:80]}")
            logger.info(f"    - Message Type: {msg.message_type}")
            logger.info(f"    - Created: {msg.created_at}")
            logger.info(f"    ---")

        # Also check total count
        total_query = select(func.count()).select_from(Message).where(where_clause)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        logger.info(f"Total count (with filter): {total}")
        logger.info(f"=== END GET SENT MESSAGES ===\n")

        return list(messages), total or 0

    async def get_message_detail(self, message_id: int, user_id: int) -> Optional[Message]:
        """Get detailed message with recipients."""
        message = await self.db.scalar(
            select(Message).options(
                selectinload(Message.recipients).selectinload(MessageRecipient.recipient)
            ).where(
                Message.id == message_id,
                Message.deleted_at.is_(None)  # Exclude deleted messages
            )
        )

        if not message:
            return None

        is_authorized = (
            message.sender_id == user_id or
            any(r.recipient_id == user_id for r in message.recipients)
        )

        if not is_authorized:
            return None

        return message

    async def mark_as_read(self, message_id: int, user_id: int) -> bool:
        """Mark message as read for user."""
        recipient = await self.db.scalar(
            select(MessageRecipient).where(
                and_(
                    MessageRecipient.message_id == message_id,
                    MessageRecipient.recipient_id == user_id
                )
            )
        )

        if not recipient:
            return False

        recipient.read_at = datetime.utcnow()
        recipient.status = "read"

        await self.db.commit()
        return True

    async def create_message_request(
        self,
        sender_id: int,
        recipient_id: int,
        message_type: MessageRequestType,
        subject: str,
        content: str
    ) -> MessageRequest:
        """Create a new message request."""
        request = MessageRequest(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            subject=subject,
            content=content,
            status="pending"
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def get_received_requests(self, user_id: int, status: Optional[str] = None) -> List[MessageRequest]:
        """Get message requests received by user."""
        query = select(MessageRequest).where(
            MessageRequest.recipient_id == user_id
        )

        if status:
            query = query.where(MessageRequest.status == status)

        query = query.order_by(MessageRequest.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_sent_requests(self, user_id: int) -> List[MessageRequest]:
        """Get message requests sent by user."""
        query = select(MessageRequest).where(
            MessageRequest.sender_id == user_id
        ).order_by(MessageRequest.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def respond_to_request(self, request_id: int, responder_id: int, status: str) -> Optional[MessageRequest]:
        """Approve, reject, or block a message request."""
        request = await self.db.get(MessageRequest, request_id)

        if not request or request.recipient_id != responder_id:
            return None

        if status not in ["approved", "rejected", "blocked"]:
            raise ValueError("Invalid status")

        request.status = status
        request.responded_at = datetime.utcnow()

        if status == "approved":
            connection = AffiliateConnection(
                user1_id=request.sender_id,
                user2_id=request.recipient_id,
                connection_type=ConnectionType.APPROVED_REQUEST
            )
            self.db.add(connection)

        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def get_affiliates(self, page: int = 1, per_page: int = 20, search: Optional[str] = None) -> Tuple[List[AffiliateProfile], int]:
        """Get list of affiliates."""
        query = select(AffiliateProfile).options(
            selectinload(AffiliateProfile.user)
        )

        if search:
            query = query.where(
                or_(
                    AffiliateProfile.user.has(User.full_name.ilike(f"%{search}%")),
                    AffiliateProfile.specialty.ilike(f"%{search}%"),
                    AffiliateProfile.bio.ilike(f"%{search}%")
                )
            )

        query = query.order_by(AffiliateProfile.reputation_score.desc())

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.db.execute(query)
        profiles = result.scalars().all()

        total = await self.db.scalar(
            select(func.count()).select_from(AffiliateProfile)
        )

        return list(profiles), total or 0

    async def get_affiliate_profile(self, user_id: int) -> Optional[AffiliateProfile]:
        """Get affiliate profile by user ID."""
        return await self.db.scalar(
            select(AffiliateProfile).options(
                selectinload(AffiliateProfile.user)
            ).where(AffiliateProfile.user_id == user_id)
        )

    async def create_or_update_affiliate_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any]
    ) -> AffiliateProfile:
        """Create or update affiliate profile."""
        profile = await self.db.scalar(
            select(AffiliateProfile).where(AffiliateProfile.user_id == user_id)
        )

        if profile:
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            profile = AffiliateProfile(
                user_id=user_id,
                **profile_data
            )
            self.db.add(profile)

        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def search_affiliates(
        self,
        current_user_id: int,
        search_term: Optional[str] = None,
        specialty: Optional[str] = None,
        user_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search affiliates with connection status."""
        # Get current user to check their type
        current_user_result = await self.db.execute(
            select(User).where(User.id == current_user_id)
        )
        current_user = current_user_result.scalar_one()

        # Start building the query - need to join User for proper ORDER BY
        query = select(AffiliateProfile, User).join(
            User, User.id == AffiliateProfile.user_id
        ).where(AffiliateProfile.user_id != current_user_id)

        # If current user is a Creator, show:
        # 1. Affiliates who have campaigns for their products
        # 2. Other Creators (for networking)
        if current_user.user_type == 'Creator':
            # Get product intelligence IDs created by this user
            creator_products_result = await self.db.execute(
                select(ProductIntelligence.id).where(
                    ProductIntelligence.created_by_user_id == current_user_id
                )
            )
            creator_product_ids = creator_products_result.scalars().all()

            # Build conditions for what to show
            show_conditions = []

            # Condition 1: Other Creators (for networking)
            show_conditions.append(AffiliateProfile.user.has(User.user_type == 'Creator'))

            # Condition 2: Affiliates with campaigns for this Creator's products
            if creator_product_ids:
                # Create a subquery for affiliates with campaigns
                affiliate_campaigns_subquery = select(Campaign.user_id).where(
                    Campaign.product_intelligence_id.in_(creator_product_ids),
                    Campaign.user_id.isnot(None)
                ).distinct()

                show_conditions.append(AffiliateProfile.user_id.in_(affiliate_campaigns_subquery))

            # Combine conditions with OR
            if len(show_conditions) > 1:
                query = query.where(or_(*show_conditions))
            elif len(show_conditions) == 1:
                query = query.where(show_conditions[0])
            else:
                # No products and no creators to show
                return []
        else:
            # For Affiliates and others, show only Affiliate and Creator profiles (not Business)
            query = query.where(
                or_(
                    AffiliateProfile.user.has(User.user_type == 'Affiliate'),
                    AffiliateProfile.user.has(User.user_type == 'Creator')
                )
            )

        if search_term:
            query = query.where(
                or_(
                    AffiliateProfile.user.has(User.full_name.ilike(f"%{search_term}%")),
                    AffiliateProfile.specialty.ilike(f"%{search_term}%")
                )
            )

        if specialty:
            query = query.where(AffiliateProfile.specialty == specialty)

        if user_type:
            query = query.where(User.user_type == user_type)

        # Apply sorting for all cases
        query = query.order_by(
            # Sort: Affiliates first (1), then Creators (2)
            case(
                (User.user_type == 'Affiliate', 1),
                (User.user_type == 'Creator', 2),
                else_=3
            ),
            User.full_name.asc()
        )

        result = await self.db.execute(query)
        # Since we joined, result returns tuples (AffiliateProfile, User)
        rows = result.all()
        profiles = [row[0] for row in rows]

        enriched = []
        for profile in profiles:
            # Get campaigns for this affiliate to find product developers
            campaigns_result = await self.db.execute(
                select(Campaign).where(
                    Campaign.user_id == profile.user_id,
                    Campaign.product_intelligence_id.isnot(None)
                )
            )
            campaigns = campaigns_result.scalars().all()

            # Extract product developers from campaigns
            product_developers = []
            if campaigns:
                # Get unique product intelligence IDs
                product_intel_ids = list(set(c.product_intelligence_id for c in campaigns if c.product_intelligence_id))

                if product_intel_ids:
                    # Get product intelligence with creators
                    product_intel_result = await self.db.execute(
                        select(ProductIntelligence)
                        .options(selectinload(ProductIntelligence.created_by))
                        .where(ProductIntelligence.id.in_(product_intel_ids))
                    )
                    product_intelligences = product_intel_result.scalars().all()

                    # Build list of product developers
                    for pi in product_intelligences:
                        if pi.created_by and pi.created_by.id not in [pd['user_id'] for pd in product_developers]:
                            product_developers.append({
                                "user_id": pi.created_by.id,
                                "full_name": pi.created_by.full_name,
                                "email": pi.created_by.email,
                                "product_name": pi.product_name,
                                "product_url": pi.product_url
                            })

            data = {
                "id": profile.id,
                "user_id": profile.user_id,
                "email": profile.user.email,
                "full_name": profile.user.full_name,
                "user_type": profile.user.user_type,
                "profile_image_url": profile.user.profile_image_url,
                "specialty": profile.specialty,
                "years_experience": profile.years_experience,
                "reputation_score": profile.reputation_score,
                "verified": profile.verified,
                "is_connected": False,
                "mutual_products": product_developers
            }

            connection = await self._check_connection(current_user_id, profile.user_id)
            data["is_connected"] = connection

            enriched.append(data)

        return enriched

    async def get_my_connections(self, user_id: int) -> List[AffiliateConnection]:
        """Get all connections for a user."""
        connections = await self.db.execute(
            select(AffiliateConnection).where(
                or_(
                    AffiliateConnection.user1_id == user_id,
                    AffiliateConnection.user2_id == user_id
                )
            ).order_by(AffiliateConnection.created_at.desc())
        )
        return list(connections.scalars().all())

    async def delete_connection(self, connection_id: int, user_id: int) -> bool:
        """Delete/remove a connection. User must be part of the connection."""
        connection = await self.db.get(AffiliateConnection, connection_id)

        if not connection:
            return False

        # Check if user is part of this connection
        if connection.user1_id != user_id and connection.user2_id != user_id:
            return False

        await self.db.delete(connection)
        await self.db.commit()
        return True

    async def block_user(self, blocker_id: int, blocked_id: int) -> bool:
        """Block a user and remove any existing connection."""
        # First, remove any existing connection
        existing_connection = await self.db.scalar(
            select(AffiliateConnection).where(
                or_(
                    and_(
                        AffiliateConnection.user1_id == blocker_id,
                        AffiliateConnection.user2_id == blocked_id
                    ),
                    and_(
                        AffiliateConnection.user1_id == blocked_id,
                        AffiliateConnection.user2_id == blocker_id
                    )
                )
            )
        )

        if existing_connection:
            await self.db.delete(existing_connection)

        # Create a blocked connection record
        blocked_connection = AffiliateConnection(
            user1_id=blocker_id,
            user2_id=blocked_id,
            connection_type=ConnectionType.BLOCKED
        )
        self.db.add(blocked_connection)
        await self.db.commit()
        return True

    async def unblock_user(self, unblocker_id: int, blocked_id: int) -> bool:
        """Unblock a user by removing blocked connection record."""
        connection = await self.db.scalar(
            select(AffiliateConnection).where(
                and_(
                    AffiliateConnection.user1_id == unblocker_id,
                    AffiliateConnection.user2_id == blocked_id,
                    AffiliateConnection.connection_type == ConnectionType.BLOCKED
                )
            )
        )

        if not connection:
            return False

        await self.db.delete(connection)
        await self.db.commit()
        return True

    async def get_message_statistics(self, user_id: int) -> Dict[str, int]:
        """Get message statistics for user."""
        total_messages = await self.db.scalar(
            select(func.count()).select_from(MessageRecipient).where(
                MessageRecipient.recipient_id == user_id
            )
        )

        unread_messages = await self.db.scalar(
            select(func.count()).select_from(MessageRecipient).where(
                and_(
                    MessageRecipient.recipient_id == user_id,
                    MessageRecipient.read_at.is_(None)
                )
            )
        )

        sent_messages = await self.db.scalar(
            select(func.count()).select_from(Message).where(
                Message.sender_id == user_id
            )
        )

        pending_requests = await self.db.scalar(
            select(func.count()).select_from(MessageRequest).where(
                and_(
                    MessageRequest.sender_id == user_id,
                    MessageRequest.status == "pending"
                )
            )
        )

        approved_requests = await self.db.scalar(
            select(func.count()).select_from(MessageRequest).where(
                and_(
                    MessageRequest.sender_id == user_id,
                    MessageRequest.status == "approved"
                )
            )
        )

        return {
            "total_messages": total_messages or 0,
            "unread_messages": unread_messages or 0,
            "sent_messages": sent_messages or 0,
            "pending_requests": pending_requests or 0,
            "approved_requests": approved_requests or 0
        }
