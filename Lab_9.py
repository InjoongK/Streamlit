import numpy as np
import pandas as pd
import zipfile
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from io import BytesIO
import streamlit as st

@st.cache_data
def load_national_data():
    names_file = 'https://www.ssa.gov/oact/babynames/names.zip'
    response = requests.get(names_file)
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        dfs = []
        files = [file for file in z.namelist() if file.endswith('.txt')]
        for file in files:
            with z.open(file) as f:
                df = pd.read_csv(f, header=None)
                df.columns = ['name', 'sex', 'count']
                df['year'] = int(file[3:7])
                dfs.append(df)
        data = pd.concat(dfs, ignore_index=True)
    return data

@st.cache_data
def load_state_data():
    names_file = 'https://www.ssa.gov/oact/babynames/state/namesbystate.zip'
    response = requests.get(names_file)
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        dfs = []
        for file in z.namelist():
            if file.endswith('.TXT'):
                with z.open(file) as f:
                    df = pd.read_csv(f, header=None)
                    df.columns = ['state', 'sex', 'year', 'name', 'count']
                    dfs.append(df)
        data = pd.concat(dfs, ignore_index=True)
    return data

# Load data with a loading spinner
with st.spinner('Loading names data...'):
    national_data = load_national_data()
    state_data = load_state_data()

# Sidebar
with st.sidebar:
    st.title('Analysis Options')
    
    data_scope = st.radio(
        "Geographic Scope",
        ["National", "State"]
    )
    
    if data_scope == "State":
        selected_states = st.multiselect(
            "Select States",
            options=sorted(state_data['state'].unique()),
            default=[]
        )
        
    analysis_type = st.radio(
        "Choose Analysis Type",
        ["Name Trends", "Top Names"]
    )
    
    st.sidebar.write("Select Gender(s)")
    gender_cols = st.columns(2)
    with gender_cols[0]:
        male_selected = st.checkbox('Male (M)', value=True)
    with gender_cols[1]:
        female_selected = st.checkbox('Female (F)', value=True)

    gender_filter = []
    if male_selected:
        gender_filter.append('M')
    if female_selected:
        gender_filter.append('F')

# Main content
st.title('Baby Names Explorer')
st.caption(f"Currently viewing: {data_scope} data")

# Tabs
tab1, tab2 = st.tabs(["Analysis", "Fun Facts & Stats"])

with tab1:
    if analysis_type == "Name Trends":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_name = st.text_input('Enter a name:', value="John")
            year_range = st.slider(
                "Year range",
                min_value=1880,
                max_value=2022,
                value=(1950, 2022)
            )
            
            if input_name: # National
                if data_scope == "National":
                    name_data = national_data[
                        (national_data['name'].str.lower() == input_name.lower()) &
                        (national_data['year'].between(*year_range))
                    ]
                else:  # State
                    name_data = state_data[
                        (state_data['name'].str.lower() == input_name.lower()) &
                        (state_data['state'].isin(selected_states)) &
                        (state_data['year'].between(*year_range))
                    ]
                
                name_data = name_data[name_data['sex'].isin(gender_filter)]
                
                if not name_data.empty:
                    if data_scope == "National":
                        fig = px.line(
                            name_data,
                            x='year',
                            y='count',
                            color='sex',
                            title=f'Popularity of "{input_name}" Over Time'
                        )
                    else:
                        fig = px.line(
                            name_data,
                            x='year',
                            y='count',
                            color='state',
                            line_dash='sex',
                            title=f'Popularity of "{input_name}" by State'
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data found for this name in the selected region(s)")
        
        with col2:
            if not name_data.empty:
                st.subheader("Name Statistics")
                
                if data_scope == "National":
                    peak_data = name_data.loc[name_data['count'].idxmax()]
                    st.metric(
                        "Peak Year",
                        int(peak_data['year']),
                        f"{peak_data['count']:,} babies"
                    )
                    
                    total_babies = name_data['count'].sum()
                    st.metric("Total Babies", f"{total_babies:,}")
                    
                    recent_year = name_data['year'].max()
                    recent_count = name_data[name_data['year'] == recent_year]['count'].sum()
                    st.metric("Most Recent Count", f"{recent_count:,}")
                else:
                    top_state = name_data.groupby('state')['count'].sum().idxmax()
                    st.metric(
                        "Most Popular in",
                        top_state,
                        f"{name_data[name_data['state'] == top_state]['count'].sum():,} babies"
                    )
    
    elif analysis_type == "Top Names":
        year_select = st.slider(
            "Select Year",
            min_value=1880,
            max_value=2022,
            value=2000
        )
        
        if data_scope == "National":
            top_data = national_data[national_data['year'] == year_select]
        else:  # State
            top_data = state_data[
                (state_data['year'] == year_select) &
                (state_data['state'].isin(selected_states))
            ]
        
        if len(gender_filter) > 0:
            cols = st.columns(len(gender_filter))
            
            for sex, col in zip(gender_filter, cols):
                with col:
                    sex_data = top_data[top_data['sex'] == sex].nlargest(10, 'count')
                    
                    color_scale = 'Teal' if sex == 'M' else 'Peach'
                    
                    fig = px.bar(
                        sex_data,
                        x='name',
                        y='count',
                        title=f'Top {sex} Names in {year_select}',
                        color='count',
                        color_continuous_scale=color_scale
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Please select at least one gender to display the top names.")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        selected_year = st.slider(
            "Select Year to Analyze",
            min_value=int(national_data['year'].min()),
            max_value=int(national_data['year'].max()),
            value=2000
        )
    
        year_data = national_data[national_data['year'] == selected_year].copy()
        
        st.info(
            "Tip: Click on the legend (e.g., 'M' or 'F' in the top-right corner) to hide or show data for specific genders."
        )
        
        if not year_data.empty:
            year_data['name_length'] = year_data['name'].str.len()
            
            fig = px.histogram(
                year_data,
                x='name_length',
                color='sex',
                barmode='group',
                title=f'Distribution of Name Lengths in {selected_year}',
                labels={'name_length': 'Name Length', 'count': 'Number of Names'},
                color_discrete_map={'M': 'dodgerblue', 'F': 'tomato'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not year_data.empty:
    
            avg_length = year_data.groupby('sex')['name_length'].mean().round(2)
            longest_names = year_data.nlargest(10, 'name_length')[['name', 'name_length', 'sex']].rename(
                columns={
                    'name': 'Name',
                    'name_length': 'Name Length',
                    'sex': 'Sex'
                }
            )
            
            if 'F' in avg_length:
                st.metric("Average Length (Female Names)", f"{avg_length['F']} letters")
            if 'M' in avg_length:
                st.metric("Average Length (Male Names)", f"{avg_length['M']} letters")
            
            st.markdown("### Longest Names This Year")
            st.dataframe(longest_names)
        else:
            st.warning("Please select at least one gender to display statistics.")

# Footer
st.markdown("---")
st.caption("Data source: U.S. Social Security Administration")