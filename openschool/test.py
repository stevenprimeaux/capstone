import unittest

from dotenv import load_dotenv, find_dotenv
from os import environ
import requests

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

header_superintendent = {
    'Authorization': 'Bearer ' + environ.get('JWT_SUPERINTENDENT')
}

header_principal1 = {
    'Authorization': 'Bearer ' + environ.get('JWT_PRINCIPAL1')
}

header_principal2 = {
    'Authorization': 'Bearer ' + environ.get('JWT_PRINCIPAL2')
}

header_public = {
    'Authorization': 'Bearer ' + environ.get('JWT_PUBLIC')
}

class TestEndpoints(unittest.TestCase):

    def setUp(self):
        requests.post(
            'http://localhost:5000/schools',
            headers=header_superintendent,
            json={'name': 'foo', 'address': 'foo'}
        )

    def tearDown(self):
        requests.delete(
            'http://localhost:5000/schools/3',
            headers=header_superintendent
        )

    def test_get_schools(self):

        url = 'http://localhost:5000/schools'
        r = requests.get(url)

        self.assertEqual(r.status_code, 200)

    def test_get_students(self):

        url = 'http://localhost:5000/students'

        r_superintendent = requests.get(url, headers=header_superintendent)
        r_principal1 = requests.get(url, headers=header_principal1)
        r_public = requests.get(url, headers=header_public)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 403)
        self.assertEqual(r_public.status_code, 403)

    def test_get_students_1(self):

        url = 'http://localhost:5000/schools/1/students'

        r_superintendent = requests.get(url, headers=header_superintendent)
        r_principal1 = requests.get(url, headers=header_principal1)
        r_principal2 = requests.get(url, headers=header_principal2)
        r_public = requests.get(url, headers=header_public)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 200)
        self.assertEqual(r_principal2.status_code, 403)
        self.assertEqual(r_public.status_code, 403)

    def test_get_students_2(self):

        url = 'http://localhost:5000/schools/2/students'

        r_superintendent = requests.get(url, headers=header_superintendent)
        r_principal1 = requests.get(url, headers=header_principal1)
        r_principal2 = requests.get(url, headers=header_principal2)
        r_public = requests.get(url, headers=header_public)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 403)
        self.assertEqual(r_principal2.status_code, 200)
        self.assertEqual(r_public.status_code, 403)

    def test_post_school(self):

        url = 'http://localhost:5000/schools'

        payload = {'name': 'School Name 3', 'address': '3 School Street'}

        r_superintendent = requests.post(url, headers=header_superintendent, json=payload)
        r_principal1 = requests.post(url, headers=header_principal1, json=payload)
        r_principal2 = requests.post(url, headers=header_principal2, json=payload)
        r_public = requests.post(url, headers=header_public, json=payload)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 403)
        self.assertEqual(r_principal2.status_code, 403)
        self.assertEqual(r_public.status_code, 403)

    def test_patch_school(self):

        url = 'http://localhost:5000/schools/1'

        payload = {'name': 'patched', 'address': 'patched'}

        r_superintendent = requests.patch(url, headers=header_superintendent, json=payload)
        r_principal1 = requests.patch(url, headers=header_principal1, json=payload)
        r_principal2 = requests.patch(url, headers=header_principal2, json=payload)
        r_public = requests.patch(url, headers=header_public, json=payload)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 403)
        self.assertEqual(r_principal2.status_code, 403)
        self.assertEqual(r_public.status_code, 403)

    def test_delete_school(self):

        url = 'http://localhost:5000/schools/3'

        r_superintendent = requests.delete(url, headers=header_superintendent)
        r_principal1 = requests.delete(url, headers=header_principal1)
        r_principal2 = requests.delete(url, headers=header_principal2)
        r_public = requests.delete(url, headers=header_public)

        self.assertEqual(r_superintendent.status_code, 200)
        self.assertEqual(r_principal1.status_code, 403)
        self.assertEqual(r_principal2.status_code, 403)
        self.assertEqual(r_public.status_code, 403)

if __name__ == '__main__':
    unittest.main()
