import unittest
import asyncio
from day_4 import get_nobel_prizes_by_year, get_nobel_prizes_by_category

class TestNobelPrizes(unittest.TestCase):

    def test_get_nobel_prizes_by_year(self):
        async def run_test():
            years = ["2019", "2020", "2021"]
            for year in years:
                data = await get_nobel_prizes_by_year(year)
                self.assertEqual(len(data), 6)
        
        asyncio.run(run_test())

    def test_get_nobel_prizes_by_category(self):
        async def run_test():
            categories = ["chemistry", "physics", "medicine"]
            for category in categories:
                data = await get_nobel_prizes_by_category(category)
                self.assertEqual(len(data), 123)
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()