"""Service for time series forecasting.

Supports three model types:
- prophet: Facebook Prophet (seasonality, holiday handling)
- ets: Exponential Smoothing (statsmodels)
- arima: Auto ARIMA (pmdarima or statsmodels)

Key design:
- All forecasting is background jobs (Celery)
- LLM only interprets results, never configures models
- Forecast results stored as JSON in DB
- Every forecast job scoped by org_id
"""
import logging
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ForecastResult:
    """Structured forecast result container."""

    def __init__(
        self,
        model_type: str,
        target_column: str,
        date_column: str,
        horizon: int,
        forecast_values: List[float],
        confidence_intervals: Optional[List[Tuple[float, float]]] = None,
        model_params: Optional[Dict] = None,
        residuals: Optional[Dict] = None,
    ):
        self.model_type = model_type
        self.target_column = target_column
        self.date_column = date_column
        self.horizon = horizon
        self.forecast_values = forecast_values
        self.confidence_intervals = confidence_intervals or []
        self.model_params = model_params or {}
        self.residuals = residuals or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for DB storage."""
        return {
            "model_type": self.model_type,
            "target_column": self.target_column,
            "date_column": self.date_column,
            "horizon": self.horizon,
            "forecast_values": self.forecast_values,
            "confidence_intervals": self.confidence_intervals,
            "model_params": self.model_params,
            "residuals": self.residuals,
        }

    @staticmethod
    def from_dict(d: Dict) -> "ForecastResult":
        """Create from dict (loaded from DB)."""
        return ForecastResult(
            model_type=d.get("model_type", "prophet"),
            target_column=d.get("target_column", ""),
            date_column=d.get("date_column", ""),
            horizon=d.get("horizon", 12),
            forecast_values=d.get("forecast_values", []),
            confidence_intervals=d.get("confidence_intervals", []),
            model_params=d.get("model_params", {}),
            residuals=d.get("residuals", {}),
        )


class ForecastService:
    """Service for running time series forecasts."""

    @staticmethod
    def validate_forecast_request(
        df: pd.DataFrame,
        target_column: str,
        date_column: str,
        horizon: int,
    ) -> Tuple[bool, str]:
        """Validate forecast request before running.

        Returns (is_valid, error_message).
        """
        # Check date column exists and is parseable
        if date_column not in df.columns:
            return False, f"Date column '{date_column}' not found in dataset"

        # Check target column exists
        if target_column not in df.columns:
            return False, f"Target column '{target_column}' not found in dataset"

        # Check we have enough data points
        if len(df) < 10:
            return False, f"Insufficient data: need at least 10 rows, have {len(df)}"

        # Check date column can be parsed
        try:
            pd.to_datetime(df[date_column])
        except Exception:
            return False, f"Cannot parse date column: {date_column}"

        # Check target column has numeric data
        try:
            pd.to_numeric(df[target_column], errors="raise")
        except Exception:
            return False, f"Target column '{target_column}' is not numeric"

        # Check horizon is reasonable
        if horizon < 1:
            return False, "Horizon must be at least 1 period"
        if horizon > 100:
            return False, "Horizon too large: maximum 100 periods"

        return True, ""

    @staticmethod
    def _prepare_data(
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
    ) -> pd.DataFrame:
        """Prepare data for forecasting.

        - Sort by date
        - Ensure datetime type
        - Ensure target is numeric
        - Remove NaN pairs
        """
        df_prepared = df[[date_column, target_column]].copy()
        df_prepared[date_column] = pd.to_datetime(df_prepared[date_column])
        df_prepared = df_prepared.sort_values(by=date_column)
        df_prepared[target_column] = pd.to_numeric(df_prepared[target_column], errors="coerce")
        df_prepared = df_prepared.dropna(subset=[target_column])
        return df_prepared

    @staticmethod
    def run_prophet_forecast(
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon: int,
    ) -> ForecastResult:
        """Run Prophet forecast.

        In production, would use fbprophet/prophet library.
        For now, returns a placeholder result using simple trend extrapolation.
        """
        try:
            from prophet import Prophet
        except ImportError:
            # Fallback: simple trend extrapolation
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "prophet"
            )

        # Prepare data for Prophet
        df_prophet = df[[date_column, target_column]].rename(
            columns={date_column: "ds", target_column: "y"}
        )
        df_prophet = df_prophet.dropna()

        if len(df_prophet) < 3:
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "prophet"
            )

        try:
            model = Prophet(
                yearly_seasonality='auto',
                weekly_seasonality='auto',
                daily_seasonality=False,
                horizon=horizon,
            )
            model.fit(df_prophet)

            # Make forecast
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)

            # Extract results
            forecast_values = forecast['yhat'].tail(horizon).tolist()
            ci_lower = forecast['yhat_lower'].tail(horizon).tolist()
            ci_upper = forecast['yhat_upper'].tail(horizon).tolist()
            confidence_intervals = list(zip(ci_lower, ci_upper))

            # Extract model params
            model_params = {
                "changepoint_rate": model.changepoint_rate,
                "seasonality_mode": model.seasonality_mode,
            }

            # Get residuals if available
            residuals = {}
            if hasattr(model, 'resid'):
                residuals = {"mse": float(model.resid.var()) if len(model.resid) > 0 else 0}

            return ForecastResult(
                model_type="prophet",
                target_column=target_column,
                date_column=date_column,
                horizon=horizon,
                forecast_values=forecast_values,
                confidence_intervals=confidence_intervals,
                model_params=model_params,
                residuals=residuals,
            )

        except Exception as e:
            logger.error(f"Prophet forecast failed: {e}")
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "prophet"
            )

    @staticmethod
    def _simple_forecast(
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon: int,
        model_type: str,
    ) -> ForecastResult:
        """Simple fallback forecast using linear extrapolation.

        Used when Prophet/ETS/ARIMA are unavailable.
        """
        df_prepared = ForecastService._prepare_data(df, date_column, target_column)

        if len(df_prepared) < 3:
            # Not enough data - return zeros
            last_date = df_prepared[date_column].max()
            return ForecastResult(
                model_type=model_type,
                target_column=target_column,
                date_column=date_column,
                horizon=horizon,
                forecast_values=[0.0] * horizon,
                confidence_intervals=[(0.0, 0.0)] * horizon,
                model_params={"method": "fallback_simple", "note": "Insufficient data for real forecast"},
                residuals={},
            )

        # Simple linear regression / extrapolation
        values = df_prepared[target_column].values
        dates = df_prepared[date_column].values

        # Fit simple line: y = slope * x + intercept
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)

        # Forecast future values
        forecast_values = []
        confidence_intervals = []

        for i in range(1, horizon + 1):
            future_x = len(values) + i - 1
            predicted = slope * future_x + intercept
            # Simple confidence interval: ±2 * std of residuals
            residual_std = float(np.std(values - (slope * x + intercept))) if len(values) > 1 else 0.0
            ci_lower = predicted - 2 * residual_std
            ci_upper = predicted + 2 * residual_std

            forecast_values.append(float(predicted))
            confidence_intervals.append((float(ci_lower), float(ci_upper)))

        # Model params
        model_params = {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(np.corrcoef(x, values)[0, 1] ** 2) if len(values) > 1 else 0.0,
            "method": "linear_regression",
        }

        # Residuals
        fitted = slope * x + intercept
        residuals = {"mse": float(np.mean((values - fitted) ** 2)) if len(values) > 0 else 0.0}

        # Last date for reference
        last_date = df_prepared[date_column].max()

        return ForecastResult(
            model_type=model_type,
            target_column=target_column,
            date_column=date_column,
            horizon=horizon,
            forecast_values=forecast_values,
            confidence_intervals=confidence_intervals,
            model_params=model_params,
            residuals=residuals,
        )

    @staticmethod
    def run_ets_forecast(
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon: int,
    ) -> ForecastResult:
        """Run ETS (Exponential Smoothing) forecast using statsmodels.

        Falls back to simple method if statsmodels unavailable.
        """
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
        except ImportError:
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "ets"
            )

        df_prepared = ForecastService._prepare_data(df, date_column, target_column)

        if len(df_prepared) < 10:
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "ets"
            )

        try:
            # Determine seasonal period based on data frequency
            # Default to additive model; detect multiplicative if variance grows
            values = df_prepared[target_column].values

            # Try additive first, then multiplicative if appropriate
            try:
                model = ExponentialSmoothing(
                    values,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=min(12, len(values) // 2),
                )
                fitted = model.fit()

                # Forecast
                forecast_values = fitted.forecast(horizon).tolist()

                # Confidence intervals
                ci = fitted.forecast(horizon, alpha=0.05)  # 95% CI
                ci_lower = ci.iloc[:, 0].tolist() if hasattr(ci, 'iloc') else ci[0].tolist()
                ci_upper = ci.iloc[:, 1].tolist() if hasattr(ci, 'iloc') else ci[1].tolist()
                confidence_intervals = list(zip(ci_lower, ci_upper))

                model_params = {
                    "trend": fitted.trend,
                    "seasonal": str(fitted.seasonal)[:50] if hasattr(fitted, 'seasonal') else "N/A",
                    "optimized_params": fitted.params,
                }

                residuals = {
                    "mse": float(fitted.sse / len(residuals)) if (residuals := len(fitted.resid)) > 0 else 0,
                }

                return ForecastResult(
                    model_type="ets",
                    target_column=target_column,
                    date_column=date_column,
                    horizon=horizon,
                    forecast_values=forecast_values,
                    confidence_intervals=confidence_intervals,
                    model_params=model_params,
                    residuals=residuals,
                )

            except Exception:
                # Try multiplicative seasonality
                try:
                    model = ExponentialSmoothing(
                        values,
                        trend="add",
                        seasonal="mul",
                        seasonal_periods=min(12, len(values) // 2),
                    )
                    fitted = model.fit()

                    forecast_values = fitted.forecast(horizon).tolist()
                    ci = fitted.forecast(horizon, alpha=0.05)
                    ci_lower = ci.iloc[:, 0].tolist() if hasattr(ci, 'iloc') else ci[0].tolist()
                    ci_upper = ci.iloc[:, 1].tolist() if hasattr(ci, 'iloc') else ci[1].tolist()
                    confidence_intervals = list(zip(ci_lower, ci_upper))

                    model_params = {
                        "trend": fitted.trend,
                        "seasonal": str(fitted.seasonal)[:50] if hasattr(fitted, 'seasonal') else "N/A",
                    }

                    residuals = {"mse": float(fitted.sse / len(fitted.resid)) if len(fitted.resid) > 0 else 0}

                    return ForecastResult(
                        model_type="ets",
                        target_column=target_column,
                        date_column=date_column,
                        horizon=horizon,
                        forecast_values=forecast_values,
                        confidence_intervals=confidence_intervals,
                        model_params=model_params,
                        residuals=residuals,
                    )

                except Exception as e2:
                    logger.error(f"ETS forecast failed both attempts: {e2}")
                    return ForecastService._simple_forecast(
                        df, date_column, target_column, horizon, "ets"
                    )

        except Exception as e:
            logger.error(f"ETS forecast failed: {e}")
            return ForecastService._simple_forecast(
                df, date_column, target_column, horizon, "ets"
            )

    @staticmethod
    def run_arima_forecast(
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon: int,
    ) -> ForecastResult:
        """Run ARIMA forecast.

        Falls back to ETS or simple method if pmdarima/unavailable.
        """
        try:
            import pmdarima as pm
        except ImportError:
            # Fall back to ETS
            return ForecastService.run_ets_forecast(df, date_column, target_column, horizon)

        df_prepared = ForecastService._prepare_data(df, date_column, target_column)

        if len(df_prepared) < 15:
            return ForecastService.run_ets_forecast(df, date_column, target_column, horizon)

        try:
            # Auto-ARIMA - find best parameters
            stepwise_model = pm.auto_arima(
                df_prepared[target_column],
                seasonal=True,
                m=min(12, len(df_prepared) // 12),  # seasonal period
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
            )

            # Forecast
            forecast_result = stepwise_model.predict(n_periods=horizon)
            forecast_values = forecast_result.tolist()

            # Confidence intervals
            ci = stepwise_model.predict_interval(n_periods=horizon, alpha=0.05)
            ci_lower = ci[:, 0].tolist()
            ci_upper = ci[:, 1].tolist()
            confidence_intervals = list(zip(ci_lower, ci_upper))

            model_params = {
                "order": stepwise_model.order,
                "seasonal_order": stepwise_model.seasonal_order,
                "aic": float(stepwise_model.aic()),
                "bic": float(stepwise_model.bic()),
            }

            residuals = {
                "aic": float(stepwise_model.aic()),
                "bic": float(stepwise_model.bic()),
                "log_likelihood": float(stepwise_model.log_likelihood()),
            }

            return ForecastResult(
                model_type="arima",
                target_column=target_column,
                date_column=date_column,
                horizon=horizon,
                forecast_values=forecast_values,
                confidence_intervals=confidence_intervals,
                model_params=model_params,
                residuals=residuals,
            )

        except Exception as e:
            logger.error(f"ARIMA forecast failed: {e}")
            # Fall back to ETS
            return ForecastService.run_ets_forecast(df, date_column, target_column, horizon)