import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load data (approximations based on IPCC AR6 projections)
def load_ipcc_data():
    years = range(2000, 2101)
    scenarios = {
        'SSP5-8.5': [0.0] + [0.2 + 0.04*i for i in range(101)],  # High emissions
        'SSP2-4.5': [0.0] + [0.2 + 0.025*i for i in range(101)],  # Intermediate
        'SSP1-2.6': [0.0] + [0.2 + 0.015*i - 0.00005*i**2 for i in range(101)],  # Low emissions
        'SSP1-1.9': [0.0] + [0.2 + 0.01*i - 0.00007*i**2 for i in range(101)]  # Very low emissions
    }
    return pd.DataFrame(scenarios, index=years)

ipcc_data = load_ipcc_data()

def plot_scenarios(data, selected_scenarios):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = {
        'SSP5-8.5': '#d62728',  # Red
        'SSP2-4.5': '#ff7f0e',  # Orange
        'SSP1-2.6': '#2ca02c',  # Green
        'SSP1-1.9': '#1f77b4'   # Blue
    }
    
    for scenario in selected_scenarios:
        ax.plot(data.index, data[scenario], label=scenario, color=colors[scenario], linewidth=2)
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Global Surface Temperature Change (°C)\nrelative to 1850-1900')
    ax.set_title('IPCC AR6 Climate Change Scenarios')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 6)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    st.pyplot(fig)

def calculate_market_sizes(data, selected_scenarios, co2_price):
    market_sizes = {}
    baseline = data['SSP5-8.5']  # Use the highest emission scenario as baseline
    for scenario in selected_scenarios:
        if scenario != 'SSP5-8.5':
            difference = baseline - data[scenario]
            market_size = np.trapz(difference, dx=1) * co2_price * 1e9
            market_sizes[scenario] = market_size
    return market_sizes

st.title("IPCC Climate Change Scenarios")

st.write("""
This tool visualizes climate change scenarios based on data from the IPCC's Sixth Assessment Report (AR6).
Select different scenarios to compare projected global temperature changes.
""")

st.warning("""
**Note**: This tool uses approximate data based on IPCC AR6 projections. For the most accurate and up-to-date information, 
please refer to the full IPCC reports and data portals.
""")

selected_scenarios = st.multiselect(
    "Select scenarios to display",
    options=ipcc_data.columns.tolist(),
    default=['SSP5-8.5', 'SSP1-2.6']
)

co2_price = st.number_input("CO2 price per ton ($)", min_value=0, max_value=1000, value=50, step=10)

if selected_scenarios:
    plot_scenarios(ipcc_data, selected_scenarios)
    
    market_sizes = calculate_market_sizes(ipcc_data, selected_scenarios, co2_price)
    if market_sizes:
        st.markdown("### Estimated Market Sizes")
        for scenario, size in market_sizes.items():
            st.write(f"- {scenario}: ${size/1e9:.2f} billion")
        st.write("*Note: These are rough estimates based on the area between the curves and the CO2 price.*")

st.markdown("""
### Scenario Descriptions:
- **SSP5-8.5**: High emissions scenario - fossil-fuel development
- **SSP2-4.5**: Intermediate emissions scenario
- **SSP1-2.6**: Low emissions scenario - sustainable development
- **SSP1-1.9**: Very low emissions scenario - sustainable development with additional effort

These scenarios are based on Shared Socioeconomic Pathways (SSPs) used in the IPCC AR6 report.
The numbers (e.g., 8.5, 4.5) represent the estimated radiative forcing (W/m²) in 2100.

For more detailed information, please refer to the [IPCC AR6 Report](https://www.ipcc.ch/report/ar6/wg1/).
""")