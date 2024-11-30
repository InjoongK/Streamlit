import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="MLB Power Hitting Analysis",
    page_icon="⚾",
    layout="wide"
)

# Function to load data
@st.cache_data
def load_data():
    url = 'https://raw.githubusercontent.com/InjoongK/injoong-blog/refs/heads/main/_posts/baseball%20data.csv'
    df = pd.read_csv(url)
    #df = pd.read_csv('C:/Users/rladl/Documents/another-stat386-theme/_posts/baseball data.csv')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df[df['Team'] != '2TM']
    return df

# Load data
try:
    df = load_data()
except:
    st.error("Please ensure your data file is in the correct location")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("MLB Power Hitting Analysis")
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a6/Major_League_Baseball_logo.svg", width=280)
    
    analysis_type = st.radio(
        "Select Analysis Type",
        ["Power Metrics Overview", "Team Analysis", "Custom Analysis"]
    )
    
    if analysis_type == "Power Metrics Overview":
        st.write("### Number of players to display")
        top_n = st.number_input(
            "Enter the number of players to display:",
            min_value=1,
            max_value=len(df),
            value=10,
            step=1,
            help="Enter a number between 1 and the total number of players."
        )
    
    st.markdown("---")
    st.markdown("Data source: baseball-reference.com")

# Main content
if analysis_type == "Power Metrics Overview":
    st.title("Power Hitting Metrics Overview")

    tab1, tab2, tab3 = st.tabs(["HR/AB Rankings", "ISO Rankings", "Correlation Analysis"])
    
    with tab1:
        st.subheader(f"Top {top_n} Players by Home Runs per At Bat")
        hr_ab_fig = px.bar(
            df.nlargest(top_n, 'Home Runs per At Bat'),
            x='Player Name',
            y='Home Runs per At Bat',
            color='Home Runs per At Bat',
            title=f"Top {top_n} Players by HR/AB"
        )
        st.plotly_chart(hr_ab_fig, use_container_width=True)
        
        search_query_hr_ab = st.text_input("Search for a player:", key="player_search_hr_ab", placeholder="Start typing a player's name...")
        
        if search_query_hr_ab:
            matched_players = df[df['Player Name'].str.contains(search_query_hr_ab, case=False, na=False)]

            if not matched_players.empty:
                player_name = st.selectbox("Select a specific player:", matched_players['Player Name'].tolist())

                player_info = matched_players[matched_players['Player Name'] == player_name]
                if not player_info.empty:
                    with st.expander(f"Player Info: {player_name}"):
                        st.write(player_info)
            else:
                st.warning("No players matched your search. Try another query.")
        else:
            st.info("Start typing to search for a specific player.")
    
    with tab2:
        st.subheader(f"Top {top_n} Players by Isolated Power")
        iso_fig = px.bar(
            df.nlargest(top_n, 'Isolated Power'),
            x='Player Name',
            y='Isolated Power',
            color='Isolated Power',
            title=f"Top {top_n} Players by ISO"
        )
        st.plotly_chart(iso_fig, use_container_width=True)
        
        search_query_iso = st.text_input("Search for a specific player:", key="player_search_iso", placeholder="Start typing a player's name...")

        if search_query_iso:
            matched_players = df[df['Player Name'].str.contains(search_query_iso, case=False, na=False)]

            if not matched_players.empty:
                player_name = st.selectbox("Select a player:", matched_players['Player Name'].tolist())

                player_info = matched_players[matched_players['Player Name'] == player_name]
                if not player_info.empty:
                    with st.expander(f"Player Info: {player_name}"):
                        st.write(player_info)
            else:
                st.warning("No players matched your search. Try another query.")
        else:
            st.info("Start typing to search for specific a player.")

    with tab3:
        st.subheader("Correlation between HR/AB and ISO")
        scatter_fig = px.scatter(
            df,
            x='Home Runs per At Bat',
            y='Isolated Power',
            hover_data=['Player Name'],
            trendline="ols",
            title="HR/AB vs ISO Correlation"
        )
        st.plotly_chart(scatter_fig, use_container_width=True)


elif analysis_type == "Team Analysis":
    st.title("Team Power Analysis")
    
    team_metric = st.selectbox(
        "Select Team Metric",
        ["Average HR/AB", "Average ISO", "Total Home Runs"]
    )
    
    if team_metric == "Average HR/AB":
        team_stats = df.groupby('Team')['Home Runs per At Bat'].mean().reset_index()
        y_col = 'Home Runs per At Bat'
    elif team_metric == "Average ISO":
        team_stats = df.groupby('Team')['Isolated Power'].mean().reset_index()
        y_col = 'Isolated Power'
    else:
        team_stats = df.groupby('Team')['Home Runs'].sum().reset_index()
        y_col = 'Home Runs'
    
    team_fig = px.bar(
        team_stats.sort_values(y_col, ascending=False),
        x='Team',
        y=y_col,
        title=f"Team {team_metric}"
    )
    st.plotly_chart(team_fig, use_container_width=True)

elif analysis_type == "Custom Analysis":
    st.title("Custom Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox(
            "Select X-axis metric",
            ['Home Runs', 'Home Runs per At Bat', 'Isolated Power', 'Slugging Percentage', 'Batting Average', 'Age']
        )
    with col2:
        y_axis = st.selectbox(
            "Select Y-axis metric",
            ['Home Runs', 'Home Runs per At Bat', 'Isolated Power', 'Slugging Percentage', 'Batting Average', 'Age'],
            index=1
        )
    
    custom_fig = px.scatter(
        df,
        x=x_axis,
        y=y_axis,
        hover_data=['Player Name'],
        trendline="ols",
        title=f"{x_axis} vs {y_axis} Analysis"
    )
    st.plotly_chart(custom_fig, use_container_width=True)

st.markdown("""---""")
st.markdown("""
    💡 **Metric Definitions:**
    - **HR/AB**: Home Runs per At Bat - measures home run efficiency
    - **ISO**: Isolated Power - represents a player’s pure slugging power by focusing on extra-base hits (doubles, triples, and home runs).
    - **SLG**: Slugging Percentage - an expected figure of how many bases a batter can get on base after hitting
    - **BA**: Batting Average - determined by dividing a player's hits by their total at-bats
""")
