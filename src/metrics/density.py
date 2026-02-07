def density_per_megapixel(num_detections, image_width, image_height):
    mp = (image_width * image_height) / 1_000_000.0
    if mp <= 0:
        return 0.0
    return num_detections / mp
