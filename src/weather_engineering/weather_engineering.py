import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry


def find_precip(latitude, longitude, start_date, end_date, throw_in, perspective):
    if perspective == 'forecast':
        expiry = 3600
    else:
        expiry = -1
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=expiry)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    if perspective == 'forecast':
        url = "https://api.open-meteo.com/v1/forecast"
    else:
        url = f'https://archive-api.open-meteo.com/v1/archive'
    params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": "precipitation",
    }

    # rain is the precipitation rate in mm/h, for previous hour, so we should probably use KO +1 hour.
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_precipitation = hourly.Variables(0).ValuesAsNumpy()

    # Construct the DataFrame
    hourly_data = {
        "datetime": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "precipitation": hourly_precipitation,
    }

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    hourly_dataframe = hourly_dataframe[hourly_dataframe['datetime'] <= throw_in]
    total_precip = hourly_dataframe['precipitation'].sum()
    return total_precip


def find_weather(latitude, longitude, start_date, end_date, perspective):
    if perspective == 'forecast':
        expiry = 3600
    else:
        expiry = -1
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=expiry)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    if perspective == 'forecast':
        url = "https://api.open-meteo.com/v1/forecast"
    else:
        url = f'https://archive-api.open-meteo.com/v1/archive'
    params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": "temperature_2m,relative_humidity_2m,pressure_msl,precipitation,wind_speed_10m,wind_direction_10m,wind_gusts_10m,rain",
    }

    # rain is the precipitation rate in mm/h, for previous hour, so we should probably use KO +1 hour.
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_humidity = hourly.Variables(1).ValuesAsNumpy()
    hourly_pressure = hourly.Variables(2).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_direction = hourly.Variables(5).ValuesAsNumpy()
    hourly_wind_gusts = hourly.Variables(6).ValuesAsNumpy()
    hourly_rain = hourly.Variables(7).ValuesAsNumpy()

    # Construct the DataFrame
    hourly_data = {
        "datetime": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature": hourly_temperature_2m,
        "rain": hourly_rain,
        "wind_speed": hourly_wind_speed,
        "wind_direction": hourly_wind_direction,
        "wind_gusts": hourly_wind_gusts,
        "humidity": hourly_humidity,
        "pressure": hourly_pressure,
        "precipitation": hourly_precipitation,
    }

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    return hourly_dataframe


def weather_engineering(df, perspective):
    """
    Merges weather data with event data for each unique date in event_shots DataFrame.

    Args:
        df (DataFrame): The DataFrame containing event data.
        perspective (str): The perspective of the weather data to be retrieved. Can be 'archive' or 'forecast'.

    Returns:
        DataFrame: The resulting DataFrame with shots data merged with weather data.
    """

    df = df.dropna(subset=['latitude', 'longitude'])
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df['date'] = df['datetime'].dt.date
    df.sort_values(by='datetime', inplace=True)

    final_merged_data = pd.DataFrame()

    for index, row in df.iterrows():
        latitude = row['latitude']
        longitude = row['longitude']
        date = row['date']
        game_id = row['game_id']
        throw_in = row['datetime']

        weather_df = find_weather(latitude, longitude, date, date, perspective)

        # Calculate total precipitation for different periods
        total_precip_48h = find_precip(latitude, longitude, date - pd.Timedelta(days=2), date, throw_in, perspective)
        total_precip_72h = find_precip(latitude, longitude, date - pd.Timedelta(days=3), date, throw_in, perspective)
        total_precip_weekly = find_precip(latitude, longitude, date - pd.Timedelta(days=7), date, throw_in, perspective)

        if weather_df is not None:
            weather_df['game_id'] = game_id

            weather_df = weather_df.assign(precip_accum_48h=total_precip_48h,
                                           precip_accum_72h=total_precip_72h,
                                           precip_accum_weekly=total_precip_weekly)

            # Get the nearest weather data row for the current game based on datetime
            nearest_weather_row = weather_df.iloc[(weather_df['datetime'] - row['datetime']).abs().argsort()[:1]]
            merged_row = pd.merge(row.to_frame().T, nearest_weather_row.drop(columns=['datetime']), left_on='game_id',
                                  right_on='game_id', how='left')
            final_merged_data = pd.concat([final_merged_data, merged_row], ignore_index=True)

    return final_merged_data
