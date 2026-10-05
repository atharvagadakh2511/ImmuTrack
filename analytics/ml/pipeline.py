import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from django.conf import settings

MODEL_DIR = Path(settings.BASE_DIR) / 'ml_models'
MODEL_PATH = MODEL_DIR / 'defaulter_risk_model.joblib'

class DefaulterRiskPipeline:
    """
    Academic & Clinical Decision Support ML Module.
    Predicts probability of a child defaulting on upcoming immunization doses.
    Features strictly use past adherence behavior and delay history without demographic bias.
    """

    @classmethod
    def train_and_persist(cls, df_synthetic=None):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        # If no custom data passed, generate reproducible synthetic dataset for academic demo
        if df_synthetic is None or len(df_synthetic) < 30:
            df = cls._generate_synthetic_training_data()
        else:
            df = df_synthetic

        # Feature matrix & target
        feature_cols = [
            'total_past_doses',
            'past_overdue_count',
            'overdue_ratio',
            'avg_delay_days',
            'days_since_last_visit',
        ]
        
        X = df[feature_cols]
        y = df['defaulter_target']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

        # Baseline Classifier
        clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
            'features': feature_cols
        }

        # Persist model
        payload = {
            'model': clf,
            'features': feature_cols,
            'metrics': metrics
        }
        joblib.dump(payload, MODEL_PATH)
        return metrics

    @classmethod
    def load_model(cls):
        if not os.path.exists(MODEL_PATH):
            return None
        return joblib.load(MODEL_PATH)

    @classmethod
    def evaluate_child_features(cls, child):
        """
        Extracts temporal non-leaking features from child dose history.
        """
        doses = child.scheduled_doses.all()
        total_doses = doses.count()
        if total_doses < 2:
            return None # Insufficient history for ML scoring

        overdue_count = doses.filter(status='OVERDUE').count()
        completed_doses = doses.filter(status='COMPLETED')
        completed_count = completed_doses.count()
        
        overdue_ratio = overdue_count / total_doses if total_doses > 0 else 0.0

        # Calculate average historical delay
        delays = []
        for cd in completed_doses:
            if hasattr(cd, 'administration_record'):
                delta = (cd.administration_record.administered_date - cd.due_date).days
                if delta > 0:
                    delays.append(delta)

        avg_delay = float(np.mean(delays)) if len(delays) > 0 else 0.0

        # Days since last completed dose
        if completed_doses.exists():
            latest_adm = completed_doses.order_by('-due_date').first()
            if hasattr(latest_adm, 'administration_record'):
                from datetime import date
                days_since = (date.today() - latest_adm.administration_record.administered_date).days
            else:
                days_since = 30
        else:
            days_since = 90

        return pd.DataFrame([{
            'total_past_doses': total_doses,
            'past_overdue_count': overdue_count,
            'overdue_ratio': overdue_ratio,
            'avg_delay_days': avg_delay,
            'days_since_last_visit': max(0, days_since),
        }])

    @classmethod
    def predict_risk(cls, child):
        payload = cls.load_model()
        if not payload:
            return {
                'level': 'INSUFFICIENT_DATA',
                'probability': 0.0,
                'factor': 'ML model not trained yet. Run train command.'
            }

        features_df = cls.evaluate_child_features(child)
        if features_df is None:
            return {
                'level': 'INSUFFICIENT_DATA',
                'probability': 0.0,
                'factor': 'New profile with fewer than 2 scheduled doses'
            }

        model = payload['model']
        prob = model.predict_proba(features_df)[0][1]

        # Determine level and key driver
        if prob >= 0.65:
            level = 'HIGH'
            factor = 'Repeated overdue history and high administration interval lag'
        elif prob >= 0.35:
            level = 'MEDIUM'
            factor = 'Occasional overdue history; prompt follow-up advised'
        else:
            level = 'LOW'
            factor = 'Consistent adherence pattern observed'

        return {
            'level': level,
            'probability': float(prob),
            'factor': factor
        }

    @staticmethod
    def _generate_synthetic_training_data(n_samples=200):
        np.random.seed(42)
        total_past_doses = np.random.randint(2, 12, size=n_samples)
        past_overdue_count = np.array([np.random.randint(0, t) for t in total_past_doses])
        overdue_ratio = past_overdue_count / total_past_doses
        avg_delay_days = np.random.exponential(scale=10, size=n_samples) + (past_overdue_count * 4)
        days_since_last_visit = np.random.randint(15, 180, size=n_samples)

        # Risk logic
        logits = -1.8 + (overdue_ratio * 4.2) + (avg_delay_days * 0.08) + (days_since_last_visit * 0.015)
        probs = 1 / (1 + np.exp(-logits))
        target = (probs > 0.45).astype(int)

        return pd.DataFrame({
            'total_past_doses': total_past_doses,
            'past_overdue_count': past_overdue_count,
            'overdue_ratio': overdue_ratio,
            'avg_delay_days': avg_delay_days,
            'days_since_last_visit': days_since_last_visit,
            'defaulter_target': target
        })
