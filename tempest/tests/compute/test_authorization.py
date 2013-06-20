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
from nose.tools import raises
import unittest2 as unittest

from tempest import openstack
from tempest.common.utils.data_utils import rand_name, parse_image_id
from tempest import exceptions
from tempest.tests.compute.base import BaseComputeTest
from tempest.tests import compute


class AuthorizationTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        if not compute.MULTI_USER:
            msg = "Need >1 user"
            raise unittest.SkipTest(msg)

        super(AuthorizationTest, cls).setUpClass()

        cls.client = cls.os.servers_client
        cls.images_client = cls.os.images_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_client = cls.os.security_groups_client
        cls.console_outputs_client = cls.os.console_outputs_client

        if cls.config.compute.allow_tenant_isolation:
            creds = cls._get_isolated_creds()
            username, tenant_name, password = creds
            cls.alt_manager = openstack.Manager(username=username,
                                                password=password,
                                                tenant_name=tenant_name)
        else:
            # Use the alt_XXX credentials in the config file
            cls.alt_manager = openstack.AltManager()

        cls.alt_client = cls.alt_manager.servers_client
        cls.alt_images_client = cls.alt_manager.images_client
        cls.alt_keypairs_client = cls.alt_manager.keypairs_client
        cls.alt_security_client = cls.alt_manager.security_groups_client
        cls.alt_console_outputs_client = cls.alt_manager.console_outputs_client

        cls.alt_security_client._set_auth()
        name = rand_name('server')
        resp, server = cls.client.create_server(name, cls.image_ref,
                                                cls.flavor_ref)
        cls.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, cls.server = cls.client.get_server(server['id'])

        name = rand_name('image')
        resp, body = cls.client.create_image(server['id'], name)
        image_id = parse_image_id(resp['location'])
        cls.images_client.wait_for_image_resp_code(image_id, 200)
        cls.images_client.wait_for_image_status(image_id, 'ACTIVE')
        resp, cls.image = cls.images_client.get_image(image_id)

        cls.keypairname = rand_name('keypair')
        resp, keypair = \
            cls.keypairs_client.create_keypair(cls.keypairname)

        name = rand_name('security')
        description = rand_name('description')
        resp, cls.security_group = \
        cls.security_client.create_security_group(name, description)

        parent_group_id = cls.security_group['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        resp, cls.rule =\
        cls.security_client.create_security_group_rule(
                                        parent_group_id,
                                        ip_protocol, from_port,
                                        to_port)

    @classmethod
    def tearDownClass(cls):
        if compute.MULTI_USER:
            cls.client.delete_server(cls.server['id'])
            cls.images_client.delete_image(cls.image['id'])
            cls.keypairs_client.delete_keypair(cls.keypairname)
            cls.security_client.delete_security_group(cls.security_group['id'])
        super(AuthorizationTest, cls).tearDownClass()

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_server_for_alt_account_fails(self):
        """A GET request for a server on another user's account should fail"""
        self.alt_client.get_server(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_server_for_alt_account_fails(self):
        """A DELETE request for another user's server should fail"""
        self.alt_client.delete_server(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_update_server_for_alt_account_fails(self):
        """An update server request for another user's server should fail"""
        self.alt_client.update_server(self.server['id'], name='test')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_list_server_addresses_for_alt_account_fails(self):
        """A list addresses request for another user's server should fail"""
        self.alt_client.list_addresses(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_list_server_addresses_by_network_for_alt_account_fails(self):
        """
        A list address/network request for another user's server should fail
        """
        server_id = self.server['id']
        self.alt_client.list_addresses_by_network(server_id, 'public')

    def test_list_servers_with_alternate_tenant(self):
        """
        A list on servers from one tenant should not
        show on alternate tenant
        """
        #Listing servers from alternate tenant
        alt_server_ids = []
        resp, body = self.alt_client.list_servers()
        alt_server_ids = [s['id'] for s in body['servers']]
        self.assertNotIn(self.server['id'], alt_server_ids)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_change_password_for_alt_account_fails(self):
        """A change password request for another user's server should fail"""
        self.alt_client.change_password(self.server['id'], 'newpass')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_reboot_server_for_alt_account_fails(self):
        """A reboot request for another user's server should fail"""
        self.alt_client.reboot(self.server['id'], 'HARD')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_rebuild_server_for_alt_account_fails(self):
        """A rebuild request for another user's server should fail"""
        self.alt_client.rebuild(self.server['id'], self.image_ref_alt)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_resize_server_for_alt_account_fails(self):
        """A resize request for another user's server should fail"""
        self.alt_client.resize(self.server['id'], self.flavor_ref_alt)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_create_image_for_alt_account_fails(self):
        """A create image request for another user's server should fail"""
        self.alt_images_client.create_image(self.server['id'], 'testImage')

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_server_with_unauthorized_image(self):
        """Server creation with another user's image should fail"""
        self.alt_client.create_server('test', self.image['id'],
                                      self.flavor_ref)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_server_fails_when_tenant_incorrect(self):
        """
        A create server request should fail if the tenant id does not match
        the current user
        """
        saved_base_url = self.alt_client.base_url
        try:
            # Change the base URL to impersonate another user
            self.alt_client.base_url = self.client.base_url
            self.alt_client.create_server('test', self.image['id'],
                                          self.flavor_ref)
        finally:
            # Reset the base_url...
            self.alt_client.base_url = saved_base_url

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_keypair_in_analt_user_tenant(self):
        """
        A create keypair request should fail if the tenant id does not match
        the current user
        """
        #POST keypair with other user tenant
        k_name = rand_name('keypair-')
        self.alt_keypairs_client._set_auth()
        self.saved_base_url = self.alt_keypairs_client.base_url
        try:
            # Change the base URL to impersonate another user
            self.alt_keypairs_client.base_url = self.keypairs_client.base_url
            resp = {}
            resp['status'] = None
            resp, _ = self.alt_keypairs_client.create_keypair(k_name)
        finally:
            # Reset the base_url...
            self.alt_keypairs_client.base_url = self.saved_base_url
            if (resp['status'] is not None):
                resp, _ = self.alt_keypairs_client.delete_keypair(k_name)
                self.fail("Create keypair request should not happen "
                          "if the tenant id does not match the current user")

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_keypair_of_alt_account_fails(self):
        """A GET request for another user's keypair should fail"""
        self.alt_keypairs_client.get_keypair(self.keypairname)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_keypair_of_alt_account_fails(self):
        """A DELETE request for another user's keypair should fail"""
        self.alt_keypairs_client.delete_keypair(self.keypairname)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_image_for_alt_account_fails(self):
        """A GET request for an image on another user's account should fail"""
        self.alt_images_client.get_image(self.image['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_image_for_alt_account_fails(self):
        """A DELETE request for another user's image should fail"""
        self.alt_images_client.delete_image(self.image['id'])

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_security_group_in_analt_user_tenant(self):
        """
        A create security group request should fail if the tenant id does not
        match the current user
        """
        #POST security group with other user tenant
        s_name = rand_name('security-')
        s_description = rand_name('security')
        self.saved_base_url = self.alt_security_client.base_url
        try:
            # Change the base URL to impersonate another user
            self.alt_security_client.base_url = self.security_client.base_url
            resp = {}
            resp['status'] = None
            resp, body = self.alt_security_client.create_security_group(
                                        s_name,
                                        s_description)
        finally:
            # Reset the base_url...
            self.alt_security_client.base_url = self.saved_base_url
            if resp['status'] is not None:
                resp, _ = \
                self.alt_security_client.delete_security_group(body['id'])
                self.fail("Create Security Group request should not happen if"
                          "the tenant id does not match the current user")

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_security_group_of_alt_account_fails(self):
        """A GET request for another user's security group should fail"""
        self.alt_security_client.get_security_group(self.security_group['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_security_group_of_alt_account_fails(self):
        """A DELETE request for another user's security group should fail"""
        self.alt_security_client.delete_security_group(
            self.security_group['id'])

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_security_group_rule_in_analt_user_tenant(self):
        """
        A create security group rule request should fail if the tenant id
        does not match the current user
        """
        #POST security group rule with other user tenant
        parent_group_id = self.security_group['id']
        ip_protocol = 'icmp'
        from_port = -1
        to_port = -1
        self.saved_base_url = self.alt_security_client.base_url
        try:
            # Change the base URL to impersonate another user
            self.alt_security_client.base_url = self.security_client.base_url
            resp = {}
            resp['status'] = None
            resp, body = \
            self.alt_security_client.create_security_group_rule(
                                                parent_group_id,
                                                ip_protocol, from_port,
                                                to_port)
        finally:
            # Reset the base_url...
            self.alt_security_client.base_url = self.saved_base_url
            if resp['status'] is not None:
                resp, _ = \
                self.alt_security_client.delete_security_group_rule(
                                        body['id'])
                self.fail("Create security group rule request should not "
                          "happen if the tenant id does not match the"
                          " current user")

    @unittest.skip("Skipped until the Bug #1001118 is resolved")
    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_security_group_rule_of_alt_account_fails(self):
        """
        A DELETE request for another user's security group rule
        should fail
        """
        self.alt_security_client.delete_security_group_rule(self.rule['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_set_metadata_of_alt_account_server_fails(self):
        """ A set metadata for another user's server should fail """
        req_metadata = {'meta1': 'data1', 'meta2': 'data2'}
        self.alt_client.set_server_metadata(self.server['id'], req_metadata)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_set_metadata_of_alt_account_image_fails(self):
        """ A set metadata for another user's image should fail """
        req_metadata = {'meta1': 'value1', 'meta2': 'value2'}
        self.alt_images_client.set_image_metadata(self.image['id'],
                                                  req_metadata)

    @attr(type='negative')
    def test_get_metadata_of_alt_account_server_fails(self):
        """ A get metadata for another user's server should fail """
        req_metadata = {'meta1': 'data1'}
        self.client.set_server_metadata(self.server['id'], req_metadata)
        try:
            resp, meta = \
            self.alt_client.get_server_metadata_item(self.server['id'],
                                                     'meta1')
        except exceptions.NotFound:
            pass
        finally:
            resp, body = \
            self.client.delete_server_metadata_item(self.server['id'], 'meta1')

    @attr(type='negative')
    def test_get_metadata_of_alt_account_image_fails(self):
        """ A get metadata for another user's image should fail """
        req_metadata = {'meta1': 'value1'}
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        try:
            resp, meta = \
            self.alt_images_client.get_image_metadata_item(self.image['id'],
                                                           'meta1')
        except exceptions.NotFound:
            pass
        finally:
            resp, body = self.images_client.delete_image_metadata_item(
                                self.image['id'], 'meta1')

    @attr(type='negative')
    def test_delete_metadata_of_alt_account_server_fails(self):
        """ A delete metadata for another user's server should fail """
        req_metadata = {'meta1': 'data1'}
        self.client.set_server_metadata(self.server['id'], req_metadata)
        try:
            resp, body = \
            self.alt_client.delete_server_metadata_item(self.server['id'],
                                                        'meta1')
        except exceptions.NotFound:
            pass
        finally:
            resp, body = \
            self.client.delete_server_metadata_item(self.server['id'], 'meta1')

    @attr(type='negative')
    def test_delete_metadata_of_alt_account_image_fails(self):
        """ A delete metadata for another user's image should fail """
        req_metadata = {'meta1': 'data1'}
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        try:
            resp, body = \
            self.alt_images_client.delete_image_metadata_item(self.image['id'],
                                                              'meta1')
        except exceptions.NotFound:
            pass
        finally:
            resp, body = \
            self.images_client.delete_image_metadata_item(self.image['id'],
                                                          'meta1')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_console_output_of_alt_account_server_fails(self):
        """
        A Get Console Output for another user's server should fail
        """
        self.alt_console_outputs_client.get_console_output(self.server['id'],
                                                           10)
