import pandas as pd

tracks = pd.read_csv(
    "data/tracks.csv",
    header=[0, 1],
    index_col=0
)

# Initial cleaning and numeric conversions
tracks.columns = ['_'.join(col) for col in tracks.columns.values]
tracks["year"] = pd.to_datetime(tracks["album_date_released"], errors="coerce").dt.year
tracks["track_listens"] = pd.to_numeric(tracks["track_listens"],   errors="coerce")
tracks["estimated_revenue"]  = tracks["track_listens"] * 0.004


def build_artist_df(track_df):
    """
    Function takes the track dataframe and aggregates based on artist.
    :param track_df: dataframe with the tracks
    :returns: aggregated datagrame.
    """
    grp = track_df.groupby("artist_name")

    agg = pd.DataFrame({
        "track_count":     grp["track_listens"].count(),
        "avg_listens":     grp["track_listens"].mean(),
        "max_listens":     grp["track_listens"].max(),
        "career_start":    grp["year"].min(),
        "genres":          grp["track_genre_top"].agg(lambda x: ", ".join(x.dropna().unique())),
        "total_missing":   grp.apply(lambda x: x.isna().sum().sum()),
        "total_fields":    grp.apply(lambda x: x.shape[0] * x.shape[1]),
        "total_revenue":   grp["estimated_revenue"].sum(),
        "avg_revenue":     grp["estimated_revenue"].mean(),
    }).reset_index()

    # one-hit wonder ratio
    agg["ratio"] = agg["max_listens"] / (agg["avg_listens"] + 1) # I don't understand why it is done this specific way. We never discussed this, I have NEVER said this needed to be here. This is why I don't want you to use Claude! -Xander

    # missing data percentage per artist (underground signal)
    agg["missing_pct"] = (agg["total_missing"] / agg["total_fields"] * 100).round(1) # Again, we did not discuss this. This pisses me off ! -Xander

    # avg_listens top 20% threshold
    p80 = agg["avg_listens"].quantile(0.80) # You did not tell about the fact it uses top 20% nor is it in the report. -Xander
    agg["top_20pct_listens"] = agg["avg_listens"] >= p80

    # Checks whether the artist has started their career in the last 5 years.
    max_year = agg["career_start"].max()
    agg["early_career"] = agg["career_start"] >= (max_year - 5)

    # label status
    label_col = "artist_associated_labels"
    if label_col in track_df.columns:
        label_map = track_df.groupby("artist_name")[label_col].first()
        agg["has_label"] = agg["artist_name"].map(label_map).notna()
        agg["has_label"] = (
            agg["has_label"] &
            agg["artist_name"].map(label_map).fillna("").astype(str).str.strip().ne("")
        )
    else:
        agg["has_label"] = False

    # talent flag: early career + few tracks + top 20% listens + no label
    agg["is_talent"] = (
        agg["early_career"] &
        (agg["track_count"] < 10) &
        agg["top_20pct_listens"] &
        ~agg["has_label"]
    )

    # one-hit wonder flag
    agg["is_one_hit"] = (agg["ratio"] > 5) & (agg["track_count"] > 1)

    return agg

artists_df = build_artist_df(tracks)

# Saving the files to .csv
artists_df.to_csv("data/artists_clean.csv")
tracks.to_csv("data/tracks_clean.csv")
