
def apply_filters(adf, sel_genres, checks, max_tracks):
    df = adf.copy()
    if sel_genres:
        df = df[df["genres"].apply(
            lambda g: any(genre in str(g) for genre in sel_genres)
        )]
    if max_tracks < 50:
        df = df[df["track_count"] <= max_tracks]
    if "talent"   in checks: df = df[df["is_talent"]]
    if "one_hit"  in checks: df = df[df["is_one_hit"]]
    if "no_label" in checks: df = df[~df["has_label"]]
    if "early"    in checks: df = df[df["early_career"]]
    return df