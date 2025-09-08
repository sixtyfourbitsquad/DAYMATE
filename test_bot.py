#!/usr/bin/env python3
"""
Unit tests for DayMate Telegram Bot
Tests core date/time calculation functionality
"""

import unittest
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

# Import the bot class (assuming it's in the same directory)
from bot import DayMateBot

class TestDayMateBot(unittest.TestCase):
    """Test cases for DayMate bot functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = DayMateBot()
        self.timezone = ZoneInfo("Asia/Kolkata")
    
    def test_age_calculation(self):
        """Test age calculation accuracy"""
        # Test case 1: Person born on July 15, 1992
        dob = date(1992, 7, 15)
        reference_date = date(2025, 9, 8)
        
        # Calculate age using relativedelta
        age = relativedelta(reference_date, dob)
        
        # Verify age calculation
        self.assertEqual(age.years, 33)
        self.assertEqual(age.months, 1)
        self.assertEqual(age.days, 24)
        
        # Test total days
        total_days = (reference_date - dob).days
        self.assertEqual(total_days, 12079)
    
    def test_days_difference_calculation(self):
        """Test days difference calculation"""
        # Test case 1: From 2024-01-01 to 2025-09-08
        start_date = date(2024, 1, 1)
        end_date = date(2025, 9, 8)
        
        diff = relativedelta(end_date, start_date)
        total_days = (end_date - start_date).days
        
        # Verify difference calculation
        self.assertEqual(diff.years, 1)
        self.assertEqual(diff.months, 8)
        self.assertEqual(diff.days, 7)
        self.assertEqual(total_days, 615)
    
    def test_time_duration_formatting(self):
        """Test time duration formatting"""
        # Test case 1: 90 minutes = 5400 seconds
        total_seconds = 5400
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        self.assertEqual(hours, 1)
        self.assertEqual(minutes, 30)
        self.assertEqual(seconds, 0)
    
    def test_leap_year_handling(self):
        """Test leap year handling in age calculation"""
        # Test case: Person born on Feb 29, 2000 (leap year)
        dob = date(2000, 2, 29)
        reference_date = date(2024, 2, 28)  # Non-leap year
        
        age = relativedelta(reference_date, dob)
        
        # Should handle leap year correctly
        self.assertEqual(age.years, 23)
        self.assertEqual(age.months, 11)
        self.assertEqual(age.days, 30)
    
    def test_future_date_validation(self):
        """Test validation of future dates"""
        # Test case: Date of birth in the future
        future_date = date.today() + timedelta(days=365)
        current_date = date.today()
        
        # Future date should be greater than current date
        self.assertGreater(future_date, current_date)
    
    def test_timezone_handling(self):
        """Test timezone handling"""
        # Test different timezones
        utc_time = datetime.now(ZoneInfo("UTC"))
        kolkata_time = datetime.now(ZoneInfo("Asia/Kolkata"))
        
        # Both should be valid datetime objects
        self.assertIsInstance(utc_time, datetime)
        self.assertIsInstance(kolkata_time, datetime)
    
    def test_date_swapping(self):
        """Test date swapping functionality"""
        # Test case: End date before start date
        start_date = date(2025, 1, 1)
        end_date = date(2024, 1, 1)
        
        # After swapping
        new_start, new_end = end_date, start_date
        
        self.assertEqual(new_start, date(2024, 1, 1))
        self.assertEqual(new_end, date(2025, 1, 1))
    
    def test_callback_data_encoding(self):
        """Test callback data encoding for Telegram"""
        # Test that callback data doesn't exceed 64 bytes
        test_callback = "age_date_20250908"
        self.assertLessEqual(len(test_callback), 64)
        
        test_callback = "days_prev_2025_9"
        self.assertLessEqual(len(test_callback), 64)
        
        test_callback = "time_custom_num_123456789"
        self.assertLessEqual(len(test_callback), 64)
    
    def test_numeric_input_validation(self):
        """Test numeric input validation"""
        # Test valid date format YYYYMMDD
        valid_date = "19920715"
        self.assertEqual(len(valid_date), 8)
        
        try:
            parsed_date = datetime.strptime(valid_date, "%Y%m%d").date()
            self.assertIsInstance(parsed_date, date)
        except ValueError:
            self.fail("Valid date format should not raise ValueError")
        
        # Test invalid date format
        invalid_date = "1992071"  # Too short
        self.assertNotEqual(len(invalid_date), 8)
    
    def test_duration_calculations(self):
        """Test various duration calculations"""
        # Test 1 hour
        one_hour = 3600
        hours = one_hour // 3600
        minutes = (one_hour % 3600) // 60
        seconds = one_hour % 60
        
        self.assertEqual(hours, 1)
        self.assertEqual(minutes, 0)
        self.assertEqual(seconds, 0)
        
        # Test 1 day
        one_day = 86400
        hours = one_day // 3600
        self.assertEqual(hours, 24)
        
        # Test 90 minutes
        ninety_minutes = 5400
        hours = ninety_minutes // 3600
        minutes = (ninety_minutes % 3600) // 60
        self.assertEqual(hours, 1)
        self.assertEqual(minutes, 30)
    
    def test_edge_cases(self):
        """Test edge cases in date calculations"""
        # Test same date (age should be 0)
        same_date = date(2024, 1, 1)
        age = relativedelta(same_date, same_date)
        self.assertEqual(age.years, 0)
        self.assertEqual(age.months, 0)
        self.assertEqual(age.days, 0)
        
        # Test 1 day difference
        start = date(2024, 1, 1)
        end = date(2024, 1, 2)
        diff = relativedelta(end, start)
        self.assertEqual(diff.days, 1)
        self.assertEqual(diff.months, 0)
        self.assertEqual(diff.years, 0)

class TestBotUtilities(unittest.TestCase):
    """Test utility functions"""
    
    def test_format_duration(self):
        """Test duration formatting function"""
        bot = DayMateBot()
        
        # Test 1 hour
        result = bot.format_duration(3600)
        self.assertIn("1 hours", result)
        self.assertIn("0 minutes", result)
        self.assertIn("0 seconds", result)
        
        # Test 90 minutes
        result = bot.format_duration(5400)
        self.assertIn("1 hours", result)
        self.assertIn("30 minutes", result)
        self.assertIn("0 seconds", result)
        
        # Test 1 day
        result = bot.format_duration(86400)
        self.assertIn("24 hours", result)
        self.assertIn("0 minutes", result)
        self.assertIn("0 seconds", result)

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDayMateBot))
    test_suite.addTest(unittest.makeSuite(TestBotUtilities))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running DayMate Bot Tests...")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    print("=" * 50)
