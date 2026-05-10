import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import redis
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset
from backend.domain.models.prediction import Prediction

logger = logging.getLogger(__name__)


DASHBOARD_CACHE_TTL = 300


class DashboardService:
    @staticmethod
    def invalidate_cache(redis_client: redis.Redis, user_id: Optional[UUID] = None):
        try:
            if user_id:
                cache_key = f"dashboard:metrics:{user_id}"
                redis_client.delete(cache_key)
                logger.info(f"Invalidated dashboard cache for user {user_id}")
            else:
                pattern = "dashboard:metrics:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} dashboard cache entries")
        except Exception as e:
            logger.warning(f"Failed to invalidate dashboard cache: {e}")

    def compute_dashboard_metrics(self, db: Session, user_id: Optional[UUID] = None) -> Dict:
        try:
            query = db.query(CustomerRecord)
            if user_id:
                query = query.join(Dataset).filter(Dataset.user_id == user_id)

            total_customers = query.count()

            if total_customers == 0:
                return {
                    "total_customers": 0,
                    "churn_rate": 0.0,
                    "at_risk_count": 0,
                    "churned_count": 0,
                    "retained_count": 0,
                }

            churned_count = query.filter(CustomerRecord.churn.is_(True)).count()
            retained_count = total_customers - churned_count
            churn_rate = (churned_count / total_customers) * 100

            prediction_query = db.query(Prediction)
            if user_id:
                prediction_query = prediction_query.filter(Prediction.user_id == user_id)

            at_risk_count = prediction_query.filter(Prediction.probability > 0.70).count()

            metrics = {
                "total_customers": total_customers,
                "churn_rate": round(churn_rate, 2),
                "at_risk_count": at_risk_count,
                "churned_count": churned_count,
                "retained_count": retained_count,
            }

            logger.info(
                f"Computed dashboard metrics: total={total_customers}, "
                f"churn_rate={churn_rate:.2f}%, at_risk={at_risk_count}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error computing dashboard metrics: {e}", exc_info=True)
            raise

    def get_churn_distribution(self, db: Session, user_id: Optional[UUID] = None) -> Dict:
        try:
            query = db.query(CustomerRecord)
            if user_id:
                query = query.join(Dataset).filter(Dataset.user_id == user_id)

            churned_count = query.filter(CustomerRecord.churn.is_(True)).count()
            total_count = query.count()
            retained_count = total_count - churned_count

            distribution = {"churned": churned_count, "retained": retained_count}

            logger.info(
                f"Computed churn distribution: churned={churned_count}, "
                f"retained={retained_count}"
            )

            return distribution

        except Exception as e:
            logger.error(f"Error computing churn distribution: {e}", exc_info=True)
            raise

    def get_monthly_churn_trend(
        self, db: Session, user_id: Optional[UUID] = None, months: int = 12
    ) -> List[Dict]:
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)

            results = db.query(
                func.date_trunc("month", CustomerRecord.created_at).label("month"),
                func.count(CustomerRecord.id).label("total_count"),
                func.sum(func.cast(CustomerRecord.churn, db.bind.dialect.BIGINT)).label(
                    "churn_count"
                ),
            ).filter(CustomerRecord.created_at >= start_date, CustomerRecord.created_at <= end_date)

            if user_id:
                results = results.join(Dataset).filter(Dataset.user_id == user_id)

            results = (
                results.group_by(func.date_trunc("month", CustomerRecord.created_at))
                .order_by(func.date_trunc("month", CustomerRecord.created_at))
                .all()
            )

            trend_data = []
            for row in results:
                month_date = row.month
                total_count = row.total_count
                churn_count = row.churn_count or 0
                churn_rate = (churn_count / total_count * 100) if total_count > 0 else 0.0

                trend_data.append(
                    {
                        "month": month_date.strftime("%Y-%m"),
                        "churn_count": churn_count,
                        "total_count": total_count,
                        "churn_rate": round(churn_rate, 2),
                    }
                )

            if not trend_data:
                logger.warning("No data available for monthly churn trend")
                return []

            logger.info(f"Computed monthly churn trend for {len(trend_data)} months")

            return trend_data

        except Exception as e:
            logger.error(f"Error computing monthly churn trend: {e}", exc_info=True)
            raise
