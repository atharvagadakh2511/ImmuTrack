from django.test import TestCase
from datetime import date
from .services import ScheduleEngine

class SchedulingEngineTestCase(TestCase):
    def test_date_calculation_offsets(self):
        dob = date(2025, 1, 1)
        # 6 weeks (42 days) offset
        due_6w = ScheduleEngine.calculate_due_date(dob, offset_days=42, offset_months=0)
        self.assertEqual(due_6w, date(2025, 2, 12))

        # 9 months offset
        due_9m = ScheduleEngine.calculate_due_date(dob, offset_days=0, offset_months=9)
        self.assertEqual(due_9m, date(2025, 10, 1))
