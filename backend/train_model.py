"""
Red-Flag ML Model Training Script
Generates synthetic medical training data and trains XGBoost classifier.
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for XGBoost
try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.error("Required packages not found. Install with: pip install xgboost scikit-learn pandas numpy")
    SKLEARN_AVAILABLE = False


def generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate synthetic medical data for training.
    
    Features:
    - age: Patient age (1-100)
    - symptom_count: Number of symptoms (1-10)
    - max_severity: Maximum symptom severity (0-3)
    - has_red_flag: Whether has red flag symptom (0/1)
    - duration_days: Symptom duration in days (0.04-365)
    - heart_rate: Heart rate (40-180)
    - systolic_bp: Systolic blood pressure (60-220)
    - diastolic_bp: Diastolic blood pressure (40-140)
    - temperature: Body temperature (35-42)
    - respiratory_rate: Respiratory rate (8-50)
    - oxygen_saturation: O2 saturation (70-100)
    - affected_systems_count: Number of body systems affected (1-5)
    
    Target:
    - high_risk: 1 if high risk, 0 if low risk
    """
    np.random.seed(42)
    
    data = {
        'age': np.random.randint(1, 100, n_samples),
        'symptom_count': np.random.randint(1, 10, n_samples),
        'max_severity': np.random.randint(0, 4, n_samples),
        'has_red_flag': np.random.binomial(1, 0.15, n_samples),
        'duration_days': np.random.exponential(7, n_samples).clip(0.04, 365),
        'heart_rate': np.random.normal(80, 20, n_samples).clip(40, 180),
        'systolic_bp': np.random.normal(120, 20, n_samples).clip(60, 220),
        'diastolic_bp': np.random.normal(80, 12, n_samples).clip(40, 140),
        'temperature': np.random.normal(37, 0.8, n_samples).clip(35, 42),
        'respiratory_rate': np.random.normal(16, 4, n_samples).clip(8, 50),
        'oxygen_saturation': 100 - np.random.exponential(2, n_samples).clip(0, 30),
        'affected_systems_count': np.random.randint(1, 6, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Generate target based on medical logic
    risk_score = np.zeros(n_samples)
    
    # Age risk (very young or elderly)
    risk_score += np.where((df['age'] < 5) | (df['age'] > 75), 0.15, 0)
    
    # Symptom count risk
    risk_score += df['symptom_count'] * 0.02
    
    # Severity risk
    risk_score += df['max_severity'] * 0.15
    
    # Red flag symptoms are high risk
    risk_score += df['has_red_flag'] * 0.35
    
    # Vital signs risks
    risk_score += np.where((df['heart_rate'] < 50) | (df['heart_rate'] > 110), 0.1, 0)
    risk_score += np.where((df['systolic_bp'] < 90) | (df['systolic_bp'] > 160), 0.12, 0)
    risk_score += np.where(df['temperature'] > 39, 0.15, 0)
    risk_score += np.where(df['temperature'] > 40, 0.2, 0)
    risk_score += np.where(df['oxygen_saturation'] < 95, 0.15, 0)
    risk_score += np.where(df['oxygen_saturation'] < 90, 0.25, 0)
    risk_score += np.where(df['respiratory_rate'] > 24, 0.1, 0)
    
    # Multiple systems affected
    risk_score += np.where(df['affected_systems_count'] >= 3, 0.1, 0)
    
    # Add some noise
    risk_score += np.random.normal(0, 0.05, n_samples)
    
    # Threshold for high risk
    df['high_risk'] = (risk_score > 0.5).astype(int)
    
    logger.info(f"Generated {n_samples} samples")
    logger.info(f"High risk cases: {df['high_risk'].sum()} ({df['high_risk'].mean()*100:.1f}%)")
    
    return df


def train_model(df: pd.DataFrame, save_path: Path) -> dict:
    """
    Train XGBoost classifier on the data.
    
    Args:
        df: Training data
        save_path: Path to save the model
        
    Returns:
        Dictionary with training metrics
    """
    feature_cols = [
        'age', 'symptom_count', 'max_severity', 'has_red_flag',
        'duration_days', 'heart_rate', 'systolic_bp', 'diastolic_bp',
        'temperature', 'respiratory_rate', 'oxygen_saturation',
        'affected_systems_count'
    ]
    
    X = df[feature_cols]
    y = df['high_risk']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    
    # Train XGBoost
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    logger.info("Training XGBoost model...")
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    roc_auc = roc_auc_score(y_test, y_proba)
    
    logger.info("\n" + "="*50)
    logger.info("MODEL EVALUATION RESULTS")
    logger.info("="*50)
    logger.info(f"\nROC-AUC Score: {roc_auc:.4f}")
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred))
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info("\nConfusion Matrix:")
    logger.info(f"  TN: {cm[0,0]:5d}  FP: {cm[0,1]:5d}")
    logger.info(f"  FN: {cm[1,0]:5d}  TP: {cm[1,1]:5d}")
    
    # Feature importance
    importance = dict(zip(feature_cols, model.feature_importances_))
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    logger.info("\nFeature Importance:")
    for feat, imp in sorted_importance:
        logger.info(f"  {feat:25s}: {imp:.4f}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
    logger.info(f"\n5-Fold CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    # Save model
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"\nModel saved to: {save_path}")
    
    return {
        'roc_auc': roc_auc,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'feature_importance': sorted_importance
    }


def validate_model(model_path: Path):
    """Validate a saved model with new synthetic data."""
    logger.info("Loading model for validation...")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Generate new test data
    df_test = generate_synthetic_data(n_samples=500)
    
    feature_cols = [
        'age', 'symptom_count', 'max_severity', 'has_red_flag',
        'duration_days', 'heart_rate', 'systolic_bp', 'diastolic_bp',
        'temperature', 'respiratory_rate', 'oxygen_saturation',
        'affected_systems_count'
    ]
    
    X_test = df_test[feature_cols]
    y_test = df_test['high_risk']
    
    y_proba = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, y_proba)
    
    logger.info(f"Validation ROC-AUC: {roc_auc:.4f}")
    
    # Test some edge cases
    logger.info("\nTesting edge cases...")
    
    # Critical case
    critical_case = np.array([[
        75,   # age
        5,    # symptom_count
        3,    # max_severity (critical)
        1,    # has_red_flag
        1,    # duration_days
        120,  # heart_rate
        180,  # systolic_bp
        100,  # diastolic_bp
        40,   # temperature
        28,   # respiratory_rate
        88,   # oxygen_saturation
        3     # affected_systems_count
    ]])
    
    critical_score = model.predict_proba(critical_case)[0, 1]
    logger.info(f"Critical case risk score: {critical_score:.4f} (expected > 0.8)")
    
    # Low risk case
    low_risk_case = np.array([[
        35,   # age
        1,    # symptom_count
        0,    # max_severity (mild)
        0,    # has_red_flag
        3,    # duration_days
        72,   # heart_rate
        118,  # systolic_bp
        78,   # diastolic_bp
        37.0, # temperature
        14,   # respiratory_rate
        99,   # oxygen_saturation
        1     # affected_systems_count
    ]])
    
    low_risk_score = model.predict_proba(low_risk_case)[0, 1]
    logger.info(f"Low risk case risk score: {low_risk_score:.4f} (expected < 0.3)")


def main():
    parser = argparse.ArgumentParser(description='Train Red-Flag ML Model')
    parser.add_argument('--samples', type=int, default=5000, help='Number of training samples')
    parser.add_argument('--validate', action='store_true', help='Run validation after training')
    args = parser.parse_args()
    
    if not SKLEARN_AVAILABLE:
        logger.error("Required dependencies not available. Exiting.")
        return
    
    # Paths
    base_dir = Path(__file__).parent
    model_path = base_dir / "app" / "models" / "red_flag_model.pkl"
    data_path = base_dir / "data" / "training_data" / "synthetic_data.csv"
    
    logger.info("="*60)
    logger.info("RED-FLAG ML MODEL TRAINING")
    logger.info("="*60)
    
    # Generate data
    logger.info("\nStep 1: Generating synthetic training data...")
    df = generate_synthetic_data(n_samples=args.samples)
    
    # Save training data
    data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(data_path, index=False)
    logger.info(f"Training data saved to: {data_path}")
    
    # Train model
    logger.info("\nStep 2: Training XGBoost classifier...")
    metrics = train_model(df, model_path)
    
    # Validate if requested
    if args.validate:
        logger.info("\nStep 3: Validating model...")
        validate_model(model_path)
    
    logger.info("\n" + "="*60)
    logger.info("TRAINING COMPLETE!")
    logger.info("="*60)
    logger.info(f"Model saved to: {model_path}")
    logger.info(f"ROC-AUC Score: {metrics['roc_auc']:.4f}")


if __name__ == "__main__":
    main()
