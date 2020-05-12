"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        self.testuser3 = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None)

        db.session.commit()

        self.testuser.followers.append(self.testuser2)
        self.testuser.followers.append(self.testuser3)
        self.testuser2.followers.append(self.testuser)

        db.session.commit()


    def test_list_users(self):
        """Does the list of users display?"""

        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)

            
    def test_list_users_with_search(self):
        """Does the list of users display with search parameter?"""

        with self.client as c:
            resp = c.get("/users?q=asdlkjfalskd")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h3>Sorry, no users found</h3>', html)

            
    def test_show_user_profile(self):
        """Does the user profile display correctly?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)


    def test_show_user_likes(self):
        """Can you view users likes when logged in?"""

        m = Message(text="Yo solo sé que no sé nada")
        self.testuser2.messages.append(m)
        self.testuser.likes.append(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Yo solo sé que no sé nada</p>', html)


    def test_following_page_logged_in(self):
        """Can a user view the following page if logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.get(f"/users/{self.testuser2.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)
            self.assertNotIn('<p>@testuser3</p>', html)


    def test_following_page_logged_out(self):
        """Can a user view the following page if logged out?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser2.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_followers_page_logged_in(self):
        """Can a user view the followers page if logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser2</p>', html)
            self.assertIn('<p>@testuser3</p>', html)


    def test_followers_page_logged_out(self):
        """Can a user view the followers page if logged out?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

