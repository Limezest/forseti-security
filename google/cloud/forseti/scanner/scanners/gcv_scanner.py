# Copyright 2019 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GCV Scanner."""

from google.cloud.forseti.common.util import logger
from google.cloud.forseti.scanner.scanners import base_scanner
from google.cloud.forseti.scanner.scanners.gcv_util import gcv_data_converter
from google.cloud.forseti.scanner.scanners.gcv_util import validator_client
from google.cloud.forseti.services.model.importer import importer


LOGGER = logger.get_logger(__name__)


class GCVScanner(base_scanner.BaseScanner):
    """GCV Scanner."""

    violation_type = 'GCV_VIOLATION'

    def __init__(self, global_configs, scanner_configs, service_config,
                 model_name, snapshot_timestamp, rules):
        """Constructor for the base pipeline.

         Args:
             global_configs (dict): Global configurations.
             scanner_configs (dict): Scanner configurations.
             service_config (ServiceConfig): Service configuration.
             model_name (str): name of the data model
             snapshot_timestamp (str): Timestamp, formatted as YYYYMMDDTHHMMSSZ.
             rules (str): Fully-qualified path and filename of the rules file.
         """
        super(GCVScanner, self).__init__(
            global_configs, scanner_configs, service_config,
            model_name, snapshot_timestamp, rules)
        self.validator_client = validator_client.ValidatorClient()

        # Maps CAI resource name-> (full_name, resource_data).
        self.resource_lookup_table = {}

    def _flatten_violations(self, violations):
        """Flatten GCV violations into a dict for each violation.

        Args:
            violations (list): The GCV violations to flatten.

        Yields:
            dict: Iterator of GCV violations as a dict per violation.
        """

        for violation in violations:
            resource_name_items = violation.resource.split('/')[0]
            resource_type, resource_id = (
                resource_name_items[-2], resource_name_items[-1])
            full_name, resource_data = self.resource_lookup_table.get(
                violation.resource, ('', ''))
            yield {
                'resource_id': resource_id,
                'resource_type': resource_type,
                'resource_name': violation.resource,
                'full_name': full_name,
                'rule_index': 0,
                'rule_name': violation.constraint,
                'violation_type': GCVScanner.violation_type,
                'violation_data': violation.meta_data,
                'resource_data': resource_data,
                'violation_message': violation.message
            }

    def _output_results(self, all_violations):
        """Output results.

        Args:
            all_violations (List[RuleViolation]): A list of GCV violations.
        """
        all_violations = list(self._flatten_violations(all_violations))
        self._output_results_to_db(all_violations)

    def _retrieve(self):
        """Retrieves the data for scanner.

        Yields:
            Asset: Google Config Validator Asset.

        Raises:
            ValueError: if resources have an unexpected type.
        """
        model_manager = self.service_config.model_manager
        scoped_session, data_access = model_manager.get(self.model_name)

        with scoped_session as session:
            # fetching GCP resources.
            LOGGER.info('Retrieving GCP resource data.')
            for resource_type in importer.GCP_TYPE_LIST:
                for resource in data_access.scanner_iter(session,
                                                         resource_type):
                    if (not resource.cai_resource_name and
                            resource.type not in
                            gcv_data_converter.CAI_RESOURCE_TYPE_MAPPING):
                        LOGGER.debug('Resource type %s is not currently '
                                     'supported in GCV scanner.',
                                     resource.type)
                        break
                    self.resource_lookup_table[resource.cai_resource_name] = (
                        resource_type.full_name, resource.data)
                    yield gcv_data_converter.convert_data_to_gcv_asset(
                        resource, 'resource')

            # fetching IAM policy.
            LOGGER.info('Retrieving GCP iam data.')
            for policy in data_access.scanner_iter(session, 'iam_policy'):
                if (not policy.cai_resource_name and
                        policy.type not in
                        gcv_data_converter.CAI_RESOURCE_TYPE_MAPPING):
                    LOGGER.debug('IAM Policy type %s is not currently '
                                 'supported in GCV scanner.',
                                 policy.type)
                    break
                yield gcv_data_converter.convert_data_to_gcv_asset(
                    policy, 'iam_policy')

    def run(self):
        """Runs the GCV Scanner."""
        # Get all the data in GCV Asset format.
        gcv_assets = self._retrieve()

        # Add asset data to GCV.
        for gcv_asset in gcv_assets:
            self.validator_client.add_data_to_buffer(gcv_asset)
        self.validator_client.flush_buffer()

        # Find all violations.
        violations = self.validator_client.audit()

        # Clean up GCV.
        self.validator_client.reset()

        # Output to db.
        self._output_results(violations)
