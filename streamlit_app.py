# -*- coding: utf-8 -*-

from datetime import date
import pandas as pd
import streamlit as st
import altair as alt
import requests

st.set_page_config(
    page_title="Capital Weather Comparison",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 수도별 날씨 비교")
st.write("Korea, USA, Italy, Germany, Switzerland, Sweden, Canada, Japan, China, Turkey의 수도 날씨를 비교합니다.")

CAPITALS = {
    "Korea - Seoul": {"lat": 37.5665, "lon": 126.9780},
    "USA - Washington D.C.": {"lat": 38.9072, "lon": -77.0369},
    "Italy - Rome": {"lat": 41.9028, "lon": 12.4964},
    "Germany - Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Switzerland - Bern": {"lat": 46.9480, "lon": 7.4474},
    "Sweden - Stockholm": {"lat": 59.3293, "lon": 18.0686},
    "Canada - Ottawa": {"lat": 45.4215, "lon": -75.6972},
    "Japan - Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "China - Beijing": {"lat": 39.9042, "lon": 116.4074},
    "Turkey - Ankara": {"lat": 39.9334, "lon": 32.8597},
}

@st.cache_data
def load_weather(city_name, lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "auto",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()["daily"]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["time"])
    df["city"] = city_name

    df = df.rename(
        columns={
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "precipitation_sum": "precipitation",
            "wind_speed_10m_max": "wind",
        }
    )

    return df[["date", "city", "temp_max", "temp_min", "precipitation", "wind"]]


st.sidebar.header("설정")

selected_cities = st.sidebar.multiselect(
    "비교할 수도 선택",
    options=list(CAPITALS.keys()),
    default=list(CAPITALS.keys()),
)

start_date = st.sidebar.date_input("시작일", date(2023, 1, 1))
end_date = st.sidebar.date_input("종료일", date(2023, 12, 31))

if start_date > end_date:
    st.error("시작일은 종료일보다 앞서야 합니다.")
    st.stop()

if not selected_cities:
    st.warning("최소 1개 이상의 수도를 선택하세요.")
    st.stop()

dfs = []

for city in selected_cities:
    info = CAPITALS[city]
    dfs.append(
        load_weather(
            city,
            info["lat"],
            info["lon"],
            str(start_date),
            str(end_date),
        )
    )

df = pd.concat(dfs, ignore_index=True)

st.subheader("요약 지표")

summary = (
    df.groupby("city")
    .agg(
        max_temp=("temp_max", "max"),
        min_temp=("temp_min", "min"),
        total_precipitation=("precipitation", "sum"),
        max_wind=("wind", "max"),
    )
    .reset_index()
)

st.dataframe(summary, use_container_width=True)

cols = st.columns(2)

with cols[0].container(border=True):
    st.markdown("### 최고 기온 비교")

    chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_max:Q", title="Max temperature (°C)"),
            color=alt.Color("city:N", title="Capital"),
            tooltip=["date:T", "city:N", "temp_max:Q"],
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

with cols[1].container(border=True):
    st.markdown("### 최저 기온 비교")

    chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_min:Q", title="Min temperature (°C)"),
            color=alt.Color("city:N", title="Capital"),
            tooltip=["date:T", "city:N", "temp_min:Q"],
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

cols = st.columns(2)

with cols[0].container(border=True):
    st.markdown("### 강수량 비교")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("month(date):O", title="Month"),
            y=alt.Y("sum(precipitation):Q", title="Total precipitation (mm)"),
            color=alt.Color("city:N", title="Capital"),
            tooltip=["city:N", "sum(precipitation):Q"],
        )
    )

    st.altair_chart(chart, use_container_width=True)

with cols[1].container(border=True):
    st.markdown("### 최대 풍속 비교")

    chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("wind:Q", title="Max wind speed (km/h)"),
            color=alt.Color("city:N", title="Capital"),
            tooltip=["date:T", "city:N", "wind:Q"],
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

st.subheader("월별 평균 기온 비교")

monthly = df.copy()
monthly["month"] = monthly["date"].dt.month

monthly_summary = (
    monthly.groupby(["city", "month"])
    .agg(
        avg_max_temp=("temp_max", "mean"),
        avg_min_temp=("temp_min", "mean"),
    )
    .reset_index()
)

chart = (
    alt.Chart(monthly_summary)
    .mark_line(point=True)
    .encode(
        x=alt.X("month:O", title="Month"),
        y=alt.Y("avg_max_temp:Q", title="Average max temperature (°C)"),
        color=alt.Color("city:N", title="Capital"),
        tooltip=["city:N", "month:O", "avg_max_temp:Q"],
    )
)

st.altair_chart(chart, use_container_width=True)

st.subheader("Raw data")
st.dataframe(df, use_container_width=True)