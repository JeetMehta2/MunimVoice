import random
from typing import Tuple

class CustomerResponseEngine:
    """
    Dedicated Customer-Response Simulator.
    Simulates customer reaction to discount campaigns based on past behavior, discount magnitude,
    and target time window.
    
    CRITICAL ISOLATION RULES:
    1. Used STRICTLY for counterfactual uplift simulation.
    2. Never reads real merchant data or production database paths.
    3. Clearly separate from product mix inference code.
    """

    @staticmethod
    def calculate_redemption_probability(
        total_visits: int,
        days_since_last_visit: int,
        discount_pct: float,
        is_target_window: bool = True
    ) -> float:
        """
        Calculates redemption probability:
          - Discount scaling: higher discount yields non-linear uptake.
          - Customer loyalty: regular customers respond faster.
          - Churn lapse: inactive customers need higher discount to wake up.
          - Time relevance: matching the promotion window boosts likelihood.
        """
        if discount_pct <= 0.0:
            # Baseline natural purchase without offer
            return 0.05 if total_visits > 10 else 0.02

        # Base curve: S-curve or scaled discount
        base_rate = min(0.65, (discount_pct / 100.0) * 1.6)

        # Loyalty multiplier
        if total_visits >= 20:
            loyalty_mult = 1.45
        elif total_visits >= 8:
            loyalty_mult = 1.20
        else:
            loyalty_mult = 0.90

        # Inactivity dampener / incentive
        if days_since_last_visit >= 25:
            # Churned customer: low discount doesn't work, high discount triggers winback
            inactivity_mult = 1.30 if discount_pct >= 20.0 else 0.55
        else:
            inactivity_mult = 1.05

        # Timing multiplier
        timing_mult = 1.25 if is_target_window else 0.70

        prob = base_rate * loyalty_mult * inactivity_mult * timing_mult
        return round(min(0.85, max(0.01, prob)), 3)

    @classmethod
    def simulate_customer_reaction(
        cls,
        total_visits: int,
        days_since_last_visit: int,
        discount_pct: float,
        is_target_window: bool = True,
        rng: Optional[random.Random] = None
    ) -> Tuple[bool, float]:
        """
        Returns (redeemed: bool, probability: float)
        """
        r = rng or random
        prob = cls.calculate_redemption_probability(
            total_visits, days_since_last_visit, discount_pct, is_target_window
        )
        redeemed = (r.random() < prob)
        return redeemed, prob
