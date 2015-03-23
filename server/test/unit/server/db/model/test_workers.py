"""
This module contains tests for the pulp.server.db.model.workers module
"""
import mock

from pulp.server.exceptions import NoWorkers
from pulp.server.db.model.workers import Worker
from ....base import ResourceReservationTests


class TestGetWorkerForReservation(ResourceReservationTests):

    @mock.patch('pulp.server.db.model.workers.Worker.objects')
    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_existing_reservation_correctly_found(self, mock_reserved_resource,
                                                  mock_worker_objects):
        get_collection = mock_reserved_resource.get_collection
        Worker.get_worker_for_reservation('resource1')
        get_collection.assert_called_once_with()
        get_collection.return_value.find_one.assert_called_once_with({'resource_id': 'resource1'})

    @mock.patch('pulp.server.db.model.workers.Worker.objects')
    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_correct_worker_returned(self, mock_reserved_resource, mock_worker_objects):
        find_one = mock_reserved_resource.get_collection.return_value.find_one
        find_one.return_value = {'worker_name': 'worker1'}
        mock_worker_objects.return_value.first.return_value = find_one.return_value
        result = Worker.get_worker_for_reservation('resource1')
        self.assertTrue(result is find_one.return_value)

    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_no_workers_raised_if_no_reservations(self, mock_reserved_resource):
        find_one = mock_reserved_resource.get_collection.return_value.find_one
        find_one.return_value = False
        try:
            Worker.get_worker_for_reservation('resource1')
        except NoWorkers:
            pass
        else:
            self.fail("NoWorkers() Exception should have been raised.")


class TestGetUnreservedWorker(ResourceReservationTests):

    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_reserved_resources_queried_correctly(self, mock_reserved_resource):
        find = mock_reserved_resource.get_collection.return_value.find
        find.return_value = [{'worker_name': 'a'}, {'worker_name': 'b'}]
        try:
            Worker.get_unreserved_worker()
        except NoWorkers:
            pass
        else:
            self.fail("NoWorkers() Exception should have been raised.")
        mock_reserved_resource.get_collection.assert_called_once_with()
        find.assert_called_once_with()

    @mock.patch('pulp.server.db.model.workers.Worker.objects')
    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_worker_returned_when_one_worker_is_not_reserved(self, mock_reserved_resource,
                                                             mock_worker_objects):
        mock_worker_objects.return_value = [{'name': 'a'}, {'name': 'b'}]
        find = mock_reserved_resource.get_collection.return_value.find
        find.return_value = [{'worker_name': 'a'}]
        result = Worker.get_unreserved_worker()
        self.assertEqual(result, {'name': 'b'})

    @mock.patch('pulp.server.db.model.workers.Worker')
    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_no_workers_raised_when_all_workers_reserved(self, mock_reserved_resource, mock_worker):
        mock_worker.objects.return_value = [{'name': 'a'}, {'name': 'b'}]
        find = mock_reserved_resource.get_collection.return_value.find
        find.return_value = [{'worker_name': 'a'}, {'worker_name': 'b'}]
        try:
            Worker.get_unreserved_worker()
        except NoWorkers:
            pass
        else:
            self.fail("NoWorkers() Exception should have been raised.")

    @mock.patch('pulp.server.db.model.workers.Worker')
    @mock.patch('pulp.server.db.model.workers.ReservedResource')
    def test_no_workers_raised_when_there_are_no_workers(self, mock_reserved_resource, mock_worker):
        mock_worker.objects.return_value = []
        find = mock_reserved_resource.get_collection.return_value.find
        find.return_value = [{'worker_name': 'a'}, {'worker_name': 'b'}]
        try:
            Worker.get_unreserved_worker()
        except NoWorkers:
            pass
        else:
            self.fail("NoWorkers() Exception should have been raised.")

    def test_is_worker(self):
        self.assertTrue(Worker._is_worker("a_worker@some.hostname"))

    def test_is_not_worker_is_scheduler(self):
        self.assertEquals(Worker._is_worker("scheduler@some.hostname"), False)

    def test_is_not_worker_is_resource_mgr(self):
        self.assertEquals(Worker._is_worker("resource_manager@some.hostname"), False)
