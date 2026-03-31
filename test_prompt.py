def get_latest_model_path(symbol, category):
    import os
    model_dir = os.path.join(os.getcwd(), "models")
    if not os.path.exists(model_dir):
        return None

    models = [f for f in os.listdir(model_dir) if f.startswith(f"{symbol}_{category}")]
    if not models:
        return None

    latest_model = max(models, key=lambda f: os.path.getctime(os.path.join(model_dir, f)))
    return os.path.join(model_dir, latest_model)
