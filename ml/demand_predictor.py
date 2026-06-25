import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, date
import xgboost as xgb

class DemandPredictor:
    MODEL_DIR = os.path.dirname(__file__)
    _cached_models = {}
    
    @classmethod
    def get_model_path(cls, name):
        return os.path.join(cls.MODEL_DIR, f"{name}_xgb_model.json")

    @classmethod
    def get_model(cls, target):
        model_path = cls.get_model_path(target)
        if not os.path.exists(model_path):
            return None
        if target in cls._cached_models:
            return cls._cached_models[target]
        try:
            model = xgb.XGBRegressor()
            model.load_model(model_path)
            cls._cached_models[target] = model
            return model
        except Exception as e:
            print(f"Error loading model {target}: {e}")
            return None

    @classmethod
    def train_and_save(cls, historical_records):
        """
        Train XGBoost Regressor models on daily historical data.
        """
        cls._cached_models.clear()
        print(f"Training XGBoost models with {len(historical_records)} records...")
        
        # Convert records to list of dicts
        data = []
        for r in historical_records:
            if hasattr(r, 'date'):
                data.append({
                    'date': r.date,
                    'orders_count': r.orders_count,
                    'reservations_count': r.reservations_count,
                    'customers_count': r.customers_count
                })
            else:
                data.append(r)
                
        # If too few records, supplement with synthetic data to make the model robust
        if len(data) < 15:
            print("Supplementing with synthetic historical data for robust training...")
            np.random.seed(42)
            existing_dates = {r['date'] for r in data}
            
            # Use current date as reference
            ref_date = date.today()
            for i in range(1, 40):
                d = ref_date - pd.Timedelta(days=i)
                d = d.date() if hasattr(d, 'date') else d
                if d not in existing_dates:
                    # Synthesize values based on day of week
                    dow = d.weekday()
                    is_we = 1 if dow >= 5 else 0
                    
                    # Generate base values
                    base_orders = 15 + is_we * 25 + np.random.randint(-3, 5)
                    base_res = 5 + is_we * 12 + np.random.randint(-2, 3)
                    base_cust = base_orders + base_res + np.random.randint(-2, 5)
                    
                    data.append({
                        'date': d,
                        'orders_count': max(1, base_orders),
                        'reservations_count': max(0, base_res),
                        'customers_count': max(1, base_cust)
                    })

        # Create DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.weekday
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        X = df[['day_of_week', 'day_of_month', 'month', 'is_weekend']]

        # Train models
        for target in ['customers_count', 'orders_count', 'reservations_count']:
            y = df[target]
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.08,
                random_state=42
            )
            model.fit(X, y)
            model.save_model(cls.get_model_path(target))
            print(f"Saved XGBoost model for {target}")

    @classmethod
    def predict_day(cls, target_date):
        """
        Predict expected customer, order, and reservation count for a target date.
        """
        # Ensure target_date is a date object
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        day_of_week = target_date.weekday()
        day_of_month = target_date.day
        month = target_date.month
        is_weekend = 1 if day_of_week >= 5 else 0

        features = pd.DataFrame([{
            'day_of_week': day_of_week,
            'day_of_month': day_of_month,
            'month': month,
            'is_weekend': is_weekend
        }])

        preds = {}
        fallback = False

        for target in ['customers_count', 'orders_count', 'reservations_count']:
            model = cls.get_model(target)
            if model is None:
                fallback = True
                break
            try:
                pred_val = model.predict(features)[0]
                preds[target] = max(0, int(round(pred_val)))
            except Exception as e:
                print(f"Error predicting {target}: {e}")
                fallback = True
                break

        if fallback:
            # Fallback baseline predictions if models don't exist
            base_orders = 20 + is_weekend * 30
            base_res = 8 + is_weekend * 15
            preds = {
                'customers_count': base_orders + base_res,
                'orders_count': base_orders,
                'reservations_count': base_res
            }

        return preds

    @classmethod
    def predict(cls, target_datetime: datetime, is_holiday: int = 0, is_event: int = 0, weather_condition: int = 0):
        """
        Hourly prediction helper for backward compatibility.
        """
        day_preds = cls.predict_day(target_datetime.date())
        # Divide daily predictions across opening hours (approx. 13 hours: 9:00 AM to 9:00 PM)
        return {
            "expected_customers": int(day_preds['customers_count'] / 13) or 3,
            "expected_orders": int(day_preds['orders_count'] / 13) or 4,
            "inventory_alert": '[]'
        }
