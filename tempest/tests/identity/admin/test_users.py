# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nose.plugins.attrib import attr
import unittest2 as unittest
from tempest.tests import utils

from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.identity import base


class UsersTestBase(object):

    alt_user = rand_name('test_user_')
    alt_password = rand_name('pass_')
    alt_email = alt_user + '@testmail.tm'
    alt_tenant = rand_name('test_tenant_')
    alt_description = rand_name('desc_')

    @attr(type='smoke')
    def test_create_user(self):
        """Create a user"""
        self.data.setup_test_tenant()
        resp, user = self.client.create_user(self.alt_user, self.alt_password,
                                             self.data.tenant['id'],
                                             self.alt_email)
        self.data.users.append(user)
        self.assertEqual('200', resp['status'])
        self.assertEqual(self.alt_user, user['name'])

    @attr(type='negative')
    def test_create_user_by_unauthorized_user(self):
        """Non-admin should not be authorized to create a user"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.create_user, self.alt_user,
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @attr(type='negative')
    def test_create_user_with_empty_name(self):
        """User with an empty name should not be created"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user, '',
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @attr(type='negative')
    @unittest.skip("Until Bug 966251 is fixed")
    def test_create_user_with_name_length_over_64(self):
        """Length of user name filed should be restricted to 64 characters"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          'a' * 65, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

    @attr(type='negative')
    def test_create_user_with_duplicate_name(self):
        """Duplicate user should not be created"""
        self.data.setup_test_user()
        self.assertRaises(exceptions.Duplicate, self.client.create_user,
                          self.data.test_user, self.data.test_password,
                          self.data.tenant['id'], self.data.test_email)

    @attr(type='negative')
    @unittest.skip("Until Bug 999084 is fixed")
    def test_create_user_with_empty_password(self):
        """User with an empty password should not be created"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          self.alt_user, '', self.data.tenant['id'],
                          self.alt_email)

    @attr(type='nagative')
    @unittest.skip("Until Bug 999084 is fixed")
    def test_create_user_with_long_password(self):
        """User having password exceeding max length should not be created"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          self.alt_user, 'a' * 65, self.data.tenant['id'],
                          self.alt_email)

    @attr(type='negative')
    @unittest.skip("Until Bug 999084 is fixed")
    def test_create_user_with_invalid_email_format(self):
        """Email format should be validated while creating a user"""
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          self.alt_user, '', self.data.tenant['id'], '12345')

    @attr(type='negative')
    def test_create_user_for_non_existant_tenant(self):
        """Attempt to create a user in a non-existent tenant should fail"""
        self.assertRaises(exceptions.NotFound, self.client.create_user,
                          self.alt_user, self.alt_password, '49ffgg99999',
                          self.alt_email)

    @attr(type='negative')
    def test_create_user_request_without_a_token(self):
        """Request to create a user without a valid token should fail"""
        self.data.setup_test_tenant()
        # Get the token of the current client
        token = self.client.get_auth()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.create_user,
                          self.alt_user, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

        # Unset the token to allow further tests to generate a new token
        self.client.clear_auth()

    @attr(type='smoke')
    def test_delete_user(self):
        """Delete a user"""
        self.data.setup_test_tenant()
        resp, user = self.client.create_user('user_1234', self.alt_password,
                                             self.data.tenant['id'],
                                             self.alt_email)
        resp, body = self.client.delete_user(user['id'])
        self.assertEquals('204', resp['status'])

    @attr(type='negative')
    def test_delete_users_by_unauthorized_user(self):
        """Non admin user should not be authorized to delete a user"""
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.delete_user,
                          self.data.user['id'])

    @attr(type='negative')
    def test_delete_non_existant_user(self):
        """Attempt to delete a non-existent user should fail"""
        self.assertRaises(exceptions.NotFound, self.client.delete_user,
                          'junk12345123')

    @attr(type='smoke')
    def test_user_authentication(self):
        """Valid user's token is authenticated"""
        self.data.setup_test_user()
        # Get a token
        self.token_client.auth(self.data.test_user, self.data.test_password,
                               self.data.test_tenant)
        # Re-auth
        resp, body = self.token_client.auth(self.data.test_user,
                                            self.data.test_password,
                                            self.data.test_tenant)
        self.assertEqual('200', resp['status'])

    @attr(type='negative')
    def test_authentication_for_disabled_user(self):
        """Disabled user's token should not get authenticated"""
        self.data.setup_test_user()
        self.disable_user(self.data.test_user)
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @attr(type='negative')
    @unittest.skip('Until Bug 988920 is fixed')
    def test_authentication_when_tenant_is_disabled(self):
        """User's token for a disabled tenant should not be authenticated"""
        self.data.setup_test_user()
        self.disable_tenant(self.data.test_tenant)
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @attr(type='negative')
    @unittest.skip('Until Bug 988920 is fixed')
    def test_authentication_with_invalid_tenant(self):
        """User's token for an invalid tenant should not be authenticated"""
        self.data.setup_one_user()
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          'junktenant1234')

    @attr(type='negative')
    def test_authentication_with_invalid_username(self):
        """Non-existent user's token should not get authenticated"""
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          'junkuser123', self.data.test_password,
                          self.data.test_tenant)

    @attr(type='negative')
    def test_authentication_with_invalid_password(self):
        """User's token with invalid password should not be authenticated"""
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user, 'junkpass1234',
                          self.data.test_tenant)

    @attr(type='positive')
    def test_authentication_request_without_token(self):
        """Request for token authentication with a valid token in header"""
        self.data.setup_test_user()
        self.token_client.auth(self.data.test_user, self.data.test_password,
                               self.data.test_tenant)
        # Get the token of the current client
        token = self.client.get_auth()
        # Delete the token from database
        self.client.delete_token(token)
        # Re-auth
        resp, body = self.token_client.auth(self.data.test_user,
                                            self.data.test_password,
                                            self.data.test_tenant)
        self.assertEqual('200', resp['status'])
        self.client.clear_auth()

    @attr(type='smoke')
    def test_get_users(self):
        """Get a list of users and find the test user"""
        self.data.setup_test_user()
        resp, users = self.client.get_users()
        self.assertIn(self.data.test_user, [u['name'] for u in users],
                      "Could not find %s" % self.data.test_user)

    @attr(type='negative')
    def test_get_users_by_unauthorized_user(self):
        """Non admin user should not be authorized to get user list"""
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.get_users)

    @attr(type='negative')
    def test_get_users_request_without_token(self):
        """Request to get list of users without a valid token should fail"""
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.get_users)
        self.client.clear_auth()

    @attr(type='positive')
    def test_list_users_for_tenant(self):
        """Return a list of all users for a tenant"""
        self.data.setup_test_tenant()
        user_ids = list()
        fetched_user_ids = list()
        resp, user1 = self.client.create_user('tenant_user1', 'password1',
                                              self.data.tenant['id'],
                                              'user1@123')
        user_ids.append(user1['id'])
        self.data.users.append(user1)
        resp, user2 = self.client.create_user('tenant_user2', 'password2',
                                              self.data.tenant['id'],
                                              'user2@123')
        user_ids.append(user2['id'])
        self.data.users.append(user2)
        #List of users for the respective tenant ID
        resp, body = self.client.list_users_for_tenant(self.data.tenant['id'])
        self.assertTrue(resp['status'].startswith('2'))
        for i in body:
            fetched_user_ids.append(i['id'])
        #verifying the user Id in the list
        missing_users =\
            [user for user in user_ids if user not in fetched_user_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @attr(type='positive')
    def test_list_users_with_roles_for_tenant(self):
        """Return list of users on tenant when roles are assigned to users"""
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        #Assigning roles to two users
        user_ids = list()
        fetched_user_ids = list()
        user_ids.append(user['id'])
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        resp, second_user = self.client.create_user('second_user', 'password1',
                                                    self.data.tenant['id'],
                                                    'user1@123')
        user_ids.append(second_user['id'])
        self.data.users.append(second_user)
        self.client.assign_user_role(tenant['id'], second_user['id'],
                                     role['id'])
        #List of users with roles for the respective tenant ID
        resp, body = self.client.list_users_for_tenant(self.data.tenant['id'])
        self.assertTrue(resp['status'].startswith('2'))
        for i in body:
            fetched_user_ids.append(i['id'])
        #verifying the user Id in the list
        missing_users =\
            [user for user in user_ids if user not in fetched_user_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @attr(type='negative')
    def test_list_users_with_invalid_tenant(self):
        """
        Should not be able to return a list of all
        users for a nonexistant tenant
        """
        #Assign invalid tenant ids
        invalid_id = list()
        invalid_id.append(rand_name('999'))
        invalid_id.append('alpha')
        invalid_id.append(rand_name("dddd@#%%^$"))
        invalid_id.append('!@#()$%^&*?<>{}[]')
        #List the users with invalid tenant id
        fail = list()
        for invalid in invalid_id:
            try:
                resp, body = self.client.list_users_for_tenant(invalid)
            except exceptions.NotFound:
                pass
            else:
                fail.append(invalid)
        if len(fail) != 0:
            self.fail('Should raise Not Found when list users with invalid'
                      'tenant ids %s' % fail)


class UsersTestJSON(base.BaseIdentityAdminTestJSON,
                    UsersTestBase):
    @classmethod
    @utils.skip('Not supported in Y! environment')
    def setUpClass(cls):
        super(UsersTestJSON, cls).setUpClass()


class UsersTestXML(base.BaseIdentityAdminTestXML, UsersTestBase):
    @classmethod
    @utils.skip('Not supported in Y! environment')
    def setUpClass(cls):
        super(UsersTestXML, cls).setUpClass()
