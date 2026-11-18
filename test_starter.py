"""Тесты recommend_price. Запуск: python test_starter.py"""

import asyncio
import unittest
from decimal import Decimal

from starter import recommend_price


def _source(offers, status="success"):
    """Источник, который сразу отдаёт заданные предложения."""
    async def fetch_offers():
        return {"status": status, "offers": offers}
    return fetch_offers


class RecommendPriceTest(unittest.IsolatedAsyncioTestCase):
    async def test_basic_calculation(self):
        """Свой магазин и доставка дольше 6 дней в расчёт не идут."""
        offers = [
            {"seller": "MyShop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ]
        result = await recommend_price(_source(offers), Decimal("4900.00"), Decimal("4500.00"))
        self.assertEqual(result["price"], Decimal("4728.00"))
        self.assertEqual(result["decision"], "APPLY")

    async def test_source_timeout_returns_hold(self):
        """Тайм-аут источника: цена не меняется."""
        async def slow_source():
            await asyncio.sleep(10)
            return {"status": "success", "offers": []}

        result = await recommend_price(slow_source, Decimal("4900.00"), Decimal("4500.00"), timeout_s=0.01)
        self.assertEqual(result["price"], Decimal("4900.00"))
        self.assertEqual(result["decision"], "HOLD")

    async def test_deviation_boundary(self):
        """Ровно 30% — APPLY, чуть больше — REVIEW."""
        current_price, min_price = Decimal("4900.00"), Decimal("1000.00")
        at_boundary = [{"seller": "A", "price": Decimal("3482.24"), "delivery_days": 1}]
        over_boundary = [{"seller": "A", "price": Decimal("3482.23"), "delivery_days": 1}]

        result = await recommend_price(_source(at_boundary), current_price, min_price)
        self.assertEqual(result["price"], Decimal("3430.00"))
        self.assertEqual(result["decision"], "APPLY")

        result = await recommend_price(_source(over_boundary), current_price, min_price)
        self.assertEqual(result["price"], Decimal("3429.99"))
        self.assertEqual(result["decision"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
