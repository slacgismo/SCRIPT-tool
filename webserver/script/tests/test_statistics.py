from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from script.models.data import County
from script.models.statistics import Energy
from script.tests.utils import create_county, create_energy

import json

class EnergyTests(APITestCase):

    county_name = 'Santa Cruz'
    total_session = 100
    total_energy = 10000.0
    peak_energy = 12312.0
    year = 2019
    month = 10
    energy = 1234.5

    def test_create_energy(self):
        """Ensure we can create a new energy object."""
        _ = create_county(self.county_name,
                            self.total_session,
                            self.total_energy,
                            self.peak_energy)
        response = create_energy(self.county_name, self.year, self.month, self.energy)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Energy.objects.count(), 1)
        obj = Energy.objects.get()
        self.assertEqual(obj.county.name, self.county_name)
        self.assertEqual(obj.year, self.year)
        self.assertEqual(obj.month, self.month)

    def test_filter_county(self):
        """Ensure we can filter energies by fields: county, year, month."""
        _ = create_county(self.county_name,
                            self.total_session,
                            self.total_energy,
                            self.peak_energy)
        response = create_energy(self.county_name, self.year, self.month, self.energy)
        response = create_energy(self.county_name, self.year, 11, self.energy)
        url = reverse('energy-list')
        data = {
            'county': self.county_name,
            'year': self.year,
            'month': self.month
        }
        response = self.client.get(url, data)
        obj = json.loads(response.content)[0]
        self.assertEqual(obj['county'], self.county_name)
        self.assertEqual(obj['year'], self.year)
        self.assertEqual(obj['month'], self.month)
        self.assertEqual(obj['energy'], self.energy)
