import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import joblib

from app.services.memory_service import MemoryService
from app.db.database import save_mental_health_alert, get_recent_mental_health_alerts
from app.utils.authentication import send_admin_notification
from app.core.config import settings


class MentalHealthService:
    """Continuous mental-health risk detection for authorized users using ML model."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service or MemoryService()
        self.admin_email = settings.ADMIN_EMAIL or "admin@university.edu"
        self.recent_interactions_limit = 15
        self.alert_cooldown_hours = 24

        # Load ML model and preprocessing artifacts
        model_dir = os.path.dirname(__file__)
        try:
            self.model = joblib.load(os.path.join(model_dir, 'best_mental_health_model.pkl'))
            self.vectorizer = joblib.load(os.path.join(model_dir, 'tfidf_vectorizer.pkl'))
            self.label_encoder = joblib.load(os.path.join(model_dir, 'label_encoder.pkl'))
            self.use_ml = True
            print("ML model loaded successfully for mental health detection.")
        except FileNotFoundError:
            print("ML model files not found, falling back to rule-based detection.")
            self.use_ml = False
            self._init_rule_based_patterns()

    def _init_rule_based_patterns(self):
        """Initialize rule-based patterns for fallback."""
        self.high_risk_patterns = [
            r"\bkill myself\b",
            r"\bi want to die\b",
            r"\bend my life\b",
            r"\bno reason to live\b",
            r"\bworthless\b",
            r"\bnot worth living\b",
            r"\bcut myself\b",
            r"\bself harm\b",
            r"\bsuicid(e|al)\b",
            r"\bcan't go on\b",
            r"\bi'm done\b",
            r"\bscared of living\b",
        ]

        self.medium_risk_patterns = [
            r"\bdepress(ed|ion)?\b",
            r"\banxious\b",
            r"\banxiety\b",
            r"\bstress(ed|ful)?\b",
            r"\boverwhelm(ed|ing)?\b",
            r"\bpanic\b",
            r"\balone\b",
            r"\bisolated\b",
            r"\bhopeless\b",
            r"\bworthless\b",
            r"\bno one cares\b",
            r"\bcan'?t handle\b",
            r"\bkeep failing\b",
            r"\bnot good enough\b",
        ]

        self.support_seeking_patterns = [
            r"\bneed help\b",
            r"\bhelp me\b",
            r"\btherapy\b",
            r"\bcounselor\b",
            r"\bmental health\b",
            r"\bnot coping\b",
            r"\bneed support\b",
            r"\blike i can't\b",
        ]

    def normalize_text(self, text: str) -> str:
        return text.lower().strip()

    def score_message(self, text: str) -> Dict[str, object]:
        normalized = self.normalize_text(text)
        score = 0
        hits: List[str] = []
        high_hits: List[str] = []
        medium_hits: List[str] = []
        support_hits: List[str] = []

        for pattern in self.high_risk_patterns:
            if re.search(pattern, normalized):
                score += 10
                hits.append(pattern)
                high_hits.append(pattern)

        for pattern in self.medium_risk_patterns:
            if re.search(pattern, normalized):
                score += 4
                hits.append(pattern)
                medium_hits.append(pattern)

        for pattern in self.support_seeking_patterns:
            if re.search(pattern, normalized):
                score += 2
                hits.append(pattern)
                support_hits.append(pattern)

        return {
            "score": score,
            "hits": hits,
            "high_hits": high_hits,
            "medium_hits": medium_hits,
            "support_hits": support_hits,
        }

    def analyze_history(self, interactions: List[Dict]) -> Dict[str, object]:
        if self.use_ml:
            return self._analyze_with_ml(interactions)
        else:
            return self._analyze_with_rules(interactions)

    def _analyze_with_ml(self, interactions: List[Dict]) -> Dict[str, object]:
        """Analyze chat history using ML model."""
        # Combine recent messages into a single text for prediction
        recent_messages = []
        for interaction in interactions[-self.recent_interactions_limit:]:
            message = interaction.get("question", "")
            if message:
                recent_messages.append(message)

        if not recent_messages:
            return {"score": 0, "risk_level": "normal", "confidence": 0.0, "recent_messages": []}

        # Combine messages and preprocess
        combined_text = " ".join(recent_messages)
        cleaned_text = self._preprocess_text(combined_text)

        # Vectorize and predict
        X = self.vectorizer.transform([cleaned_text])
        probabilities = self.model.predict_proba(X)[0]
        predicted_class_idx = self.model.predict(X)[0]
        predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
        confidence = probabilities[predicted_class_idx]

        # Map to risk levels
        risk_mapping = {
            'Normal': 'normal',
            'Anxiety': 'moderate',
            'Stress': 'moderate',
            'Depression': 'high',
            'Suicidal': 'high',
            'Bipolar': 'high',
            'Personality disorder': 'high'
        }

        risk_level = risk_mapping.get(predicted_class, 'moderate')
        score = int(confidence * 100)  # Convert to 0-100 scale

        return {
            "score": score,
            "risk_level": risk_level,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "recent_messages": recent_messages,
        }

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text similar to training."""
        import re
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        import nltk

        # Download if needed
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')

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

    def _analyze_with_rules(self, interactions: List[Dict]) -> Dict[str, object]:
        """Fallback rule-based analysis."""
        total_score = 0
        high_hits: List[str] = []
        medium_hits: List[str] = []
        support_hits: List[str] = []
        recent_messages: List[str] = []

        for interaction in interactions[-self.recent_interactions_limit:]:
            message = interaction.get("question", "")
            if not message:
                continue
            recent_messages.append(message)
            result = self.score_message(message)
            total_score += result["score"]
            high_hits.extend(result["high_hits"])
            medium_hits.extend(result["medium_hits"])
            support_hits.extend(result["support_hits"])

        return {
            "score": total_score,
            "high_hits": list(set(high_hits)),
            "medium_hits": list(set(medium_hits)),
            "support_hits": list(set(support_hits)),
            "recent_messages": recent_messages,
        }

    def determine_severity(self, analysis: Dict[str, object]) -> str:
        if self.use_ml:
            return analysis.get("risk_level", "low")
        else:
            if analysis["high_hits"]:
                return "high"
            if analysis["score"] >= 18:
                return "high"
            if analysis["score"] >= 10:
                return "moderate"
            return "low"

    def should_alert(self, analysis: Dict[str, object]) -> bool:
        if self.use_ml:
            risk_level = analysis.get("risk_level", "normal")
            confidence = analysis.get("confidence", 0.0)
            return risk_level in ["high", "moderate"] and confidence > 0.7
        else:
            if analysis["high_hits"]:
                return True
            return analysis["score"] >= 12

    def has_recent_alert(self, user_id: int, db, hours: int = 24) -> bool:
        recent = get_recent_mental_health_alerts(user_id, db, hours=hours)
        return len(recent) > 0

    def evaluate_user_risk(self, user_id: str, reg_id: Optional[str], db) -> Optional[Dict[str, object]]:
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        interactions = self.memory_service.get_user_memory(str(user_id_int))
        if not interactions:
            return None

        analysis = self.analyze_history(interactions)
        if not self.should_alert(analysis):
            return None

        if self.has_recent_alert(user_id_int, db, hours=self.alert_cooldown_hours):
            return None

        latest_message = analysis["recent_messages"][-1] if analysis["recent_messages"] else ""
        severity = self.determine_severity(analysis)
        
        if self.use_ml:
            matched_phrases = f"ML Prediction: {analysis.get('predicted_class', 'Unknown')} (confidence: {analysis.get('confidence', 0.0):.2f})"
        else:
            matched_phrases = ", ".join(analysis["high_hits"] + analysis["medium_hits"] + analysis["support_hits"])

        alert = save_mental_health_alert(
            user_id=user_id_int,
            reg_id=reg_id,
            severity=severity,
            score=analysis["score"],
            matched_phrases=matched_phrases,
            question_sample=latest_message,
            db=db,
        )

        self.notify_admin(alert)
        return {
            "alert_id": alert.id,
            "user_id": alert.user_id,
            "reg_id": alert.reg_id,
            "severity": alert.severity,
            "score": alert.score,
            "matched_phrases": alert.matched_phrases,
            "question_sample": alert.question_sample,
        }

    def notify_admin(self, alert) -> None:
        subject = f"Mental health risk alert for user {alert.reg_id or alert.user_id}"
        message = (
            f"A mental-health risk signal was detected for user {alert.reg_id or alert.user_id}.\n"
            f"Severity: {alert.severity}\n"
            f"Score: {alert.score}\n"
            f"Detected phrases: {alert.matched_phrases}\n"
            f"Latest user message: {alert.question_sample}\n"
            f"Alert created at: {alert.created_at.isoformat()}\n"
        )
        send_admin_notification(self.admin_email, subject, message)
