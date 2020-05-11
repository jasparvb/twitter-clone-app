"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:41361@localhost/warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup(
            username="messi10",
            email="messi@fcb.es",
            password="G.O.A.T",
            image_url="/images/messi.jpg"
        )

        db.session.commit()

        self.u1 = u1
        self.client = app.test_client()


    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="Yo solo sé que no sé nada",
            user_id=self.u1.id
        )

        db.session.add(m)
        db.session.commit()

        # User should have no messages, no followers, & no likes
        self.assertEqual(len(self.u1.messages), 1)


    def test_valid_message(self):
        """Does creating a message work?"""
        m = Message(text="Yo solo sé que no sé nada")
        self.u1.messages.append(m)
        db.session.commit()
        test_id = m.id

        test_message = Message.query.get(test_id)

        self.assertEqual(test_message.text, "Yo solo sé que no sé nada")
        self.assertTrue(test_message.timestamp)
        self.assertEqual(test_message.user_id, self.u1.id)


    def test_invalid_text(self):
        m = Message(text=None)
        self.u1.messages.append(m)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_likes(self):
        m = Message(text="Yo solo sé que no sé nada")
        self.u1.messages.append(m)
        u = User.signup(username="terstegen1", email="terstegen@fcb.es", password="W.A.L.L", image_url="/images/terstegen.jpg")
        db.session.add_all([m, u])
        db.session.commit()

        u.likes.append(m)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == u.id).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m.id)
      