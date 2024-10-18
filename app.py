import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Google Sheets API setup
API_KEY = st.secrets['google']["API_KEY"]  # Replace with your API key
SPREADSHEET_ID = st.secrets['google']["SPREADSHEET_ID"]  # Replace with your spreadsheet ID

def get_sheet_names(api_key, spreadsheet_id):
    """Fetch all sheet names from the Google Spreadsheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")

    sheets = response.json().get("sheets", [])
    return [sheet["properties"]["title"] for sheet in sheets]

def get_sheet_data(api_key, spreadsheet_id, sheet_name):
    """Fetch data from a specific sheet."""
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}"
        f"?key={api_key}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")

    data = response.json().get("values", [])
    if not data:
        return pd.DataFrame()  # Return empty DataFrame if no data

    # Normalize data to match the header length
    max_cols = len(data[0])
    normalized_data = [row + [''] * (max_cols - len(row)) for row in data]
    return pd.DataFrame(normalized_data[1:], columns=normalized_data[0])

def mapping_team(df, team, sheet_name):
    """Map team names with their group codes."""
    config = {
        "N- กลุ่ม A": "a_n-",
        "N- กลุ่ม B": "b_n-",
        "N กลุ่ม A": "a_n",
        "N กลุ่ม B": "b_n"
    }
    
    # Check if sheet_name exists in the config
    group_code = config.get(sheet_name)
    df['group_code'] = group_code
    
    # Correct the column names for merging
    _a = pd.merge(df[['team_a', 'group_code']], team, left_on=["group_code", "team_a"], right_on=["group_code", "team"], how="left")
    _b = pd.merge(df[['team_b', 'group_code']], team, left_on=["group_code", "team_b"], right_on=["group_code", "team"], how="left")

    df['name_a'] = _a['name']
    df['name_b'] = _b['name']
    return df


def visualize(df):
    """Visualize the data."""
    df['score_a_1'] = df['score_1'].str.split('-').str[0]
    df['score_b_1'] = df['score_1'].str.split('-').str[1]
    df['score_a_2'] = df['score_2'].str.split('-').str[0]
    df['score_b_2'] = df['score_2'].str.split('-').str[1]
    df['point_a'] = df['point'].str.split('-').str[0]
    df['point_b'] = df['point'].str.split('-').str[1]
    df = df.replace("", 0)

    # astype
    df = df.astype({
        'point_a': float,
        'point_b': float,
        'score_a_1': float,
        'score_b_1': float,
        'score_a_2': float,
        'score_b_2': float,
    })

    df['gd_a'] = (df['score_a_1'] + df['score_a_2']) - (df['score_b_1'] + df['score_b_2'])
    df['gd_b'] = (df['score_b_1'] + df['score_b_2']) - (df['score_a_1'] + df['score_a_2'])

    gd_a = df.groupby(['name_a']).agg({
        'gd_a': 'sum'
    })
    gd_a['team'] = gd_a.index

    gd_b = df.groupby(['name_b']).agg({
        'gd_b': 'sum'
    })
    gd_b['team'] = gd_b.index

    df_gd = pd.merge(gd_a, gd_b, how='outer').fillna(0)
    df_gd['gd'] = df_gd['gd_a']+df_gd['gd_b']

    point_a = df.groupby(['name_a']).agg({
        'point_a': 'sum'
    })
    point_a['team'] = point_a.index
    point_b = df.groupby(['name_b']).agg({
        'point_b': 'sum'
    })
    point_b['team'] = point_b.index
    df_point = pd.merge(point_a, point_b, how='outer').fillna(0)
    df_point['point'] = df_point['point_a']+df_point['point_b']

    score = pd.merge(df_point[['team', 'point']], df_gd[['team','gd']], on='team')
    score = score.sort_values(by='point', ascending=False)
    score['rank'] = range(1, len(score)+1)
    
    columns = {
        'rank': 'อันดับ',
        'team': 'ทีม',
        'point': 'เกม',
        'gd': 'คะแนน'
    }
    score = score.rename(columns=columns)

    st.markdown('###### ตารางคะแนน')
    st.dataframe(score[columns.values()], use_container_width=True, hide_index=True)
    # plot data
    fig = px.bar(score, x='อันดับ', y='คะแนน', color='ทีม', title='ผลการแข่งขัน')
    st.plotly_chart(fig)


def display_table(df):
    """Display the data in a table."""
    columns = {
        'match': 'ลำดับที่',
        'court': 'สนาม',
        'name_a': 'Team A',
        'name_b': 'Team B',
        'point': 'คะแนน',
        'score_1': 'เกมที่ 1',
        'score_2': 'เกมที่ 2'
    }
    df = df.rename(columns=columns)

    st.dataframe(df[columns.values()], use_container_width=True, hide_index=True)


def display_knownout_table(df):
    """Display the data in a table."""
    columns = {
        'match': 'ลำดับที่',
        'court': 'สนาม',
        'team_a': 'Team A',
        'team_b': 'Team B',
        'point': 'คะแนน',
        'score_1': 'เกมที่ 1',
        'score_2': 'เกมที่ 2',
        'score_3': 'เกมที่ 3',
    }
    df = df.rename(columns=columns)

    st.dataframe(df[columns.values()], use_container_width=True, hide_index=True)
    st.image(image='knockedout.png', use_column_width=True)


# App title
st.title("Badminton for Everyday life")

try:
    # Fetch all sheet names
    sheet_names = get_sheet_names(API_KEY, SPREADSHEET_ID)[1:]

    # Create a tab for each sheet
    tabs = st.tabs(sheet_names)
    
    # Fetch team data from the "team" sheet
    team = get_sheet_data(API_KEY, SPREADSHEET_ID, "team")

    for i, sheet_name in enumerate(sheet_names):
        with tabs[i]:
            st.header(f"🏸 ตารางการแข่งขัน {sheet_name}")
            try:
                df = get_sheet_data(API_KEY, SPREADSHEET_ID, sheet_name)
                
                if sheet_name.startswith("Knockout"):
                    display_knownout_table(df)
                else:
                    df = mapping_team(df, team, sheet_name)
                    display_table(df)
                    visualize(df)
            except Exception as e:
                st.error(f"Error fetching data from '{sheet_name}': {e}")

except Exception as e:
    st.error(f"Error fetching sheet names: {e}")