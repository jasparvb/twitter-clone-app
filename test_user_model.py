"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test model for users."""

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

        u2 = User.signup(
            username="luis9",
            email="suarez@fcb.es",
            password="Pistolero",
            image_url="/images/suarez.jpg"
        )

        db.session.commit()
        
        self.u1 = u1
        self.u2 = u2
        self.client = app.test_client()


    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages, no followers, & no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.likes), 0)


    def test_follows(self):
        self.u1.followers.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.followers), 1)
        self.assertEqual(len(self.u1.following), 0)
        self.assertEqual(len(self.u2.following), 1)
        self.assertEqual(len(self.u2.followers), 0)


    def test_is_followed(self):
        self.u1.followers.append(self.u2)
        db.session.commit()

        self.assertFalse(self.u2.is_followed_by(self.u1))
        self.assertTrue(self.u1.is_followed_by(self.u2))


    def test_is_following(self):
        self.u1.followers.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_following(self.u1))
        self.assertFalse(self.u1.is_following(self.u2))


    def test_valid_signup(self):
        """Does signup work?"""
        u = User.signup(username="terstegen1", email="terstegen@fcb.es", password="W.A.L.L", image_url="/images/terstegen.jpg")
        db.session.commit()
        test_id = u.id

        test_user = User.query.get(test_id)

        self.assertEqual(test_user.username, "terstegen1")
        self.assertEqual(test_user.email, "terstegen@fcb.es")
        self.assertNotEqual(test_user.password, "W.A.L.L")
        self.assertEqual(test_user.image_url, "/images/terstegen.jpg")


    def test_invalid_username(self):
        u = User.signup(username=None, email="terstegen@fcb.es", password="W.A.L.L", image_url="/images/terstegen.jpg")
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_username_not_unique(self):
        u = User.signup(username="messi10", email="terstegen@fcb.es", password="W.A.L.L", image_url="/images/terstegen.jpg")
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            u = User.signup(username="messi10", email="terstegen@fcb.es", password=None, image_url="/images/terstegen.jpg")


    def test_authentication_valid_input(self):
        """Does authentication work?"""
        self.assertEqual(User.authenticate("messi10", "G.O.A.T"), self.u1)


    def test_authentication_invalid_username(self):
        self.assertFalse(User.authenticate("messi11", "G.O.A.T."))


    def test_authentication_invalid_password(self):
        self.assertFalse(User.authenticate("messi10", "G.O.A.T.2"))