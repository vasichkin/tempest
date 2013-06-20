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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute.base import BaseComputeTest
from tempest.tests import utils


class ImagesMetadataTest(BaseComputeTest):

    @classmethod
    @utils.skip('Not supported in Y! environment')
    def setUpClass(cls):
        super(ImagesMetadataTest, cls).setUpClass()
        cls.servers_client = cls.servers_client
        cls.client = cls.images_client

        name = rand_name('server')
        resp, server = cls.servers_client.create_server(name, cls.image_ref,
                                                        cls.flavor_ref)
        cls.server_id = server['id']

        #Wait for the server to become active
        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

        # Snapshot the server once to save time
        name = rand_name('image')
        resp, _ = cls.client.create_image(cls.server_id, name, {})
        cls.image_id = resp['location'].rsplit('/', 1)[1]

        cls.client.wait_for_image_resp_code(cls.image_id, 200)
        cls.client.wait_for_image_status(cls.image_id, 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_image(cls.image_id)
        cls.servers_client.delete_server(cls.server_id)
        super(ImagesMetadataTest, cls).tearDownClass()

    def setUp(self):
        meta = {'key1': 'value1', 'key2': 'value2'}
        resp, _ = self.client.set_image_metadata(self.image_id, meta)
        self.assertEqual(resp.status, 200)

    def test_list_image_metadata(self):
        """All metadata key/value pairs for an image should be returned"""
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    def test_set_image_metadata(self):
        """The metadata for the image should match the new values"""
        req_metadata = {'meta2': 'value2', 'meta3': 'value3'}
        resp, body = self.client.set_image_metadata(self.image_id,
                                                    req_metadata)

        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        self.assertEqual(req_metadata, resp_metadata)

    def test_update_image_metadata(self):
        """The metadata for the image should match the updated values"""
        req_metadata = {'key1': 'alt1', 'key3': 'value3'}
        resp, metadata = self.client.update_image_metadata(self.image_id,
                                                           req_metadata)

        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'alt1', 'key2': 'value2', 'key3': 'value3'}
        self.assertEqual(expected, resp_metadata)

    def test_get_image_metadata_item(self):
        """The value for a specific metadata key should be returned"""
        resp, meta = self.client.get_image_metadata_item(self.image_id,
                                                         'key2')
        self.assertTrue('value2', meta['key2'])

    def test_set_image_metadata_item(self):
        """
        The value provided for the given meta item should be set for the image
        """
        meta = {'key1': 'alt'}
        resp, body = self.client.set_image_metadata_item(self.image_id,
                                                         'key1', meta)
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'alt', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    def test_delete_image_metadata_item(self):
        """The metadata value/key pair should be deleted from the image"""
        resp, body = self.client.delete_image_metadata_item(self.image_id,
                                                            'key1')
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='negative')
    def test_list_nonexistant_image_metadata(self):
        """Negative test: List on nonexistant image
        metadata should not happen"""
        try:
            resp, resp_metadata = self.client.list_image_metadata(999)
        except exceptions.NotFound:
            pass
        else:
            self.fail('List on nonexistant image metadata should'
                      'not happen')

    @attr(type='negative')
    def test_update_nonexistant_image_metadata(self):
        """Negative test:An update should not happen for a nonexistant image"""
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        try:
            resp, metadata = self.client.update_image_metadata(999, meta)
        except exceptions.NotFound:
            pass
        else:
            self.fail('An update shouldnt happen for nonexistant image')

    @attr(type='negative')
    def test_get_nonexistant_image_metadata_item(self):
        """Negative test: Get on nonexistant image should not happen"""
        try:
            resp, metadata = self.client.get_image_metadata_item(999, 'key2')
        except exceptions.NotFound:
            pass
        else:
            self.fail('Get on nonexistant image should not happen')

    @attr(type='negative')
    def test_set_nonexistant_image_metadata(self):
        """Negative test: Metadata should not be set to a nonexistant image"""
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        try:
            resp, meta = self.client.set_image_metadata(999, meta)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Metadata should not be set to a nonexistant image')

    @attr(type='negative')
    def test_set_nonexistant_image_metadata_item(self):
        """Negative test: Metadata item should not be set to a
        nonexistant image"""
        meta = {'key1': 'alt'}
        try:
            resp, body = self.client.set_image_metadata_item(999, 'key1', meta)
            resp, metadata = self.client.list_image_metadata(999)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Metadata item should not be set to a nonexistant image')

    @attr(type='negative')
    def test_delete_nonexistant_image_metadata_item(self):
        """Negative test: Shouldnt be able to delete metadata
                          item from nonexistant image"""
        try:
            resp, body = self.client.delete_image_metadata_item(999, 'key1')
            resp, metadata = self.client.list_image_metadata(999)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to delete metadata item from a'
                      'nonexistant image')
