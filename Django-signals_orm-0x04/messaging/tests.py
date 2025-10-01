from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message, Notification, MessageHistory


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
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """
        Test that a message can be created successfully.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello, this is a test message!'
        )
        
        self.assertIsNotNone(message.message_id)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, 'Hello, this is a test message!')
        self.assertIsNotNone(message.timestamp)
        self.assertFalse(message.edited)

    def test_notification_created_on_message_save(self):
        """
        Test that a notification is automatically created when a message is saved.
        """
        # Check initial notification count
        initial_notification_count = Notification.objects.count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message for notification'
        )
        
        # Check that notification count increased by 1
        self.assertEqual(Notification.objects.count(), initial_notification_count + 1)
        
        # Verify the notification was created for the receiver
        notification = Notification.objects.get(message=message)
        self.assertEqual(notification.user, self.receiver)
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
                receiver=self.receiver,
                content=f'Test message {i+1}'
            )
        
        # Check that 3 new notifications were created
        self.assertEqual(Notification.objects.count(), initial_count + 3)
        
        # Verify all notifications are for the receiver
        receiver_notifications = Notification.objects.filter(user=self.receiver)
        self.assertEqual(receiver_notifications.count(), 3)

    def test_notification_not_created_on_message_update(self):
        """
        Test that updating a message doesn't create a new notification.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original message'
        )
        
        # Get notification count after creation
        notification_count_after_creation = Notification.objects.count()
        
        # Update the message
        message.content = 'Updated message'
        message.save()
        
        # Verify no new notification was created
        self.assertEqual(Notification.objects.count(), notification_count_after_creation)

    def test_notification_content(self):
        """
        Test that notification content is formatted correctly.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Testing notification content'
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
            receiver=self.receiver,
            content='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        self.assertFalse(notification.is_read)
        
        # Mark as read
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertTrue(notification.is_read)

    def test_multiple_receivers_different_notifications(self):
        """
        Test that different receivers receive separate notifications.
        """
        receiver2 = User.objects.create_user(
            username='receiver2_user',
            email='receiver2@example.com',
            password='testpass123'
        )
        
        # Send message to first receiver
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Message to receiver 1'
        )
        
        # Send message to second receiver
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=receiver2,
            content='Message to receiver 2'
        )
        
        # Check notifications
        notification1 = Notification.objects.get(message=message1)
        notification2 = Notification.objects.get(message=message2)
        
        self.assertEqual(notification1.user, self.receiver)
        self.assertEqual(notification2.user, receiver2)
        self.assertNotEqual(notification1.notification_id, notification2.notification_id)

    def test_message_string_representation(self):
        """
        Test the __str__ method of Message model.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        expected_str = f"Message from {self.sender.username} to {self.receiver.username} at {message.timestamp}"
        self.assertEqual(str(message), expected_str)

    def test_notification_string_representation(self):
        """
        Test the __str__ method of Notification model.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        expected_str = f"Notification for {self.receiver.username}: {notification.content[:50]}"
        self.assertEqual(str(notification), expected_str)


class MessageEditSignalTestCase(TestCase):
    """
    Test cases for Message edit signals and MessageHistory creation.
    """

    def setUp(self):
        """
        Set up test users and message for edit tests.
        """
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_edit_creates_history(self):
        """
        Test that editing a message creates a history entry.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        # Verify no history exists yet
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)
        
        # Edit the message
        message.content = 'Updated content'
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        
        # Verify history was created
        self.assertEqual(MessageHistory.objects.count(), 1)
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.last_edited_at)
        
        # Verify history content
        history = MessageHistory.objects.first()
        self.assertEqual(history.message, message)
        self.assertEqual(history.old_content, 'Original content')
        self.assertEqual(history.edited_by, self.sender)

    def test_multiple_edits_create_multiple_history_entries(self):
        """
        Test that multiple edits create multiple history entries.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Version 1'
        )
        
        # First edit
        message.content = 'Version 2'
        message.save()
        
        # Second edit
        message.content = 'Version 3'
        message.save()
        
        # Third edit
        message.content = 'Version 4'
        message.save()
        
        # Verify 3 history entries were created
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 3)
        
        # Verify history entries have correct old content
        histories = MessageHistory.objects.filter(message=message).order_by('edited_at')
        self.assertEqual(histories[0].old_content, 'Version 1')
        self.assertEqual(histories[1].old_content, 'Version 2')
        self.assertEqual(histories[2].old_content, 'Version 3')

    def test_no_history_created_when_content_unchanged(self):
        """
        Test that no history is created when message is saved without content change.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        # Save without changing content
        message.save()
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)

    def test_message_edited_flag(self):
        """
        Test that the edited flag is set correctly.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        self.assertFalse(message.edited)
        self.assertIsNone(message.last_edited_at)
        
        # Edit the message
        message.content = 'Edited content'
        message.save()
        message.refresh_from_db()
        
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.last_edited_at)

    def test_message_history_string_representation(self):
        """
        Test the __str__ method of MessageHistory model.
        """
        # Create and edit a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        message.content = 'Updated content'
        message.save()
        
        # Get the history entry
        history = MessageHistory.objects.first()
        expected_str = f"History for message {message.message_id} edited at {history.edited_at}"
        self.assertEqual(str(history), expected_str)

    def test_message_history_relationship(self):
        """
        Test that message history is accessible through the message relationship.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Version 1'
        )
        
        # Edit multiple times
        message.content = 'Version 2'
        message.save()
        
        message.content = 'Version 3'
        message.save()
        
        # Access history through message relationship
        history_entries = message.history.all()
        self.assertEqual(history_entries.count(), 2)

    def test_new_message_has_no_history(self):
        """
        Test that creating a new message doesn't create history.
        """
        initial_history_count = MessageHistory.objects.count()
        
        # Create a new message
        Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='New message'
        )
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), initial_history_count)


class UserDeletionSignalTestCase(TestCase):
    """
    Test cases for User deletion signals and cleanup of related data.
    """

    def setUp(self):
        """
        Set up test users and data for deletion tests.
        """
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_user_deletion_removes_sent_messages(self):
        """
        Test that deleting a user removes all messages they sent.
        """
        # Create messages sent by user1
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message from user1 to user2'
        )
        message2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            content='Message from user1 to user3'
        )
        
        # Verify messages exist
        self.assertEqual(Message.objects.filter(sender=self.user1).count(), 2)
        
        # Delete user1
        self.user1.delete()
        
        # Verify messages were deleted
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 0)

    def test_user_deletion_removes_received_messages(self):
        """
        Test that deleting a user removes all messages they received.
        """
        # Create messages received by user2
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message to user2 from user1'
        )
        message2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Message to user2 from user3'
        )
        
        # Verify messages exist
        self.assertEqual(Message.objects.filter(receiver=self.user2).count(), 2)
        
        # Delete user2
        self.user2.delete()
        
        # Verify messages were deleted
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 0)

    def test_user_deletion_removes_notifications(self):
        """
        Test that deleting a user removes all their notifications.
        """
        # Create messages which will create notifications
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message 1'
        )
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Message 2'
        )
        
        # Verify notifications were created
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 2)
        
        # Delete user2
        self.user2.delete()
        
        # Verify notifications were deleted
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 0)

    def test_user_deletion_clears_message_history_references(self):
        """
        Test that deleting a user clears edited_by references in message history.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Original content'
        )
        
        # Edit the message to create history
        message.content = 'Updated content'
        message.save()
        
        # Verify history was created with edited_by
        history = MessageHistory.objects.first()
        self.assertEqual(history.edited_by, self.user1)
        
        # Delete user1
        self.user1.delete()
        
        # Since the message is deleted with user1, history should also be deleted via CASCADE
        self.assertEqual(MessageHistory.objects.count(), 0)

    def test_user_deletion_does_not_affect_other_users_data(self):
        """
        Test that deleting one user doesn't affect other users' data.
        """
        # Create messages between different users
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message from user1 to user2'
        )
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user3,
            content='Message from user2 to user3'
        )
        
        # Delete user1
        self.user1.delete()
        
        # Verify message1 was deleted but message2 still exists
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 1)
        
        # Verify user2 and user3 still exist
        self.assertTrue(User.objects.filter(username='user2').exists())
        self.assertTrue(User.objects.filter(username='user3').exists())

    def test_cascade_deletion_of_message_history(self):
        """
        Test that message history is deleted when associated message is deleted.
        """
        # Create and edit a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Original content'
        )
        
        message.content = 'Updated content'
        message.save()
        
        # Verify history exists
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 1)
        
        # Delete the user (which deletes the message)
        self.user1.delete()
        
        # Verify history was also deleted (CASCADE)
        self.assertEqual(MessageHistory.objects.count(), 0)

    def test_multiple_users_deletion(self):
        """
        Test deleting multiple users cleans up all their data.
        """
        # Create messages between all users
        Message.objects.create(sender=self.user1, receiver=self.user2, content='Msg 1')
        Message.objects.create(sender=self.user2, receiver=self.user3, content='Msg 2')
        Message.objects.create(sender=self.user3, receiver=self.user1, content='Msg 3')
        
        # Verify initial counts
        self.assertEqual(Message.objects.count(), 3)
        self.assertEqual(Notification.objects.count(), 3)
        
        # Delete all users
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        
        # Verify all messages and notifications were deleted
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)


class UserDeletionViewTestCase(TestCase):
    """
    Test cases for user deletion views.
    """

    def setUp(self):
        """
        Set up test client and users.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123'
        )

    def test_delete_user_account_view_requires_login(self):
        """
        Test that delete account view requires authentication.
        """
        response = self.client.get(reverse('messaging:delete_user_account'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_delete_user_account_view_displays_confirmation(self):
        """
        Test that delete account view displays confirmation page.
        """
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data for the user
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message'
        )
        
        response = self.client.get(reverse('messaging:delete_user_account'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('sent_messages_count', response.context)

    def test_delete_user_requires_post(self):
        """
        Test that delete user endpoint only accepts POST requests.
        """
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('messaging:delete_user'))
        # Should return 405 Method Not Allowed or redirect
        self.assertIn(response.status_code, [302, 405])

    def test_delete_user_with_confirmation(self):
        """
        Test successful user deletion with proper confirmation.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message'
        )
        
        # Verify user exists
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Delete user with confirmation
        response = self.client.post(
            reverse('messaging:delete_user'),
            {'confirmation': 'delete'}
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify user was deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_delete_user_without_proper_confirmation(self):
        """
        Test that deletion fails without proper confirmation.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Try to delete without proper confirmation
        response = self.client.post(
            reverse('messaging:delete_user'),
            {'confirmation': 'wrong'}
        )
        
        # Should redirect back
        self.assertEqual(response.status_code, 302)
        
        # Verify user still exists
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_data_summary_api(self):
        """
        Test user data summary API endpoint.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message 1'
        )
        Message.objects.create(
            sender=self.other_user,
            receiver=self.user,
            content='Test message 2'
        )
        
        response = self.client.get(reverse('messaging:user_data_summary'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['sent_messages_count'], 1)
        self.assertEqual(data['received_messages_count'], 1)
        self.assertEqual(data['notifications_count'], 1)  # One notification for received message