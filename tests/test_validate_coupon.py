import asyncio

from backend import server


class FakeCoupons:
    async def find_one(self, query):
        code = query.get("code")
        if code == "SAVE10":
            return {
                "_id": "c1",
                "code": "SAVE10",
                "discount_type": "fixed",
                "amount": 15,
            }
        if code == "DOUBLE":
            return {
                "_id": "c2",
                "code": "DOUBLE",
                "discount_type": "percent",
                "amount": 200,
            }
        return None


class FakeDB:
    coupons = FakeCoupons()


def test_fixed_coupon_discount_cannot_exceed_subtotal(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDB())
    req = server.CouponCheckRequest(code="SAVE10", subtotal=10)
    result = asyncio.run(server.validate_coupon(req))
    assert result["discount_amount"] == 10


def test_percent_coupon_discount_cannot_exceed_subtotal(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDB())
    req = server.CouponCheckRequest(code="DOUBLE", subtotal=10)
    result = asyncio.run(server.validate_coupon(req))
    assert result["discount_amount"] == 10
