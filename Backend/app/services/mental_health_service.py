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
        self._init_rule_based_patterns()

        # Load ML model and preprocessing artifacts
        model_dir = os.path.dirname(__file__)
        try:
            self.model = joblib.load(os.path.join(model_dir, 'best_mental_health_model.pkl'))
            self.vectorizer = joblib.load(os.path.join(model_dir, 'tfidf_vectorizer.pkl'))
            self._repair_vectorizer_compatibility()
            self.label_encoder = joblib.load(os.path.join(model_dir, 'label_encoder.pkl'))
            self.use_ml = True
            print("ML model loaded successfully for mental health detection.")
        except FileNotFoundError:
            print("ML model files not found, falling back to rule-based detection.")
            self.use_ml = False

    def _repair_vectorizer_compatibility(self) -> None:
        """Restore TF-IDF internals when loading newer sklearn pickles."""
        tfidf = getattr(self.vectorizer, "_tfidf", None)
        if not tfidf or hasattr(tfidf, "_idf_diag"):
            return

        idf = getattr(tfidf, "__dict__", {}).get("idf_")
        if idf is not None:
            self.vectorizer.idf_ = idf

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
            r"\bi can't continue\b",
            r"\bi cannot continue\b",
            r"\bi should quit\b",
            r"\bwant to quit\b",
            r"\bno,? ami sekhane jete chai na\b",
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
            r"\bfeeling low\b",
            r"\bfeel low\b",
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
        rule_analysis = self._analyze_with_rules(interactions)

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
            "rule_score": rule_analysis["score"],
            "high_hits": rule_analysis["high_hits"],
            "medium_hits": rule_analysis["medium_hits"],
            "support_hits": rule_analysis["support_hits"],
        }

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text similar to training."""
        import re

        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        words = text.split()

        try:
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer

            stop_words = set(stopwords.words('english'))
            lemmatizer = WordNetLemmatizer()
            words = [
                lemmatizer.lemmatize(word)
                for word in words
                if word not in stop_words
            ]
        except Exception:
            fallback_stop_words = {
                "a", "an", "and", "are", "as", "at", "be", "but", "by",
                "for", "from", "has", "have", "i", "in", "is", "it",
                "of", "on", "or", "that", "the", "to", "was", "were",
                "with", "you", "your",
            }
            words = [word for word in words if word not in fallback_stop_words]

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
            predicted_class = analysis.get("predicted_class", "")
            confidence = float(analysis.get("confidence", 0.0) or 0.0)
            risk_level = analysis.get("risk_level", "low")

            if analysis.get("high_hits"):
                return "critical"
            if int(analysis.get("rule_score", 0) or 0) >= 18:
                return "high"
            if predicted_class == "Suicidal" and confidence >= 0.7:
                return "critical"
            if risk_level == "high" and confidence >= 0.9:
                return "critical"
            if risk_level in ["high", "moderate", "low"]:
                return risk_level
            return "low"
        else:
            if analysis["high_hits"]:
                return "critical"
            if analysis["score"] >= 18:
                return "high"
            if analysis["score"] >= 10:
                return "moderate"
            return "low"

    def should_alert(self, analysis: Dict[str, object]) -> bool:
        if self.use_ml:
            if analysis.get("high_hits"):
                return True
            if int(analysis.get("rule_score", 0) or 0) >= 12:
                return True
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
            rule_hits = analysis.get("high_hits", []) + analysis.get("medium_hits", []) + analysis.get("support_hits", [])
            matched_phrases = f"ML Prediction: {analysis.get('predicted_class', 'Unknown')} (confidence: {analysis.get('confidence', 0.0):.2f})"
            if rule_hits:
                matched_phrases = f"{matched_phrases}; Rule hits: {', '.join(rule_hits)}"
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
            predicted_class=analysis.get("predicted_class") if self.use_ml else None,
            confidence=float(analysis.get("confidence", 0.0) or 0.0) if self.use_ml else None,
        )

        self.notify_admin(alert)
        return {
            "alert_id": alert.id,
            "user_id": alert.user_id,
            "reg_id": alert.reg_id,
            "severity": alert.severity,
            "score": alert.score,
            "predicted_class": alert.predicted_class,
            "confidence": alert.confidence,
            "matched_phrases": alert.matched_phrases,
            "question_sample": alert.question_sample,
            "status": alert.status,
        }

    def notify_admin(self, alert) -> None:
        subject = f"Mental health risk alert for user {alert.reg_id or alert.user_id}"
        message = (
            f"A mental-health risk signal was detected for user {alert.reg_id or alert.user_id}.\n"
            f"Severity: {alert.severity}\n"
            f"Score: {alert.score}\n"
            f"Predicted class: {alert.predicted_class or 'N/A'}\n"
            f"Confidence: {alert.confidence if alert.confidence is not None else 'N/A'}\n"
            f"Detected phrases: {alert.matched_phrases}\n"
            f"Latest user message: {alert.question_sample}\n"
            f"Alert created at: {alert.created_at.isoformat()}\n"
        )
        send_admin_notification(self.admin_email, subject, message)
