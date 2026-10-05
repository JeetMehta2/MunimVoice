import json
import random
import datetime as dt
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from app.models.entities import Campaign, Customer
from app.sim.customer_response import CustomerResponseEngine

class CampaignUpliftSimulator:
    """
    Measures campaign uplift vs holdout group counterfactuals.
    Strictly simulated; all results prominently flagged with simulated=True.
    """

    @classmethod
    def run_simulation(
        cls, 
        session: Session, 
        campaign_id: int
    ) -> Dict[str, Any]:
        campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
        if not campaign:
            return {"error": "Campaign not found"}

        merchant_id = campaign.merchant_id
        discount_pct = campaign.discount_pct
        holdout_pct = campaign.holdout_pct or 0.20

        # Fetch audience
        customers = session.exec(
            select(Customer).where(Customer.merchant_id == merchant_id)
        ).all()
        if not customers:
            return {"error": "No customers found for merchant"}

        # Select target audience
        random.seed(42 + campaign_id)
        audience = list(customers)
        random.shuffle(audience)
        target_size = min(len(audience), max(10, campaign.audience_count or 40))
        audience = audience[:target_size]

        # Split into Treatment and Holdout
        holdout_size = max(2, int(len(audience) * holdout_pct))
        holdout_group = audience[:holdout_size]
        treatment_group = audience[holdout_size:]

        # Run simulated responses
        treatment_redemptions = 0
        treatment_revenue = 0.0
        avg_basket = 35.0  # Average order value

        for c in treatment_group:
            redeemed, _ = CustomerResponseEngine.simulate_customer_reaction(
                total_visits=c.total_visits,
                days_since_last_visit=15,
                discount_pct=discount_pct,
                is_target_window=True
            )
            if redeemed:
                treatment_redemptions += 1
                treatment_revenue += avg_basket * (1.0 - (discount_pct / 100.0))

        # Holdout response (natural baseline without discount)
        holdout_redemptions = 0
        holdout_revenue = 0.0
        for c in holdout_group:
            redeemed, _ = CustomerResponseEngine.simulate_customer_reaction(
                total_visits=c.total_visits,
                days_since_last_visit=15,
                discount_pct=0.0,
                is_target_window=False
            )
            if redeemed:
                holdout_redemptions += 1
                holdout_revenue += avg_basket

        # Normalize rates
        treatment_rate = treatment_redemptions / max(1, len(treatment_group))
        holdout_rate = holdout_redemptions / max(1, len(holdout_group))

        # Check if campaign worked
        if discount_pct < 5.0 or treatment_rate <= holdout_rate:
            did_work = False
            uplift_pct = 0.0
            verdict = "Campaign ne koi significant uplift generate nahi kiya (Discount bahot kam tha)."
        else:
            did_work = True
            raw_uplift = ((treatment_rate - holdout_rate) / max(0.01, holdout_rate)) * 100.0
            uplift_pct = round(raw_uplift, 1)
            verdict = f"Campaign safal raha! Holdout ke mukable +{uplift_pct}% extra orders mile."

        net_incremental_revenue = round(treatment_revenue - (holdout_revenue * (len(treatment_group) / max(1, len(holdout_group)))), 2)
        net_incremental_revenue = max(0.0, net_incremental_revenue)

        uplift_result = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "discount_pct": discount_pct,
            "treatment_audience": len(treatment_group),
            "treatment_redemptions": treatment_redemptions,
            "treatment_conversion_rate": round(treatment_rate * 100.0, 1),
            "holdout_audience": len(holdout_group),
            "holdout_redemptions": holdout_redemptions,
            "holdout_conversion_rate": round(holdout_rate * 100.0, 1),
            "uplift_pct": uplift_pct,
            "uplift_range": f"+{max(0.0, uplift_pct - 3.5):.1f}% to +{uplift_pct + 4.2:.1f}%",
            "net_incremental_revenue": net_incremental_revenue,
            "verdict": verdict,
            "did_work": did_work,
            "simulated": True,  # Mandatory honesty badge
            "timestamp": dt.datetime.utcnow().isoformat()
        }

        # Save to campaign record
        campaign.simulated_uplift = json.dumps(uplift_result)
        campaign.status = "COMPLETED"
        session.add(campaign)
        session.commit()

        return uplift_result
