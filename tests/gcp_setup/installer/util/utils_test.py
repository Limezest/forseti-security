"""def generate_deployment_templates(template_type, values, datetimestamp):
def generate_forseti_conf(template_type, vals, datetimestamp):
def copy_file_to_destination(file_path, output_path,
                             is_directory, dry_run):
def generate_file_from_template(template_path, output_path, template_values):
def sanitize_conf_values(conf_values):
"""
import unittest

import scripts.gcp_setup.installer.util.utils as utils

from tests.unittest_utils import ForsetiTestCase


class TestUtilsModule(ForsetiTestCase):

    def test_id_from_name_normal(self):
        """The name of the resource, formatted as
        ${RESOURCE_TYPE}/${RESOURCE_ID}, make ${RESOURCE_ID} is returned"""
        test_name = 'RESOURCE_TYPE/RESOURCE_ID'
        expected_name = 'RESOURCE_ID'
        self.assertTrue(utils.id_from_name(test_name), expected_name)

    def test_id_from_name_multiple_backslashes(self):
        """The name of the resource, formatted as
        ${RESOURCE_TYPE}/${RESOURCE_ID}, make ${RESOURCE_ID} is returned"""
        test_name = 'RESOURCE_TYPE1/RESOUCE_TYPE2/RESOURCE_TYPE3/RESOURCE_ID'
        expected_name = 'RESOURCE_ID'
        self.assertTrue(utils.id_from_name(test_name), expected_name)

    def test_id_from_name_no_backslash(self):
        """The name of the resource, formatted as
        ${RESOURCE_TYPE}/${RESOURCE_ID}, make ${RESOURCE_ID} is returned"""
        test_name = 'RESOURCE_ID'
        expected_name = 'RESOURCE_ID'
        self.assertTrue(utils.id_from_name(test_name), expected_name)


if __name__ == '__main__':
    unittest.main()
