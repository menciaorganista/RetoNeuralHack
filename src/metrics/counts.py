from collections import Counter

def count_by_class(detections: list[dict]) -> dict:
    class_ids = [d["class_id"] for d in detections]
    return dict(Counter(class_ids))
