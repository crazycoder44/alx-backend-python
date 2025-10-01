from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification


class MessageSignalTestCase(TestCase):
    """
    Test cases for Message signals and Notification creation.
    """

    def setUp(self):
        """
        Set up test users for messaging tests.
        """
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.recipient = User.objects.create_user(
            username='recipient_user',
            email='recipient@example.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """
        Test that a message can be created successfully.
        """
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Hello, this is a test message!'
        )
        
        self.assertIsNotNone(message.message_id)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.recipient, self.recipient)
        self.assertEqual(message.message_body, 'Hello, this is a test message!')
        self.assertIsNotNone(message.sent_at)

    def test_notification_created_on_message_save(self):
        """
        Test that a notification is automatically created when a message is saved.
        """
        # Check initial notification count
        initial_notification_count = Notification.objects.count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Test message for notification'
        )
        
        # Check that notification count increased by 1
        self.assertEqual(Notification.objects.count(), initial_notification_count + 1)
        
        # Verify the notification was created for the recipient
        notification = Notification.objects.get(message=message)
        self.assertEqual(notification.user, self.recipient)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.content)
        self.assertFalse(notification.is_read)

    def test_multiple_messages_create_multiple_notifications(self):
        """
        Test that multiple messages create multiple notifications.
        """
        initial_count = Notification.objects.count()
        
        # Create multiple messages
        for i in range(3):
            Message.objects.create(
                sender=self.sender,
                recipient=self.recipient,
                message_body=f'Test message {i+1}'
            )
        
        # Check that 3 new notifications were created
        self.assertEqual(Notification.objects.count(), initial_count + 3)
        
        # Verify all notifications are for the recipient
        recipient_notifications = Notification.objects.filter(user=self.recipient)
        self.assertEqual(recipient_notifications.count(), 3)

    def test_notification_not_created_on_message_update(self):
        """
        Test that updating a message doesn't create a new notification.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Original message'
        )
        
        # Get notification count after creation
        notification_count_after_creation = Notification.objects.count()
        
        # Update the message
        message.message_body = 'Updated message'
        message.save()
        
        # Verify no new notification was created
        self.assertEqual(Notification.objects.count(), notification_count_after_creation)

    def test_notification_content(self):
        """
        Test that notification content is formatted correctly.
        """
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Testing notification content'
        )
        
        notification = Notification.objects.get(message=message)
        expected_content = f"You have a new message from {self.sender.username}"
        self.assertEqual(notification.content, expected_content)

    def test_mark_notification_as_read(self):
        """
        Test the mark_as_read method on Notification model.
        """
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        self.assertFalse(notification.is_read)
        
        # Mark as read
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertTrue(notification.is_read)

    def test_multiple_recipients_different_notifications(self):
        """
        Test that different recipients receive separate notifications.
        """
        recipient2 = User.objects.create_user(
            username='recipient2_user',
            email='recipient2@example.com',
            password='testpass123'
        )
        
        # Send message to first recipient
        message1 = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Message to recipient 1'
        )
        
        # Send message to second recipient
        message2 = Message.objects.create(
            sender=self.sender,
            recipient=recipient2,
            message_body='Message to recipient 2'
        )
        
        # Check notifications
        notification1 = Notification.objects.get(message=message1)
        notification2 = Notification.objects.get(message=message2)
        
        self.assertEqual(notification1.user, self.recipient)
        self.assertEqual(notification2.user, recipient2)
        self.assertNotEqual(notification1.notification_id, notification2.notification_id)

    def test_message_string_representation(self):
        """
        Test the __str__ method of Message model.
        """
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Test message'
        )
        
        expected_str = f"Message from {self.sender.username} to {self.recipient.username} at {message.sent_at}"
        self.assertEqual(str(message), expected_str)

    def test_notification_string_representation(self):
        """
        Test the __str__ method of Notification model.
        """
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            message_body='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        expected_str = f"Notification for {self.recipient.username}: {notification.content[:50]}"
        self.assertEqual(str(notification), expected_str)