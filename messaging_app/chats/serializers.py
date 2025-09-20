from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Conversation, Message, MessageReadStatus


# User Serializers
class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for public user information.
    Used in nested relationships to avoid exposing sensitive data.
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'full_name', 'email', 'role', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with additional fields for authenticated users.
    """
    full_name = serializers.ReadOnlyField()
    conversation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'role', 'created_at', 'updated_at',
            'conversation_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def get_conversation_count(self, obj):
        """Return the number of conversations the user participates in."""
        return obj.conversations.count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration/creation.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'phone_number', 'role', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


# Message Serializers
class MessageSerializer(serializers.ModelSerializer):
    """
    Basic message serializer with sender information.
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True)
    preview = serializers.ReadOnlyField()
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation', 
            'message_body', 'message_type', 'sent_at', 'is_read', 'preview'
        ]
        read_only_fields = ['message_id', 'sent_at']
    
    def validate_sender_id(self, value):
        """Validate that sender exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid sender ID.")
        return value


class MessageDetailSerializer(serializers.ModelSerializer):
    """
    Detailed message serializer with read status information.
    """
    sender = UserSerializer(read_only=True)
    read_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'conversation', 'message_body', 
            'message_type', 'sent_at', 'is_read', 'read_by'
        ]
        read_only_fields = ['message_id', 'sent_at']
    
    def get_read_by(self, obj):
        """Return list of users who have read this message."""
        read_statuses = MessageReadStatus.objects.filter(message=obj).select_related('user')
        return [
            {
                'user_id': status.user.id,
                'username': status.user.username,
                'full_name': status.user.full_name,
                'read_at': status.read_at
            }
            for status in read_statuses
        ]


# Conversation Serializers
class ConversationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing conversations with basic information.
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'title', 'participants', 'participant_count',
            'created_at', 'updated_at', 'is_active', 'last_message', 'unread_count'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Return the last message in the conversation."""
        last_message = obj.messages.last()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender': last_message.sender.full_name,
                'preview': last_message.preview,
                'sent_at': last_message.sent_at,
                'message_type': last_message.message_type
            }
        return None
    
    def get_unread_count(self, obj):
        """Return count of unread messages for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed conversation serializer with nested messages.
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    participant_count = serializers.ReadOnlyField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'title', 'participants', 'participant_ids',
            'participant_count', 'messages', 'message_count', 'created_at', 
            'updated_at', 'is_active'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """Return total number of messages in conversation."""
        return obj.messages.count()
    
    def validate_participant_ids(self, value):
        """Validate that all participant IDs exist."""
        if value:
            existing_users = User.objects.filter(id__in=value).count()
            if existing_users != len(value):
                raise serializers.ValidationError("One or more participant IDs are invalid.")
        return value
    
    def create(self, validated_data):
        """Create conversation and add participants."""
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        
        if participant_ids:
            participants = User.objects.filter(id__in=participant_ids)
            conversation.participants.set(participants)
        
        return conversation
    
    def update(self, instance, validated_data):
        """Update conversation and handle participant changes."""
        participant_ids = validated_data.pop('participant_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update participants if provided
        if participant_ids is not None:
            participants = User.objects.filter(id__in=participant_ids)
            instance.participants.set(participants)
        
        return instance


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new conversations.
    """
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of user IDs to include in the conversation"
    )
    
    class Meta:
        model = Conversation
        fields = ['title', 'participant_ids']
    
    def validate_participant_ids(self, value):
        """Validate participant IDs and ensure they exist."""
        # Remove duplicates
        value = list(set(value))
        
        # Check if all users exist
        existing_users = User.objects.filter(id__in=value)
        if existing_users.count() != len(value):
            invalid_ids = set(value) - set(existing_users.values_list('id', flat=True))
            raise serializers.ValidationError(f"Invalid user IDs: {list(invalid_ids)}")
        
        return value
    
    def create(self, validated_data):
        """Create conversation with participants."""
        participant_ids = validated_data.pop('participant_ids')
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants
        participants = User.objects.filter(id__in=participant_ids)
        conversation.participants.set(participants)
        
        return conversation


# Message Read Status Serializer
class MessageReadStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for message read status tracking.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReadStatus
        fields = ['message', 'user', 'read_at']
        read_only_fields = ['read_at']


# Nested serializers for specific use cases
class ConversationWithRecentMessagesSerializer(serializers.ModelSerializer):
    """
    Conversation serializer with limited recent messages (for performance).
    """
    participants = UserSerializer(many=True, read_only=True)
    recent_messages = serializers.SerializerMethodField()
    participant_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'title', 'participants', 'participant_count',
            'recent_messages', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_recent_messages(self, obj):
        """Return last 20 messages in the conversation."""
        recent_messages = obj.messages.select_related('sender').order_by('-sent_at')[:20]
        return MessageSerializer(recent_messages, many=True).data