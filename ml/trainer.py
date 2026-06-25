import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

class MLTrainer:
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'demand_model.pkl')

    @classmethod
    def train_and_save(cls, historical_data=None):
        """
        Train the RandomForestRegressor on historical data and save the model.
        In a real scenario, `historical_data` would be a DataFrame fetched from the database.
        """
        print("Training new ML model...")
        
        if historical_data is None:
            # Generate synthetic data for training if none provided
            np.random.seed(42)
            n_samples = 1000
            
            # Features: day_of_week (0-6), hour (8-22), weather (0-2), is_holiday (0-1), is_event (0-1)
            days = np.random.randint(0, 7, n_samples)
            hours = np.random.randint(8, 23, n_samples)
            weather = np.random.choice([0, 1, 2], n_samples, p=[0.7, 0.2, 0.1])
            holidays = np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
            events = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
            
            features = pd.DataFrame({
                'day_of_week': days,
                'hour': hours,
                'weather': weather,
                'is_holiday': holidays,
                'is_event': events
            })
            
            # Targets: expected_customers, expected_orders
            # Synthetic logic: weekends and events increase traffic
            base_customers = 30 + (hours - 8) * 2 + (days >= 5) * 40 + events * 50 - weather * 10
            customers = base_customers + np.random.normal(0, 10, n_samples)
            customers = np.maximum(5, customers).astype(int)
            orders = (customers * np.random.uniform(1.1, 1.5, n_samples)).astype(int)
            
            targets = np.column_stack((customers, orders))
        else:
            features = historical_data[['day_of_week', 'hour', 'weather', 'is_holiday', 'is_event']]
            targets = historical_data[['customers', 'orders']]
            
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(features, targets)
        
        joblib.dump(model, cls.MODEL_PATH)
        print(f"Model saved to {cls.MODEL_PATH}")

if __name__ == '__main__':
    MLTrainer.train_and_save()
