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

    df = df.replace("", 0)

    # astype
    df = df.astype({
        'score_a_1': float,
        'score_b_1': float,
        'score_a_2': float,
        'score_b_2': float,
    })
    # group by each team and calculate the total score
    total_a = df.groupby(['name_a']).agg({
        'score_a_1': 'sum',
        'score_a_2': 'sum'
    })
    total_a['total'] = total_a['score_a_1'] + total_a['score_a_2']

    total_b = df.groupby(['name_b']).agg({
        'score_b_1': 'sum',
        'score_b_2': 'sum'
    })
    total_b['total'] = total_b['score_b_1'] + total_b['score_b_2']

    total = pd.concat([total_a, total_b])
    total['name'] = total.index

    total = total.groupby('name').agg({
        'total': 'sum'
    })
    total = total.sort_values(by='total', ascending=False)

    # Create a bar chart with customized aesthetics
    fig = px.bar(
        total,
        x=total.index,
        y='total',
        color='total',
        color_continuous_scale=px.colors.sequential.Viridis,  # Use a nice color scale
        text='total',  # Show total scores on top of the bars
    )

    # Update layout for better visuals
    fig.update_layout(
        title='Total Scores by Team',  # Add a title
        xaxis_title='Teams',  # Label x-axis
        yaxis_title='Total Score',  # Label y-axis
        showlegend=False,  # Hide legend as it is not necessary
        template='plotly_white',  # Use a clean template
    )

    # Update the text position and font
    fig.update_traces(textposition='outside', textfont_size=12)

    # Display the chart in Streamlit
    st.plotly_chart(fig)

def display_table(df):
    """Display the data in a table."""
    rename = {
        'match': 'ลำดับที่',
        'name_a': 'Team A',
        'name_b': 'Team B',
        'score_1': 'เกมที่ 1',
        'score_2': 'เกมที่ 2'
    }
    df = df.rename(columns=rename)

    st.dataframe(df[rename.values()], use_container_width=True, hide_index=True)

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
            st.header(f"{sheet_name}")
            try:
                df = get_sheet_data(API_KEY, SPREADSHEET_ID, sheet_name)
                df = mapping_team(df, team, sheet_name)

                display_table(df)
                visualize(df)
            except Exception as e:
                st.error(f"Error fetching data from '{sheet_name}': {e}")

except Exception as e:
    st.error(f"Error fetching sheet names: {e}")