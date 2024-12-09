import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Streamlit page configuration
st.set_page_config(
    page_title='AGP Dashboard',
    page_icon=':bar_chart:',
)

# --------------------------------------------------------------------
# Data Processing Functions
# --------------------------------------------------------------------

def load_data(file_path):
    """Load and preprocess the dataset."""
    df = pd.ExcelFile(file_path).parse('Sheet1')
    df['Χρονική σήμανση συσκευής'] = pd.to_datetime(df['Χρονική σήμανση συσκευής'])
    df.rename(columns={
        'Χρονική σήμανση συσκευής': 'Timestamp',
        'Ιστορική γλυκόζη mg/dL': 'Glucose'
    }, inplace=True)
    return df

def compute_agp_summary(data):
    """Compute AGP summary statistics."""
    target_range = (70, 180)
    low_range = (54, 69)
    very_low_range = (0, 53)
    high_range = (181, 250)
    very_high_range = (251, float('inf'))

    summary = {
        'Total Readings': len(data),
        'Time in Target Range (70-180 mg/dL) (%)': data['Glucose'].between(*target_range).mean() * 100,
        'Time Below Range (54-69 mg/dL) (%)': data['Glucose'].between(*low_range).mean() * 100,
        'Time Very Low (<54 mg/dL) (%)': data['Glucose'].between(*very_low_range).mean() * 100,
        'Time Above Range (181-250 mg/dL) (%)': data['Glucose'].between(*high_range).mean() * 100,
        'Time Very High (>250 mg/dL) (%)': data['Glucose'].between(*very_high_range).mean() * 100,
        'Mean Glucose (mg/dL)': data['Glucose'].mean(),
        'Coefficient of Variation (%CV)': (data['Glucose'].std() / data['Glucose'].mean()) * 100,
    }
    return summary

def compute_daily_profiles(data):
    """Compute daily glucose profiles."""
    data['Date'] = data['Timestamp'].dt.date
    daily_stats = data.groupby('Date')['Glucose'].agg(
        Min='min', Max='max', Mean='mean'
    ).reset_index()
    return daily_stats

def compute_agp(data):
    """Compute glucose variability statistics by time of day."""
    data['Time of Day'] = data['Timestamp'].dt.hour + data['Timestamp'].dt.minute / 60
    grouped = data.groupby('Time of Day')['Glucose']
    agp_stats = grouped.agg(
        Median='median',
        Percentile5=lambda x: np.percentile(x, 5),
        Percentile25=lambda x: np.percentile(x, 25),
        Percentile75=lambda x: np.percentile(x, 75),
        Percentile95=lambda x: np.percentile(x, 95)
    )
    return agp_stats.reset_index()

# --------------------------------------------------------------------
# Visualization Functions
# --------------------------------------------------------------------

def plot_time_in_range_stacked_vertical(summary):
    """Plot vertical stacked bar chart for Time in Range."""
    ranges = ['Very Low (<54 mg/dL)', 'Low (54-69 mg/dL)', 'Target (70-180 mg/dL)', 'High (181-250 mg/dL)', 'Very High (>250 mg/dL)']
    percentages = [
        summary['Time Very Low (<54 mg/dL) (%)'],
        summary['Time Below Range (54-69 mg/dL) (%)'],
        summary['Time in Target Range (70-180 mg/dL) (%)'],
        summary['Time Above Range (181-250 mg/dL) (%)'],
        summary['Time Very High (>250 mg/dL) (%)']
    ]
    colors = ['#ff6666', '#ffc000', '#8fd9b6', '#ffcc99', '#ff9999']

    fig, ax = plt.subplots(figsize=(6, 8))
    cumulative = np.zeros(1)
    for range_name, pct, color in zip(ranges, percentages, colors):
        ax.bar([0], [pct], bottom=cumulative, color=color, edgecolor='black', width=0.5)
        cumulative += pct

    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    ax.set_title('ΧΡΟΝΟΣ ΕΝΤΟΣ ΕΥΡΟΥΣ ΣΤΟΧΩΝ', fontsize=16, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    return fig

def plot_agp(agp_data):
    """Plot AGP graph."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(agp_data['Time of Day'], agp_data['Percentile5'], agp_data['Percentile95'], color='lightblue', alpha=0.5, label='5th-95th Percentile')
    ax.fill_between(agp_data['Time of Day'], agp_data['Percentile25'], agp_data['Percentile75'], color='blue', alpha=0.3, label='25th-75th Percentile')
    ax.plot(agp_data['Time of Day'], agp_data['Median'], color='darkblue', linewidth=2, label='Median (50th Percentile)')
    ax.axhspan(70, 180, color='green', alpha=0.1, label='Target Range (70-180 mg/dL)')
    ax.set_title('ΠΡΟΦΙΛ ΔΙΑΚΥΜΑΝΣΗΣ ΓΛΥΚΟΖΗΣ (AGP)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Time of Day (Hours)', fontsize=12)
    ax.set_ylabel('Glucose (mg/dL)', fontsize=12)
    return fig

# --------------------------------------------------------------------
# Streamlit Application
# --------------------------------------------------------------------

st.title("Ambulatory Glucose Profile (AGP) Report")

uploaded_file = st.file_uploader("Upload your AGP dataset (Excel format)", type=["xlsx"])

if uploaded_file:
    data = load_data(uploaded_file)

    # Summary
    summary = compute_agp_summary(data)
    st.header("AGP Summary")
    st.write(f"**Mean Glucose:** {summary['Mean Glucose (mg/dL)']:.1f} mg/dL")
    gmi = 3.31 + 0.02392 * summary['Mean Glucose (mg/dL)']
    st.write(f"**GMI:** {gmi:.1f}%")
    st.pyplot(plot_time_in_range_stacked_vertical(summary))

    # AGP
    agp_data = compute_agp(data)
    st.pyplot(plot_agp(agp_data))

    # Daily Profiles
    daily_profiles = compute_daily_profiles(data)
    st.header("Daily Profiles")
    st.dataframe(daily_profiles)




import duckdb

# Function to save data to DuckDB
def save_to_duckdb(df, table_name="editable_data"):
    conn = duckdb.connect("data_store.duckdb")
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER, name STRING, age INTEGER, email STRING)")
    conn.execute(f"DELETE FROM {table_name}")  # Clear the table before saving
    conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
    conn.close()

# Initial data
initial_data = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"},
]

# Load or initialize the dataframe
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(initial_data)

# Editable dataframe
st.write("### Editable DataFrame")
edited_df = st.data_editor(
    st.session_state.data,
    key="data_editor",
    use_container_width=True
)

# Display the edited dataframe
st.write("### Current Data")
st.dataframe(edited_df, use_container_width=True)

# Save the data to DuckDB
if st.button("Save to Database"):
    save_to_duckdb(edited_df)
    st.success("Data saved to DuckDB successfully!")

# Optionally: Display the saved data
if st.button("Load Data from Database"):
    conn = duckdb.connect("data_store.duckdb")
    saved_data = conn.execute("SELECT * FROM editable_data").fetchdf()
    conn.close()
    st.write("### Saved Data")
    st.dataframe(saved_data, use_container_width=True)
