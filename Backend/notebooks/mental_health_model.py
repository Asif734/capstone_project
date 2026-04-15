import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
import mlflow
import mlflow.sklearn
import joblib

# Download NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Set up MLflow
mlflow.set_experiment("Mental Health Detection")

print("Libraries imported and MLflow set up.")

# Load the dataset
df = pd.read_csv('app/db/Combined Data.csv')
print(f"Dataset shape: {df.shape}")
print(df.head())
print(df.info())

# Exploratory Data Analysis
plt.figure(figsize=(8, 6))
sns.countplot(data=df, x='status')  # Assuming 'status' is the target column
plt.title('Distribution of Mental Health Status')
plt.show()

# Check for missing values
print(df.isnull().sum())

# Handle missing values
df = df.dropna(subset=['statement'])

# Text length analysis
df['text_length'] = df['statement'].apply(len)  # Assuming 'statement' is the text column
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='text_length', hue='status', bins=50)
plt.title('Text Length Distribution by Status')
plt.show()

# Text Preprocessing
def preprocess_text(text):
    # Lowercase
    text = text.lower()
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]
    return ' '.join(words)

df['cleaned_text'] = df['statement'].apply(preprocess_text)
print(df[['statement', 'cleaned_text']].head())

# Feature Extraction
tfidf = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X = tfidf.fit_transform(df['cleaned_text'])
y = df['status']

# Encode labels if needed
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

print(f"Training set shape: {X_train.shape}")
print(f"Test set shape: {X_test.shape}")
print(f"Classes: {le.classes_}")

# Model Training and Evaluation
models = {
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Random Forest': RandomForestClassifier(random_state=42, n_estimators=100),
    'XGBoost': xgb.XGBClassifier(random_state=42, n_estimators=100, eval_metric='mlogloss'),
    'LightGBM': lgb.LGBMClassifier(random_state=42, n_estimators=100, verbose=-1),
    'AdaBoost': AdaBoostClassifier(random_state=42, n_estimators=100)
}

results = {}

for name, model in models.items():
    with mlflow.start_run(run_name=name):
        # Train model
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = None
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_test)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        # For multi-class, use macro average for ROC-AUC
        if y_pred_proba is not None:
            try:
                roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='macro')
            except:
                roc_auc = 0.0  # In case of issues
        else:
            roc_auc = 0.0  # For models without predict_proba
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("roc_auc", roc_auc)
        
        # Log model
        mlflow.sklearn.log_model(model, name)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title(f'Confusion Matrix - {name}')
        plt.savefig(f'cm_{name}.png')
        mlflow.log_artifact(f'cm_{name}.png')
        plt.close()
        
        results[name] = {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'classification_report': classification_report(y_test, y_pred, target_names=le.classes_)
        }
        
        print(f"{name} - Accuracy: {accuracy:.4f}, ROC-AUC: {roc_auc:.4f}")

# Print detailed results
for name, result in results.items():
    print(f"\n{name}:")
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"ROC-AUC: {result['roc_auc']:.4f}")
    print("Classification Report:")
    print(result['classification_report'])

# Cross-validation for robustness
for name, model in models.items():
    cv_scores = cross_val_score(model, X, y_encoded, cv=5, scoring='accuracy')
    print(f"{name} CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    with mlflow.start_run(run_name=f"{name}_CV"):
        mlflow.log_metric("cv_mean_accuracy", cv_scores.mean())
        mlflow.log_metric("cv_std_accuracy", cv_scores.std())

# Save the best model
best_model_name = max(results, key=lambda x: results[x]['accuracy'])  # Changed to accuracy instead of ROC-AUC
best_model = models[best_model_name]

with mlflow.start_run(run_name="Best Model"):
    mlflow.sklearn.log_model(best_model, "best_model")
    mlflow.log_param("best_model_name", best_model_name)
    mlflow.log_metric("best_accuracy", results[best_model_name]['accuracy'])
    mlflow.log_metric("best_roc_auc", results[best_model_name]['roc_auc'])

print(f"Best model: {best_model_name} with ROC-AUC: {results[best_model_name]['roc_auc']:.4f}")

# Save the TF-IDF vectorizer as well
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
print("Saved tfidf_vectorizer.pkl")
mlflow.log_artifact('tfidf_vectorizer.pkl')

# Save the label encoder
joblib.dump(le, 'label_encoder.pkl')
print("Saved label_encoder.pkl")
mlflow.log_artifact('label_encoder.pkl')

# Save the best model
joblib.dump(best_model, 'best_mental_health_model.pkl')
print("Saved best_mental_health_model.pkl")
mlflow.log_artifact('best_mental_health_model.pkl')