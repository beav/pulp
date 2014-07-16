from gettext import gettext as _
from itertools import chain, imap
import logging

from pulp.common.plugins import reporting_constants
from pulp.plugins.conduits.mixins import UnitAssociationCriteria
from pulp.plugins.util.publish_step import Step

_LOG = logging.getLogger(__name__)


class SyncStep(Step):

    def __init__(self, step_type, repo=None, sync_conduit=None, config=None, working_dir=None,
                 importer_type=None):
        """
        Set the default parent, step_type and unit_type for the the sync step
        the unit_type defaults to none since some steps are not used for processing units.

        :param step_type: The id of the step this processes
        :type step_type: str
        :param repo: The repo to be synced to
        :type repo: pulp.plugins.model.Repository
        :param sync_conduit: The sync conduit for the repo to be synced
        :type sync_conduit: tbd
        :param config: The sync configuration
        :type config: PluginCallConfiguration
        :param importer_type: The type of the importer that is being synced
        :type importer_type: str
        """
        super(SyncStep, self).__init__(step_type, sync_conduit)
        self.importer_type = importer_type
        self.repo = repo
        self.sync_conduit = sync_conduit
        self.config = config

    def sync(self):
        """
        Perform the sync action the repo & information specified in the constructor
        """
        self.process_lifecycle()
        return self._build_final_report()

    def get_importer_type(self):
        """
        :returns: the type of importer this action is for
        :rtype: str or None
        """
        if self.importer_type:
            return self.importer_type
        if self.parent:
            return self.parent.get_importer_type()
        return None

    def get_repo(self):
        """
        :returns: the repository for this sync action
        :rtype: pulp.plugins.model.Repository
        """
        if self.repo:
            return self.repo
        return self.parent.get_repo()

    def get_conduit(self):
        """
        :returns: Return the conduit for this sync action
        :rtype: tbd
        """
        if self.sync_conduit:
            return self.sync_conduit
        return self.parent.get_conduit()

    def get_config(self):
        """
        :returns: Return the config for this sync action
        :rtype: pulp.plugins.config.PluginCallConfiguration
        """
        if self.config:
            return self.config
        return self.parent.get_config()

    def get_progress_report_summary(self):
        """
        Get the simpler, more human legible progress report
        """
        report = {}
        for step in self.children:
            report.update({step.step_id: step.state})
        return report

    def _build_final_report(self):
        """
        Build the PublishReport to be returned as the result after task completion

        :return: report describing the publish run
        :rtype:  pulp.plugins.model.PublishReport
        """

        overall_success = True
        if self.state == reporting_constants.STATE_FAILED:
            overall_success = False

        progress_report = self.get_progress_report()
        summary_report = self.get_progress_report_summary()

        if overall_success:
            final_report = self.get_conduit().build_success_report(summary_report, progress_report)
        else:
            final_report = self.get_conduit().build_failure_report(summary_report, progress_report)

        final_report.canceled_flag = self.canceled

        return final_report


class UnitSyncStep(SyncStep):

    def __init__(self, step_type, unit_type=None, association_filters=None,
                 unit_fields=None):
        """
        Set the default parent, step_type and unit_type for the sync step
        the unit_type defaults to none since some steps are not used for processing units.

        :param step_type: The id of the step this processes
        :typstep_typeid: str
        :param unit_type: The type of unit this step processes
        :type unit_type: str or list of str
        """
        super(UnitSyncStep, self).__init__(step_type)
        if isinstance(unit_type, list):
            self.unit_type = unit_type
        else:
            self.unit_type = [unit_type]
        self.skip_list = set()
        self.association_filters = association_filters
        self.unit_fields = unit_fields

    def get_unit_generator(self):
        """
        This method returns a generator for the unit_type specified on the SyncStep.
        The units created by this generator will be iterated over by the process_unit method.

        :return: generator of units
        :rtype:  GeneratorType of Units
        """
        types_to_query = (set(self.unit_type)).difference(self.skip_list)
        criteria = UnitAssociationCriteria(type_ids=list(types_to_query),
                                           association_filters=self.association_filters,
                                           unit_fields=self.unit_fields)
        return self.get_conduit().get_units(criteria, as_generator=True)

    def is_skipped(self):
        """
        Test to find out if the step should be skipped.

        :return: whether or not the step should be skipped
        :rtype:  bool
        """
        if not self.skip_list:
            config = self.get_config()
            skip = config.get('skip', [])
            # there is a chance that the skip list is actually a dictionary with a
            # boolean to indicate whether or not each item should be skipped
            # if that is the case iterate over it to build a list of the items
            # that should be skipped instead
            if type(skip) is dict:
                return [k for k, v in skip.items() if v]
            self.skip_list = set(skip)

        return set(self.unit_type).issubset(self.skip_list)

    def process_unit(self, unit):
        """
        Do any work required for syncing a unit in this step

        :param unit: The unit to process
        :type unit: Unit
        """
        pass

    def _process_block(self):
        """
        This block is called for the main processing loop
        """
        package_unit_generator = self.get_unit_generator()
        for package_unit in package_unit_generator:
            if self.canceled:
                return
            self.process_unit(package_unit)
            self.progress_successes += 1
            self.report_progress()

    def _get_total(self, id_list=None):
        """
        Return the total number of units that are processed by this step.
        This is used generally for progress reporting.  The value returned should not change
        during the processing of the step.

        :param id_list: List of type ids to get the total count of
        :type id_list: list of str
        """
        if id_list is None:
            id_list = self.unit_type
        total = 0
        if self.association_filters:
            # We have no good way to get this count without iterating over all units so punt
            total = 1
        else:
            types_to_query = (set(id_list)).difference(self.skip_list)
            for type_id in types_to_query:
                total += self.parent.repo.content_unit_counts.get(type_id, 0)
        return total
