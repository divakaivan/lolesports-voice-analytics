import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

#######################
# Page configuration
st.set_page_config(
    page_title="LoL Esports Scrim Audio Analysis",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

#######################
# Load data


def load_data():
    df = pd.read_csv(
        "https://huggingface.co/datasets/divakaivan/lolesports_voice_analytics_vis_df/resolve/main/data_for_vis.csv?download=true"
    )
    df["INGESTION_TIMESTAMP"] = pd.to_datetime(df["INGESTION_TIMESTAMP"])
    return df


df = load_data()

#######################
# Sidebar
with st.sidebar:
    st.title("🎮 LoL Esports Scrim Audio Analysis")

    team = st.sidebar.selectbox("Select a team", df.TEAM.unique())
    yt_video_title = st.sidebar.selectbox(
        "Select a video", df[df.TEAM == team].YT_VIDEO_TITLE.unique()
    )

    game_id_to_num = {
        i + 1: j
        for i, j in enumerate(
            df[
                (df.TEAM == team)
                & (df.YT_VIDEO_TITLE == yt_video_title)
                & (df.GAME_ID != "-1")
            ]
            .sort_values("INGESTION_TIMESTAMP")
            .GAME_ID.unique()
        )
    }
    game_num = st.sidebar.selectbox("Select a game", game_id_to_num.keys())
    game_id = game_id_to_num[game_num]
    game_part = st.sidebar.selectbox(
        "Info for Full Game or a part (5 min segments)",
        ["Full Game"]
        + [
            i[8:14]
            for i in df[
                (df.TEAM == team)
                & (df.YT_VIDEO_TITLE == yt_video_title)
                & (df.GAME_ID == game_id)
            ].SEGMENT_TITLE.sort_values()
        ],
    )


#######################
# Helper functions
def calculate_metrics(input_df, game_id, game_part):
    game_df = input_df[input_df.GAME_ID == game_id]

    if game_part == "Full Game":
        metrics = {
            "total_words": game_df.TEXT.str.split().apply(len).sum(),
            "avg_clarity": round(game_df.AVG_GAME_CLARITY.mean(), 2),
            "avg_intensity": round(game_df.AVG_GAME_INTENSITY.mean(), 2),
        }

        other_game_metrics = {
            "total_words": input_df[
                (input_df.GAME_ID != game_id)
                & (input_df.GAME_ID != -1)
                & (df.SEGMENT_TITLE.str.contains(r"Game \d+ \(Part \d+\)", regex=True))
            ]
            .groupby("GAME_ID")
            .TEXT.apply(lambda texts: texts.str.split().apply(len).sum())
            .mean(),
            "avg_clarity": round(
                input_df[
                    (input_df.GAME_ID != game_id) & (input_df.GAME_ID != -1)
                ].AVG_GAME_CLARITY.mean(),
                2,
            ),
            "avg_intensity": round(
                input_df[
                    (input_df.GAME_ID != game_id) & (input_df.GAME_ID != -1)
                ].AVG_GAME_INTENSITY.mean(),
                2,
            ),
        }

        deltas = {
            "words_delta": int(
                metrics["total_words"] - other_game_metrics["total_words"]
            ),
            "clarity_delta": float(
                metrics["avg_clarity"] - other_game_metrics["avg_clarity"]
            ),
            "intensity_delta": float(
                metrics["avg_intensity"] - other_game_metrics["avg_intensity"]
            ),
        }

        return metrics, other_game_metrics, deltas

    else:
        segment_df = game_df[game_df.SEGMENT_TITLE.str.contains(game_part)]
        segment_metrics = {
            "total_words": segment_df.TEXT.str.split().apply(len).sum(),
            "avg_clarity": round(segment_df.GPT_CLARITY.mean(), 2),
            "avg_intensity": round(segment_df.GPT_INTENSITY.mean(), 2),
        }

        full_game_metrics = {
            "total_words": input_df[input_df.SEGMENT_TITLE.str.contains(game_part)]
            .TEXT.str.split()
            .apply(len)
            .mean(),
            "avg_clarity": round(game_df.AVG_GAME_CLARITY.mean(), 2),
            "avg_intensity": round(game_df.AVG_GAME_INTENSITY.mean(), 2),
        }

        deltas = {
            "words_delta": int(
                segment_metrics["total_words"] - full_game_metrics["total_words"]
            ),
            "clarity_delta": float(
                segment_metrics["avg_clarity"] - full_game_metrics["avg_clarity"]
            ),
            "intensity_delta": float(
                segment_metrics["avg_intensity"] - full_game_metrics["avg_intensity"]
            ),
        }

        return segment_metrics, full_game_metrics, deltas


def make_word_cloud(input_df, game_id, game_part):
    if game_part == "Full Game":
        text = input_df[df.GAME_ID == game_id].TEXT.str.cat(sep=" ")
    else:
        text = input_df[
            (df.GAME_ID == game_id) & (df.SEGMENT_TITLE.str.contains(game_part))
        ].TEXT.str.cat(sep=" ")

    wordcloud = WordCloud(background_color="white", height=500, max_words=300).generate(
        text
    )
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig


#######################
# Dashboard Main Panel
col = st.columns((1.3, 4.5, 1.7), gap="medium")

with col[0]:
    st.markdown("#### Audio Details")

    st.metric(label="Record Count", value=df.shape[0], border=True)
    st.metric(label="Sample Rate", value=df.SAMPLE_RATE.iloc[0], border=True)
    st.metric(label="Channels", value=df.CHANNELS.iloc[0], border=True)
    st.metric(
        label="Avg Duration (sec)", value=round(df.DURATION.mean(), 2), border=True
    )
    st.metric(
        label="Avg File Size (MB)",
        value=round(df.SIZE.mean() / (1024 * 1024), 2),
        border=True,
    )

with col[1]:
    st.markdown("#### Word Cloud")

    fig = make_word_cloud(df, game_id, game_part)
    st.pyplot(fig)

with col[2]:
    st.markdown("#### Communication Metrics (vs. Avg)")

    metrics, full_game_metrics, deltas = calculate_metrics(df, game_id, game_part)

    st.metric(
        label="Words Said",
        value=metrics["total_words"],
        delta=deltas["words_delta"],
        border=True,
    )
    st.metric(
        label="Avg Clarity",
        value=metrics["avg_clarity"],
        delta=round(deltas["clarity_delta"], 2),
        help="How clear was the communication on a scale of 1 (low) to 5 (high) (given by AI)",
        border=True,
    )
    st.metric(
        label="Avg Intensity",
        value=metrics["avg_intensity"],
        delta=round(deltas["intensity_delta"], 2),
        help="Intensity of the emotion on a scale of 1 (low) to 5 (high) (given by AI)",
        border=True,
    )

    st.markdown("#### AI Summary")
    st.write(
        "Select a game part"
        if game_part == "Full Game"
        else df[
            (df.GAME_ID == game_id) & (df.SEGMENT_TITLE.str.contains(game_part))
        ].GPT_SUMMARY.iloc[0]
    )
