# chats/serializers.py

from rest_framework import serializers
from .models import User, Conversation, Message


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    conversation_count = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'role', 'created_at', 'updated_at',
            'conversation_count', 'password', 'password_confirm'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at', 'full_name', 'conversation_count']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_conversation_count(self, obj):
        return obj.conversations.count()

    def validate(self, attrs):
        if self.context.get('request') and self.context['request'].method == 'POST':
            password = attrs.get('password')
            password_confirm = attrs.get('password_confirm')
            if password and password != password_confirm:
                raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
    

# Simplified User Serializer for nested relationships
class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'email', 'first_name', 'last_name', 'full_name', 'role']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


# Message Serializer
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    preview = serializers.SerializerMethodField()
    conversation_id = serializers.UUIDField(source='conversation.conversation_id', read_only=True)

    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation', 'conversation_id',
            'message_body', 'message_type', 'sent_at', 'is_read',
            'preview'
        ]
        read_only_fields = ['message_id', 'sent_at', 'preview', 'sender']

    def get_preview(self, obj):
        return obj.message_body[:50] + '...' if len(obj.message_body) > 50 else obj.message_body

    def validate_sender_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Invalid sender ID.")
        return value

    def create(self, validated_data):
        # Remove sender_id from nested data if present
        sender_data = validated_data.pop('sender', None)
        if sender_data:
            sender_id = sender_data.get('user_id')
            if sender_id:
                validated_data['sender'] = User.objects.get(user_id=sender_id)
        return super().create(validated_data)


# Conversation Serializers
class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to include in the conversation"
    )
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    recent_messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids',
            'participant_count', 'last_message', 'unread_count',
            'messages', 'message_count', 'recent_messages',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']

    def get_participant_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender_name': last_message.sender.full_name,
                'sender_id': last_message.sender.user_id,
                'preview': last_message.message_body[:50] + '...' if len(last_message.message_body) > 50 else last_message.message_body,
                'sent_at': last_message.sent_at,
                'message_type': last_message.message_type,
                'is_read': last_message.is_read
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_recent_messages(self, obj):
        # Get the last 10 messages in the conversation
        recent_messages = obj.messages.select_related('sender').order_by('-sent_at')[:20]
        # Reverse to show in chronological order
        recent_messages = list(reversed(recent_messages))
        return MessageSerializer(recent_messages, many=True, context=self.context).data

    def get_messages(self, obj):
        messages = obj.messages.select_related('sender').order_by('sent_at')
        return MessageSerializer(messages, many=True, context=self.context).data

    def get_message_count(self, obj):
        return obj.messages.count()

    def validate_participant_ids(self, value):
        """Ensure participants are valid, unique, and include creator."""
        request = self.context.get('request')

        if not value:
            raise serializers.ValidationError("At least one participant must be specified.")
        
        value = list(set(value))  # remove duplicates

        existing_users = User.objects.filter(user_id__in=value)
        existing_ids = set(str(uid) for uid in existing_users.values_list("user_id", flat=True))

        # Detect invalid IDs
        invalid_ids = set(map(str, value)) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"Invalid user IDs: {list(invalid_ids)}")

        # Ensure current user is always a participant
        if request and request.user.is_authenticated:
            if str(request.user.user_id) not in existing_ids:
                value.append(str(request.user.user_id))
        return value

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)

        participants = list(User.objects.filter(user_id__in=participant_ids))

        # Ensure the current user (if available) is added as a participant
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user not in participants:
                participants.append(request.user)

        conversation.participants.set(participants)
        return conversation

    def update(self, instance, validated_data):
        participant_ids = validated_data.pop('participant_ids', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update participants if provided
        if participant_ids is not None:
            participants = list(User.objects.filter(user_id__in=participant_ids))

            # Always keep the current user in the conversation
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                if request.user not in participants:
                    participants.append(request.user)

            instance.participants.set(participants)

        return instance
    

# Detailed Conversation Serializer (includes all messages)
class ConversationDetailSerializer(ConversationSerializer):
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages', 'message_count']

    def get_messages(self, obj):
        messages = obj.messages.select_related('sender').order_by('sent_at')
        return MessageSerializer(messages, many=True, context=self.context).data

    def get_message_count(self, obj):
        return obj.messages.count()


# Serializer for creating messages within a conversation (nested route)
class ConversationMessageSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    preview = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'message_body', 'message_type', 
            'sent_at', 'is_read', 'preview'
        ]
        read_only_fields = ['message_id', 'sent_at', 'preview', 'sender']

    def get_preview(self, obj):
        return obj.message_body[:50] + '...' if len(obj.message_body) > 50 else obj.message_body

    def create(self, validated_data):
        # The conversation and sender will be set by the view
        return super().create(validated_data)