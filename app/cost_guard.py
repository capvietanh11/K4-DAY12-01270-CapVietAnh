"""CP3 - Cost guard."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

KEY_TTL_SECONDS = 3 * 24 * 3600


class CostGuard:
    def __init__(self, client, daily_budget_usd: float) -> None:
        self.client = client
        self.budget = daily_budget_usd

    @staticmethod
    def today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    def _key(cls, client_id: str, day: str | None = None) -> str:
        return f"spend:{client_id}:{day or cls.today()}"

    def spent(self, client_id: str, day: str | None = None) -> float:
        value = self.client.get(self._key(client_id, day))
        return 0.0 if value is None else float(value)

    def check(
        self,
        client_id: str,
        estimated_cost: float = 0.0,
        day: str | None = None,
    ) -> None:
        if self.spent(client_id, day) + estimated_cost > self.budget:
            raise HTTPException(status_code=402, detail="daily budget exceeded")

    def record(self, client_id: str, cost: float, day: str | None = None) -> float:
        key = self._key(client_id, day)
        total = self.client.incrbyfloat(key, cost)
        self.client.expire(key, KEY_TTL_SECONDS)
        return float(total)

    def remaining(self, client_id: str, day: str | None = None) -> float:
        return max(0.0, self.budget - self.spent(client_id, day))
