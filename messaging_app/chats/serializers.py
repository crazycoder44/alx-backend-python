from rest_framework import serializers
from .models import User, Conversation, Message


from rest_framework import serializers

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    conversation_count = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'role', 'created_at', 'updated_at',
            'conversation_count', 'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'conversation_count']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_conversation_count(self, obj):
        return obj.conversations.count()

    def validate(self, attrs):
        if self.context.get('request') and self.context['request'].method == 'POST':
            password = attrs.get('password')
            password_confirm = attrs.get('password_confirm')
            if password != password_confirm:
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

# Message Serializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    preview = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation',
            'message_body', 'message_type', 'sent_at', 'is_read',
            'preview'
        ]
        read_only_fields = ['message_id', 'sent_at', 'preview']

    def get_preview(self, obj):
        return obj.message_body[:50] + '...' if len(obj.message_body) > 50 else obj.message_body

    def validate_sender_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Invalid sender ID.")
        return value

    def create(self, validated_data):
        sender_id = validated_data.pop('sender_id', None)
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
    participant_count = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField(read_only=True)
    recent_messages = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'title', 'participants', 'participant_ids',
            'participant_count', 'last_message', 'unread_count',
            'messages', 'message_count', 'recent_messages',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']

    def get_participant_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender': f"{last_message.sender.first_name} {last_message.sender.last_name}",
                'preview': last_message.message_body[:50] + '...' if len(last_message.message_body) > 50 else last_message.message_body,
                'sent_at': last_message.sent_at,
                'message_type': last_message.message_type
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_recent_messages(self, obj):
        recent_messages = obj.messages.select_related('sender').order_by('-sent_at')[:20]
        return MessageSerializer(recent_messages, many=True, context=self.context).data

    def validate_participant_ids(self, value):
        value = list(set(value))  # remove duplicates
        existing_users = User.objects.filter(user_id__in=value)
        if existing_users.count() != len(value):
            invalid_ids = set(value) - set(existing_users.values_list('user_id', flat=True))
            raise serializers.ValidationError(f"Invalid user IDs: {list(invalid_ids)}")
        return value

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        return conversation

    def update(self, instance, validated_data):
        participant_ids = validated_data.pop('participant_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if participant_ids is not None:
            participants = User.objects.filter(user_id__in=participant_ids)
            instance.participants.set(participants)
        return instance