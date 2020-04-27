import json
import time

from django.test import TestCase

POST_LINKS = '/visited_links'
GET_DOMAINS = '/visited_domains'


class TestAPI(TestCase):

    def test_post_bad_request(self):
        invalid_data = [
            {'link': 'yandex.ru'},
            {'links'},
            {'links': []},
            'links',
            123,
            {},
            [],
            None
        ]
        for data in invalid_data:
            response = self.client.post(POST_LINKS, data, 'application/json')
            self.assertEqual(response.status_code, 400)

    def test_get_bad_request(self):
        response = self.client.get(GET_DOMAINS)
        self.assertEqual(response.status_code, 400)
        self.assertJSONNotEqual(response.content, {'status': 'ok'})
        time_to = time.time()
        time_from = time_to - 86400000.0
        url = f'{GET_DOMAINS}?time_from={time_from}&time_to={time_to}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONNotEqual(response.content, {'domains': [], 'status': 'ok'})

    def test_post_visited_links(self):
        data = {
            "links": [
                "https://ya.ru",
                "https://ya.ru?q=123",
                "funbox.ru",
                "https://stackoverflow.com/questions/11828270/how-to-exit-the-vim-editor"
            ]
        }
        response = self.client.post(POST_LINKS, data, 'application/json')
        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(response.content, {'status': 'ok'})

    def test_get_visited_domains(self):
        time_to = time.time()
        time_from = time_to - 86400000.0
        url = f'{GET_DOMAINS}?from={time_from}&to={time_to}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        domains = json.loads(response.content)['domains']
        self.assertIn(container=domains, member='ya.ru')
        self.assertIn(container=domains, member='funbox.ru')
        self.assertIn(container=domains, member='stackoverflow.com')

    def test_get_visited_domains_empty_time_period(self):
        time_from = time.time()
        time_to = time.time()
        url = f'{GET_DOMAINS}?from={time_from}&to={time_to}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        domains = json.loads(response.content)['domains']
        self.assertJSONEqual(response.content, {'domains': [], 'status': 'ok'})
        self.assertNotIn(container=domains, member='ya.ru')
        self.assertNotIn(container=domains, member='funbox.ru')
        self.assertNotIn(container=domains, member='stackoverflow.com')

    def test_get_visited_domains_wrong_time(self):
        time_from = time.time()
        time_to = time_from - 1
        url = f'{GET_DOMAINS}?from={time_from}&to={time_to}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONNotEqual(response.content, {'domains': [], 'status': 'ok'})

    def test_wrong_method(self):
        response = self.client.get(POST_LINKS)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(GET_DOMAINS)
        self.assertEqual(response.status_code, 405)

    def test_page_not_found(self):
        response = self.client.get('/page_that_does_not_exists')
        self.assertEqual(response.status_code, 404)
