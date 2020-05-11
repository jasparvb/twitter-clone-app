"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:41361@localhost/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_add_message_not_logged_in(self):
        """Can you add a message when not logged in?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_add_message_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 111111

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_show_message(self):
        """Does the message display?"""

        m = Message(text="Yo solo sé que no sé nada")
        self.testuser.messages.append(m)
        db.session.commit()
        test_id = m.id

        with self.client as c:
            resp = c.get(f'/messages/{test_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p class="single-message">Yo solo sé que no sé nada</p>', html)


    def test_delete_message(self):
        """Can user delete a message?"""
        m = Message(text="Yo solo sé que no sé nada")
        self.testuser.messages.append(m)
        db.session.commit()
        test_id = m.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{test_id}/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(test_id)
            self.assertIsNone(m)


    def test_delete_message_invalid_user(self):
        """Can user delete a message that is not his?"""
        m = Message(text="Yo solo sé que no sé nada")
        self.testuser.messages.append(m)
        db.session.commit()
        test_id = m.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 11111

            resp = c.post(f"/messages/{test_id}/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

            m = Message.query.get(test_id)
            self.assertIsNotNone(m)


    def test_delete_message_not_logged_in(self):
        """Can you delete a message when not logged in?"""
        m = Message(text="Yo solo sé que no sé nada")
        self.testuser.messages.append(m)
        db.session.commit()
        test_id = m.id

        with self.client as c:

            resp = c.post(f"/messages/{test_id}/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

            m = Message.query.get(test_id)
            self.assertIsNotNone(m)
