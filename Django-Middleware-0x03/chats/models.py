# chats/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import uuid


class User(AbstractUser):
    """
    Extended User model that inherits from Django's AbstractUser.
    Adds additional fields not present in the built-in User model.
    """
    
    # Role choices
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    ]
    
    # Override the default id field to use UUID
    user_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_index=True
    )
    
    # Override email to make it unique and required
    email = models.EmailField(unique=True)
    
    # Additional fields beyond Django's built-in User model
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="User's phone number"
    )
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='guest',
        help_text="User's role in the system"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128, null=False)

    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class Conversation(models.Model):
    """
    Model to track conversations between users.
    Uses a many-to-many relationship to handle multiple participants.
    """
    
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['created_at']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ", ".join([
            user.get_full_name() or user.username 
            for user in self.participants.all()[:3]
        ])
        if self.participants.count() > 3:
            participant_names += f" and {self.participants.count() - 3} others"
        
        return f"Conversation: {participant_names}"
    
    @property
    def participant_count(self):
        """Return the number of participants in the conversation."""
        return self.participants.count()
    
    def add_participant(self, user):
        """Add a user to the conversation."""
        self.participants.add(user)
        self.save()
    
    def remove_participant(self, user):
        """Remove a user from the conversation."""
        self.participants.remove(user)
        self.save()


class Message(models.Model):
    """
    Model to store messages within conversations.
    Links to both the sender and the conversation.
    """
    
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent the message"
    )
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )
    
    message_body = models.TextField(
        help_text="Content of the message"
    )
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Add message metadata
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )
    
    message_type = models.CharField(
        max_length=20,
        default='text',
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('file', 'File'),
            ('system', 'System Message'),
        ],
        help_text="Type of message"
    )
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['conversation']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['conversation', 'sent_at']),  # Compound index for conversation timeline
        ]
        ordering = ['sent_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def preview(self):
        """Return a preview of the message (first 50 characters)."""
        return self.message_body[:50] + "..." if len(self.message_body) > 50 else self.message_body
