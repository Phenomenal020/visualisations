# import necessary libraries
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

import chardet
import pycountry

#### Config options for Streamlit
# Set page config for wide mode
st.set_page_config(layout="wide")
st.title("Visualising the environmental impacts of different diet groups in the UK")

#### Data definition and loading 
# Load the data
file_path_1 = 'diet_groups/Results_21Mar2022.csv'  # normalised calorie intake
file_path_2 = 'diet_groups/Results_21MAR2022_nokcaladjust.csv' # non-normalised calorie intake

# Define the columns to read
columns_to_read = ['mc_run_id', 'grouping', 'mean_ghgs', 'mean_land', 'mean_watscar', 'mean_eut', 'mean_ghgs_ch4',
                   'mean_ghgs_n2o', 'mean_bio', 'mean_watuse', 'mean_acid', 'sex', 'diet_group', 'age_group']

# Define the environmental impacts to be used in the visualisation
environmental_impacts = [
    'mean_ghgs', 'mean_land', 'mean_watscar', 'mean_eut', 
    'mean_ghgs_ch4', 'mean_ghgs_n2o', 'mean_bio', 'mean_watuse', 'mean_acid'
]

# Define a dictionary for renaming the diet groups
rename_dict = {
    'fish': 'fish-eaters',
    'meat50': 'low meat-eaters',
    'meat100': 'high meat-eaters',
    'meat': 'medium meat-eaters',
    'vegan': 'vegans',
    'veggie': 'vegetarians'
}

# Read only the specified columns from the CSV file
data1 = pd.read_csv(file_path_1, usecols=columns_to_read)
data2 = pd.read_csv(file_path_2, usecols=columns_to_read)


####  Sidebar for filters 
st.sidebar.title("Filters")

cal_adjusted = st.sidebar.selectbox("Include calorie adjustment:", ['Yes', 'No'])

if cal_adjusted == 'Yes':
    data = data1
else:
    data = data2

# Get the unique Monte Carlo run IDs and create a selectbox in the sidebar for choosing a Monte Carlo run
mc_run_ids = data['mc_run_id'].unique()
mc_run_filter = st.sidebar.selectbox("Select Monte Carlo run:", mc_run_ids)

# Create a selectbox in the sidebar for choosing an environmental impact
env_filter = st.sidebar.selectbox("Select environmental impact (Optional):", environmental_impacts)

# Filter data based on the selected Monte Carlo run
filtered_df = data[data['mc_run_id'] == mc_run_filter]


####  Main Section 
# Layout setup: Three rows each spanning full width 

# Now extract the unique diet groups after renaming
diet_groups = filtered_df['diet_group'].unique()

# Hyperlinks to the original paper and dataset
st.markdown('A copy of the paper can be found [here](https://ora.ox.ac.uk/objects/uuid:332d8ffb-75cf-4f59-bded-bc2042de955d/files/rpn89d7401) ')
st.markdown('The original dataset can be downloaded from [here](https://ora.ox.ac.uk/objects/uuid:ca441840-db5a-48c8-9b82-1ec1d77c2e9c) ')

#### Row 1 
# First row for the main visualisation - treemap
 
if not filtered_df.empty:
    # Rename the 'diet_group' values according to the rename_dict
    filtered_df['diet_group'] = filtered_df['diet_group'].map(rename_dict)

    # Check if env_filter is a valid column name
    if env_filter in filtered_df.columns:
        # Create a treemap using Plotly Express
        fig = px.treemap(
            filtered_df,  # use the filtered dataframe
            path=["sex", "diet_group", "age_group"],  # Hierarchical levels
            values=env_filter,  # Values to aggregate and display sizes
            title=f"Environmental impact by {env_filter}" 
        )

        # Update the layout to include custom title settings and fixed size
        fig.update_layout(
            title={
                'text': f"Environmental impact by {env_filter}",
                'y': 0.93,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'family': "'Roboto', sans-serif",  # Specify font and choose 'sans-serif' as fallback
                    'size': 24,  # Increase the font size 
                    'color': "black"  # Specify the font color 
                }
            },
            autosize=False,
            width=650,  # Set an explicit width to match the heatmap
            height=800  # Set an explicit height to match the heatmap
        )

        # Display the plot in Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Selected environmental impact '{env_filter}' is not valid.")
else:
    st.write("No data available to display.")
        
st.divider()        

#### Row 2

# Second row for the secondary visualization - digital map
# esimated disaggregated_ghgs

# detect the encoding of the file
with open('diet_groups/disaggregated_ghgs.csv', 'rb') as file:
    raw_data = file.read()
    encoding = chardet.detect(raw_data)['encoding']

# Load the data with the detected encoding
map_cols_to_read = ["Country_Count", "Total GHG Emis (kg CO2 eq)"]
map_df = pd.read_csv('diet_groups/disaggregated_ghgs.csv', usecols=map_cols_to_read, encoding=encoding)

# convert country name to iso code
def get_iso_code(country):
    try:
        return pycountry.countries.lookup(country).alpha_3
    except LookupError:
        return None

# convert the country names to ISO codes
map_df['iso_code'] = map_df['Country_Count'].apply(get_iso_code)

# Create a choropleth map using Plotly Express
fig = px.choropleth(map_df, locations='iso_code',
                    color='Total GHG Emis (kg CO2 eq)',
                    hover_name='Country_Count',
                    color_continuous_scale=['cyan', 'purple', 'red'], 
                    labels={'Total GHG Emis (kg CO2 eq)': 'Total GHG Emissions'})

# Update the layout to include custom title settings and fixed size
fig.update_layout(
            title={
                'text': "FIG. 2: Estimated Total GHG Emissions (kg CO2 eq) by Country",
                'y': 0.98,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'family': "'Roboto', sans-serif",  # Specify font and choose 'sans-serif' as fallback
                    'size': 24,  # Increase the font size 
                    'color': "black"  # Specify the font color 
                }
            },
            autosize=False,
            height=800  # Set an explicit height to match the heatmap
        )

# Display the map in the Streamlit app with explicit sizing
st.plotly_chart(fig, use_container_width=True)

st.divider()

#### Row 3
# Third row for a summary visualization - heatmap

#  Determining the specific range that constitutes low, medium, and high impact levels for various environmental metrics such as greenhouse gas emissions, land use, water scarcity, and others can be complex because it depends heavily on the context and standards set by regulatory bodies or scientific studies.
if not filtered_df.empty:
    
    # Select only numeric columns, excluding 'diet_group' which is categorical
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols.remove('mc_run_id')  # Remove 'mc_run_id' from numeric columns

    # Group by 'diet_group' and calculate the mean for numeric columns only
    new_df = filtered_df.groupby('diet_group')[numeric_cols].mean().reset_index()
    new_df['diet_group'] = new_df['diet_group'].replace(rename_dict)

    # Apply a logarithmic transformation to each numeric column due to differences in scale
    new_df[numeric_cols] = np.log1p(new_df[numeric_cols])

    # Set 'diet_group' as index and transpose
    heatmap_data = new_df.set_index('diet_group').T

    # Set specific order of columns based on 'diet_group'
    column_order = ['vegans', 'vegetarians', 'fish-eaters', 'low meat-eaters', 'medium meat-eaters', 'high meat-eaters']
    heatmap_data = heatmap_data[column_order]  # Reorder columns before plotting

    # Create a custom colorscale from green to red
    custom_colorscale = [
        [0.0, 'green'],        # Low impact
        [0.1, 'lightgreen'],   # Lower-medium impact
        [0.4, 'orange'],       # Medium impact
        [0.6, 'darkorange'],   # Upper-medium impact
        [0.8, 'red'],          # High impact
        [1.0, 'darkred']       # Very high impact
    ]

    # Create a Plotly heatmap with annotations
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,  # Heatmap values
        x=heatmap_data.columns,  # Columns for the X axis
        y=heatmap_data.index,  # Rows for the Y axis
        colorscale=custom_colorscale,  # Custom colorscale
        colorbar=dict(title='Log-scaled metric value'),  # Color bar settings
        text=np.around(np.expm1(heatmap_data.values), decimals=2),  # Show original scale values as text rounded to 2 decimals
        texttemplate="%{text}",  # Template to display text
        hoverinfo='text'  # Hover will show text
    ))

    # Update layout to increase font size
    fig.update_layout(
        title={
            'text': 'FIG. 3: Environmental impact across all diet groups',
            'y': 0.93,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family="'Roboto', sans-serif", # Specify font and choose 'sans-serif' as fallback
                size=24,  # Increase the font size 
                color="black"  # Specify the font color 
            )
        },
        xaxis_title='Diet Group',
        yaxis_title='Metrics',
        xaxis=dict(tickfont=dict(size=16)),  # Increased font size for X axis
        yaxis=dict(tickfont=dict(size=16)),  # Increased font size for Y axis
        autosize=False,
        width=650,  # Set an explicit width
        height=800  # Set an explicit height
    )

    # Set font size for annotations
    fig.update_traces(textfont=dict(size=16))

    # Show the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No data available to display.")
    
#### End of the script
