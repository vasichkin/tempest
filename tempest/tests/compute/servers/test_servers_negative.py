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

import sys

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base
import testtools

class ServersNegativeTest(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    @testtools.skip("Error on FOLSOM (fix alt_demo user)")
    def setUpClass(cls):
        super(ServersNegativeTest, cls).setUpClass()
        cls.client = cls.servers_client
        cls.img_client = cls.images_client
        cls.alt_os = clients.AltManager()
        cls.alt_client = cls.alt_os.servers_client

    @attr(type='negative')
    def test_server_name_blank(self):
        # Create a server with name parameter empty

        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          name='')

    @attr(type='negative')
    def test_personality_file_contents_not_encoded(self):
        # Use an unencoded file when creating a server with personality

        file_contents = 'This is a test file.'
        person = [{'path': '/etc/testfile.txt',
                   'contents': file_contents}]

        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          personality=person)

    @attr(type='negative')
    def test_create_with_invalid_image(self):
        # Create a server with an unknown image

        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          image_id=-1)

    @attr(type='negative')
    def test_create_with_invalid_flavor(self):
        # Create a server with an unknown flavor

        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          flavor=-1,)

    @attr(type='negative')
    def test_invalid_access_ip_v4_address(self):
        # An access IPv4 address must match a valid address pattern

        IPv4 = '1.1.1.1.1.1'
        self.assertRaises(exceptions.BadRequest,
                          self.create_server, accessIPv4=IPv4)

    @attr(type='negative')
    def test_invalid_ip_v6_address(self):
        # An access IPv6 address must match a valid address pattern

        IPv6 = 'notvalid'

        self.assertRaises(exceptions.BadRequest,
                          self.create_server, accessIPv6=IPv6)

    @attr(type='negative')
    def test_reboot_deleted_server(self):
        # Reboot a deleted server
        resp, server = self.create_server()
        self.server_id = server['id']
        self.client.delete_server(self.server_id)
        self.client.wait_for_server_termination(self.server_id)
        self.assertRaises(exceptions.NotFound, self.client.reboot,
                          self.server_id, 'SOFT')

    @attr(type='negative')
    def test_rebuild_deleted_server(self):
        # Rebuild a deleted server

        resp, server = self.create_server()
        self.server_id = server['id']
        self.client.delete_server(self.server_id)
        self.client.wait_for_server_termination(self.server_id)

        self.assertRaises(exceptions.NotFound,
                          self.client.rebuild,
                          self.server_id, self.image_ref_alt)

    @attr(type='negative')
    def test_create_numeric_server_name(self):
        # Create a server with a numeric name
        if self.__class__._interface == "xml":
            raise self.skipException("Not testable in XML")

        server_name = 12345
        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          name=server_name)

    @attr(type='negative')
    def test_create_server_name_length_exceeds_256(self):
        # Create a server with name length exceeding 256 characters

        server_name = 'a' * 256
        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          name=server_name)

    @attr(type='negative')
    def test_create_with_invalid_network_uuid(self):
        # Pass invalid network uuid while creating a server

        networks = [{'fixed_ip': '10.0.1.1', 'uuid': 'a-b-c-d-e-f-g-h-i-j'}]

        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          networks=networks)

    @attr(type='negative')
    def test_create_with_non_existant_keypair(self):
        # Pass a non existant keypair while creating a server

        key_name = rand_name('key')
        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          key_name=key_name)

    @attr(type='negative')
    def test_create_server_metadata_exceeds_length_limit(self):
        # Pass really long metadata while creating a server

        metadata = {'a': 'b' * 260}
        self.assertRaises(exceptions.OverLimit,
                          self.create_server,
                          meta=metadata)

    @attr(type='negative')
    def test_update_name_of_non_existent_server(self):
        # Update name of a non-existent server

        server_name = rand_name('server')
        new_name = rand_name('server') + '_updated'

        self.assertRaises(exceptions.NotFound, self.client.update_server,
                          server_name, name=new_name)

    @attr(type='negative')
    def test_update_server_set_empty_name(self):
        # Update name of the server to an empty string

        server_name = rand_name('server')
        new_name = ''

        self.assertRaises(exceptions.BadRequest, self.client.update_server,
                          server_name, name=new_name)

    @attr(type='negative')
    def test_update_server_of_another_tenant(self):
        # Update name of a server that belongs to another tenant

        resp, server = self.create_server(wait_until='ACTIVE')
        new_name = server['id'] + '_new'
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.update_server, server['id'],
                          name=new_name)

    @attr(type='negative')
    def test_update_server_name_length_exceeds_256(self):
        # Update name of server exceed the name length limit

        resp, server = self.create_server(wait_until='ACTIVE')
        new_name = 'a' * 256
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_server,
                          server['id'],
                          name=new_name)

    @attr(type='negative')
    def test_delete_non_existent_server(self):
        # Delete a non existent server

        self.assertRaises(exceptions.NotFound, self.client.delete_server,
                          '999erra43')

    @attr(type='negative')
    def test_delete_a_server_of_another_tenant(self):
        # Delete a server that belongs to another tenant
        try:
            resp, server = self.create_server(wait_until='ACTIVE')
            self.assertRaises(exceptions.NotFound,
                              self.alt_client.delete_server,
                              server['id'])
        finally:
            self.client.delete_server(server['id'])

    @attr(type='negative')
    def test_delete_server_pass_negative_id(self):
        # Pass an invalid string parameter to delete server

        self.assertRaises(exceptions.NotFound, self.client.delete_server, -1)

    @attr(type='negative')
    def test_delete_server_pass_id_exceeding_length_limit(self):
        # Pass a server ID that exceeds length limit to delete server

        self.assertRaises(exceptions.NotFound, self.client.delete_server,
                          sys.maxint + 1)

    @attr(type='negative')
    def test_create_with_nonexistent_security_group(self):
        # Create a server with a nonexistent security group

        security_groups = [{'name': 'does_not_exist'}]
        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          security_groups=security_groups)

    @attr(type='negative')
    def test_get_non_existent_server(self):
        # Get a non existent server details

        self.assertRaises(exceptions.NotFound, self.client.get_server,
                          '999erra43')


class ServersNegativeTestXML(ServersNegativeTest):
    _interface = 'xml'
