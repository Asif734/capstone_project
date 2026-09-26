import json
import re
from pathlib import Path

import joblib
import lightgbm as lgb
import nltk
import pandas as pd
import xgboost as xgb
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = BACKEND_ROOT / "app" / "db" / "Combined Data.csv"
RESULTS_DIR = BACKEND_ROOT / "tests" / "results"
CSV_OUTPUT_PATH = RESULTS_DIR / "mental_health_model_accuracy_comparison.csv"
JSON_OUTPUT_PATH = RESULTS_DIR / "mental_health_model_accuracy_comparison.json"


def ensure_nltk_data() -> None:
    try:
        stopwords.words("english")
        WordNetLemmatizer().lemmatize("model")
    except LookupError:
        nltk.download("stopwords", quiet=True)
        nltk.download("wordnet", quiet=True)


def preprocess_text(text: str, stop_words: set[str], lemmatizer: WordNetLemmatizer) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = [word for word in text.split() if word not in stop_words]
    return " ".join(lemmatizer.lemmatize(word) for word in words)


def build_models() -> dict:
    return {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(random_state=42, n_estimators=100),
        "XGBoost": xgb.XGBClassifier(
            random_state=42,
            n_estimators=100,
            eval_metric="mlogloss",
        ),
        "LightGBM": lgb.LGBMClassifier(
            random_state=42,
            n_estimators=100,
            verbose=-1,
        ),
        "AdaBoost": AdaBoostClassifier(random_state=42, n_estimators=100),
    }


def main() -> None:
    ensure_nltk_data()
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()

    data = pd.read_csv(DATA_PATH).dropna(subset=["statement"])
    data["cleaned_text"] = data["statement"].apply(
        lambda text: preprocess_text(text, stop_words, lemmatizer)
    )

    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    features = vectorizer.fit_transform(data["cleaned_text"])
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(data["status"])
    train_features, test_features, train_labels, test_labels = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    results = []
    for model_name, model in build_models().items():
        model.fit(train_features, train_labels)
        predictions = model.predict(test_features)
        cv_scores = cross_val_score(model, features, labels, cv=5, scoring="accuracy")
        results.append(
            {
                "model": model_name,
                "test_accuracy": round(float(accuracy_score(test_labels, predictions)), 6),
                "kfold_accuracy_mean": round(float(cv_scores.mean()), 6),
                "kfold_accuracy_std": round(float(cv_scores.std()), 6),
                "kfold_scores": [round(float(score), 6) for score in cv_scores],
            }
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(CSV_OUTPUT_PATH, index=False)
    JSON_OUTPUT_PATH.write_text(
        json.dumps(
            {
                "dataset": str(DATA_PATH),
                "dataset_rows": len(data),
                "class_count": len(label_encoder.classes_),
                "classes": list(label_encoder.classes_),
                "test_split": "80/20, random_state=42, stratified",
                "cross_validation": "5-fold accuracy",
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Model                         Test Accuracy   5-Fold Accuracy")
    print("-" * 67)
    for result in results:
        print(
            f"{result['model']:<29} "
            f"{result['test_accuracy']:<16.4f} "
            f"{result['kfold_accuracy_mean']:.4f} "
            f"(+/- {result['kfold_accuracy_std']:.4f})"
        )
    print(f"\nSaved CSV: {CSV_OUTPUT_PATH}")
    print(f"Saved JSON: {JSON_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
