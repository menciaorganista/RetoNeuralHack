def occupancy_ratio(detections, image_width, image_height):
    if image_width <= 0 or image_height <= 0:
        return 0.0

    img_area = float(image_width * image_height)
    if img_area == 0:
        return 0.0

    total_area = 0.0
    for d in detections:
        x1, y1, x2, y2 = d["bbox_xyxy"]
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        total_area += w * h

    return total_area / img_area
