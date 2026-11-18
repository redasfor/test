"""Расчёт рекомендованной цены по предложениям конкурентов.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
sample_fetch_offers имитирует внешний источник: реальные запросы не нужны.

Контракт fetch_offers(): async-функция без аргументов, возвращает словарь
со status (success / partial / error) и offers (список предложений).
Все суммы на входе — положительные Decimal с точностью до копейки.
seller — строка; delivery_days — неотрицательное целое число или None.
Формат входных данных корректен; дополнительных проверок типов не требуется.
fetch_offers может завершиться исключением или долго ожидать ответа.
current_price — текущая цена; min_price — минимально допустимая цена.
timeout_s — положительное число секунд, по умолчанию 2.

ПРАВИЛА В ПОРЯДКЕ ПРИМЕНЕНИЯ
1. Ограничьте ожидание fetch_offers значением timeout_s. При ошибке источника,
   тайм-ауте или status != success верните текущую цену и HOLD.
2. Учитывайте предложения с известной доставкой не более 6 дней.
   Исключайте собственный магазин MYSHOP независимо от регистра букв.
3. Если подходящих предложений нет, верните текущую цену и HOLD,
   даже если текущая цена ниже min_price.
4. Минимальную цену подходящего конкурента уменьшите на 1,5% и округлите
   вниз до копейки. Рекомендация — максимум из этой суммы и min_price.
5. Если рекомендация отличается от текущей цены более чем на 30% в любую
   сторону, верните рекомендацию и REVIEW. Иначе — рекомендацию и APPLY.
   Ровно 30% допускается. REVIEW означает, что автоматическое применение
   запрещено до ручной проверки.

РЕЗУЛЬТАТ
Словарь с полями price (Decimal), decision (APPLY / REVIEW / HOLD),
reason (короткая понятная причина). Сохраните интерфейс recommend_price;
вспомогательные функции допустимы.
"""

import asyncio
from decimal import ROUND_DOWN, Decimal

OWN_SHOP = "myshop"
MAX_DELIVERY_DAYS = 6
DISCOUNT = Decimal("0.985")
KOPECK = Decimal("0.01")
REVIEW_THRESHOLD_PERCENT = 30


def _hold(current_price, reason):
    """Решение не менять цену."""
    return {"price": current_price, "decision": "HOLD", "reason": reason}


def _is_suitable(offer):
    """Предложение конкурента: не свой магазин и доставка известна и не более 6 дней."""
    if offer["seller"].strip().casefold() == OWN_SHOP:
        return False
    delivery_days = offer["delivery_days"]
    return delivery_days is not None and delivery_days <= MAX_DELIVERY_DAYS


def _round_down_to_kopeck(value):
    """Округление вниз до копейки."""
    return value.quantize(KOPECK, rounding=ROUND_DOWN)


def _needs_review(price, current_price):
    """Отклонение от текущей цены больше 30% в любую сторону."""
    return abs(price - current_price) * 100 > current_price * REVIEW_THRESHOLD_PERCENT


async def recommend_price(fetch_offers, current_price, min_price, timeout_s=2.0):
    """Возвращает рекомендованную цену и решение APPLY / REVIEW / HOLD."""
    try:
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)
    except asyncio.TimeoutError:
        return _hold(current_price, "источник не ответил за отведённое время")
    except Exception:
        return _hold(current_price, "ошибка источника")

    if result.get("status") != "success":
        return _hold(current_price, f"источник вернул статус {result.get('status')}")

    prices = [offer["price"] for offer in result.get("offers") or [] if _is_suitable(offer)]
    if not prices:
        return _hold(current_price, "нет подходящих предложений конкурентов")

    price = max(_round_down_to_kopeck(min(prices) * DISCOUNT), min_price)
    if _needs_review(price, current_price):
        return {"price": price, "decision": "REVIEW", "reason": "отклонение больше 30% от текущей цены"}
    return {"price": price, "decision": "APPLY", "reason": "цена по минимальному предложению конкурента"}


async def sample_fetch_offers():
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


if __name__ == "__main__":
    print(asyncio.run(recommend_price(
        sample_fetch_offers,
        current_price=Decimal("4900.00"),
        min_price=Decimal("4500.00"),
    )))
