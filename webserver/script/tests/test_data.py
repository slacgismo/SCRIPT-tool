from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from script.models.data import County
from script.tests.utils import create_county

import json
from pprint import pprint

class CountyTests(APITestCase):

    county_name = 'Santa Cruz'
    total_session = 100
    total_energy = 10000.0
    peak_energy = 12312.0

    def test_create_county(self):
        """Ensure we can create a new county object."""
        response = create_county(self.county_name,
                                self.total_session,
                                self.total_energy,
                                self.peak_energy)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(County.objects.count(), 1)
        obj = County.objects.get()
        self.assertEqual(obj.name, self.county_name)
        self.assertEqual(obj.total_session, self.total_session)
        self.assertEqual(obj.total_energy, self.total_energy)
        self.assertEqual(obj.peak_energy, self.peak_energy)

    def test_create_conflict(self):
        """Ensure we cannot create two counties with the same name."""
        _ = create_county(self.county_name,
                            self.total_session,
                            self.total_energy,
                            self.peak_energy)
        response = create_county(self.county_name,
                                self.total_session + 1,
                                self.total_energy,
                                self.peak_energy)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_counties(self):
        """Ensure we can list all counties."""
        _ = create_county(self.county_name,
                            self.total_session + 1,
                            self.total_energy + 2,
                            self.peak_energy + 3)
        _ = create_county('Sunnyvale',
                            self.total_session + 4,
                            self.total_energy + 5,
                            self.peak_energy + 6)
        _ = create_county('Palo Alto',
                            self.total_session + 7,
                            self.total_energy + 8,
                            self.peak_energy + 9)
        url = reverse('county-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 3)

    def test_delete_county(self):
        """Ensure we can delete a county by its primary key."""
        response = create_county(self.county_name,
                            self.total_session,
                            self.total_energy,
                            self.peak_energy)
        data = json.loads(response.content)
        url = reverse('county-detail', args=[self.county_name])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_modify_county(self):
        """Ensure we can modify a county by its primary key."""
        _ = create_county(self.county_name,
                            self.total_session,
                            self.total_energy,
                            self.peak_energy)
        url = reverse('county-detail', args=[self.county_name])
        data = {
            'name': self.county_name,
            'total_session': self.total_session + 1,
            'total_energy': self.total_energy + 2,
            'peak_energy': self.peak_energy + 3
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url, format='json')
        data = json.loads(response.content)
        self.assertEqual(data['total_session'], self.total_session + 1)
