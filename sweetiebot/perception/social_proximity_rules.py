def allowed_speed_for_distance(distance_m: float) -> float:
    if distance_m < 1.0:
        return 0.15
    if distance_m < 2.0:
        return 0.30
    return 0.50
