import os


def _load_events(file_path):
    import json

    with open(file_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    return events


def test_predict_human():
    from rabbit.predictor import predict_user_type

    events_file = os.path.join(
        os.path.dirname(__file__), "..", "data", "events_human.json"
    )
    user_events = _load_events(events_file)

    username = "test"
    user_type, confidence = predict_user_type(username, user_events)
    assert user_type == "Human"
    assert 0.0 <= confidence <= 1.0
