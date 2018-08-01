import json

from rest_framework.test import APIRequestFactory
from tests.mixins import APITestCase
from drf_batch_requests.request import BatchRequest
from drf_batch_requests.settings import conf

CONTENT_ID_HEADER = conf.SUBREQ_ID_HEADER

class RequestHeadersTest(APITestCase):

    def test_subrequest_headers(self):
        # Arrange
        data = {
            'method': 'get',
            'relative_url': '/test/',
            'headers': {
                'header-1': 'whatever',
                'Content-Length': 56,
            },
            '_body': ''
        }
        request = APIRequestFactory().post('/test')
        # Act
        result = BatchRequest(request, data)
        # Assert
        self.assertIn('HTTP_HEADER_1', result.META)
        self.assertIn('CONTENT_LENGTH', result.META)

    def test_id_headers_in_responses(self):
        # Arrange
        batch = [
            {
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'idontcare',
                },
            },
            {
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'nordoi',
                },
            },
        ]
        subreq_ids = {sr['headers'][CONTENT_ID_HEADER] for sr in batch}
        # Act
        responses = self.forced_auth_req('post','/batch/',
            data={'batch': batch})
        # Assert
        response_headers = [rd['headers'] for rd in responses.data]
        [
            self.assertIn(CONTENT_ID_HEADER, subreq_headers)
            for subreq_headers in response_headers
        ]
        response_ids = {rh[CONTENT_ID_HEADER] for rh in response_headers}
        self.assertEqual(subreq_ids, response_ids)

    def test_missing_id_header(self):
        # Arrange
        batch = [
            {
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER+'nonsense': 'idontcare',
                },
            },
        ]
        # Act
        responses = self.forced_auth_req('post','/batch/',
            data={'batch': batch})
        # Assert
        self.assertEqual(responses.status_code, 400)

    def test_duplicated_ids(self):
        # Arrange
        batch = [
            {
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'idontcare',
                },
            },
            {
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'idontcare',
                },
            },
        ]
        # Act
        responses = self.forced_auth_req('post','/batch/',
            data={'batch': batch})
        # Assert
        self.assertEqual(responses.status_code, 400)

    def test_duplicated_names(self):
        # Arrange
        batch = [
            {
                'name': 'samenameeverywhere',
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'notequal_1',
                },
            },
            {
                'name': 'samenameeverywhere',
                'method': 'get',
                'relative_url': '/test/',
                'headers': {
                    CONTENT_ID_HEADER: 'notequal_2',
                },
            },
        ]
        # Act
        responses = self.forced_auth_req('post','/batch/',
            data={'batch': batch})
        # Assert
        self.assertEqual(responses.status_code, 400)