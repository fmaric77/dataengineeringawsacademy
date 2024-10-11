import pytest
import asyncio
from day_4 import get_nobel_prizes_by_year, get_nobel_prizes_by_category

@pytest.mark.asyncio
async def test_get_nobel_prizes_by_year():
    years = ["2019", "2020", "2021"]
    for year in years:
        data = await get_nobel_prizes_by_year(year)
        assert len(data) == 6

@pytest.mark.asyncio
async def test_get_nobel_prizes_by_category():
    categories = ["chemistry", "physics", "medicine"]
    for category in categories:
        data = await get_nobel_prizes_by_category(category)
        assert len(data) == 123