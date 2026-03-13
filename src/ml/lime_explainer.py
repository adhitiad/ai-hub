# src/ml/lime_explainer.py
import lime
import lime.lime_tabular


class LIMEExplainer:
    def __init__(self, model, feature_names, class_names):
        self.model = model
        self.feature_names = feature_names
        self.class_names = class_names

        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data,  # Background data
            feature_names=feature_names,
            class_names=class_names,
            mode="classification",
        )

    def explain(self, instance, num_features=10):
        """Generate LIME explanation"""
        exp = self.explainer.explain_instance(
            instance, self.model.predict_proba, num_features=num_features
        )

        return {
            "explanation": exp.as_list(),
            "probability": exp.predict_proba,
            "feature_importance": exp.as_map(),
        }
