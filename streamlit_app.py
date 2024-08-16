import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Approximations based on IPCC AR6 projections
def load_ipcc_data():
    years = range(2000, 2101)  # This creates 101 years (2000 to 2100 inclusive)
    scenarios = {
        'SSP5-8.5': [0.2 + 0.04*i for i in range(101)],  # High emissions
        'SSP2-4.5': [0.2 + 0.025*i for i in range(101)],  # Intermediate
        'SSP1-2.6': [0.2 + 0.015*i - 0.00005*i**2 for i in range(101)],  # Low emissions
        'SSP1-1.9': [0.2 + 0.01*i - 0.00007*i**2 for i in range(101)]  # Very low emissions
    }
    return pd.DataFrame(scenarios, index=years)

ipcc_data = load_ipcc_data()

def generate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration):
    years = range(2000, 2101)
    bau = ipcc_data['SSP5-8.5']
    cut_emissions = ipcc_data['SSP2-4.5']
    emissions_removal = ipcc_data['SSP1-2.6']
    climate_interventions = ipcc_data['SSP1-1.9'].copy()

    # Adjust scenarios based on user inputs
    cut_emissions *= (1 - co2_price / 1000)  # Higher CO2 price reduces temperature
    emissions_removal *= (1 - years_to_reduce / 200)  # Faster reduction lowers temperature

    # Apply intervention effect
    intervention_start = 2000 + int(intervention_temp * 20)  # Rough conversion from temperature to year
    intervention_end = min(2100, intervention_start + intervention_duration)
    intervention_effect = np.linspace(0, 1, intervention_end - intervention_start)
    climate_interventions[intervention_start-2000:intervention_end-2000] -= intervention_effect * (climate_interventions[intervention_start-2000:intervention_end-2000] - 1)

    return years, bau, cut_emissions, emissions_removal, climate_interventions

def plot_scenarios(scenarios):
    years, bau, cut_emissions, emissions_removal, climate_interventions = scenarios
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(years, bau, label='Business as Usual (SSP5-8.5)', color='red')
    ax.plot(years, cut_emissions, label='Cut Emissions Aggressively (SSP2-4.5)', color='orange')
    ax.plot(years, emissions_removal, label='Emissions Removal (SSP1-2.6)', color='green')
    ax.plot(years, climate_interventions, label='Climate Interventions (SSP1-1.9)', color='blue')
    
    ax.fill_between(years, 0, bau, alpha=0.1, color='red')
    ax.fill_between(years, bau, cut_emissions, alpha=0.1, color='orange')
    ax.fill_between(years, cut_emissions, emissions_removal, alpha=0.1, color='green')
    ax.fill_between(years, emissions_removal, climate_interventions, alpha=0.1, color='blue')
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Global Surface Temperature Change (°C)\nrelative to 1850-1900')
    ax.set_title('IPCC AR6 Climate Change Scenarios')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(bottom=0, top=6)
    ax.set_xlim(2000, 2100)
    
    plt.tight_layout()
    return fig

def calculate_market_sizes(scenarios, co2_price):
    years, bau, cut_emissions, emissions_removal, climate_interventions = scenarios
    
    emissions_removal_market = np.trapz(cut_emissions - emissions_removal, years) * co2_price * 1e9
    climate_interventions_market = np.trapz(emissions_removal - climate_interventions, years) * co2_price * 1e9
    
    return {
        'Emissions Removal': emissions_removal_market,
        'Climate Interventions': climate_interventions_market
    }

st.title("Interactive IPCC-based Climate Impact Scenarios")

st.write("""
This tool allows you to explore different climate impact scenarios based on IPCC AR6 projections.
Adjust the parameters below to see how they might affect the projected temperature increase above pre-industrial levels.
""")

co2_price = st.slider("CO2 price per ton ($)", 0, 1000, 50, 10)
years_to_reduce = st.slider("Years to reduce emissions by >90%", 0, 100, 30)
intervention_temp = st.slider("Temperature for climate interventions (°C above pre-industrial)", 1.0, 3.0, 1.5, 0.1)
intervention_duration = st.slider("Duration of climate interventions (years)", 0, 100, 20)

scenarios = generate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration)
fig = plot_scenarios(scenarios)
st.pyplot(fig)

market_sizes = calculate_market_sizes(scenarios, co2_price)
st.subheader("Estimated Market Sizes")
st.write(f"Emissions Removal Market: ${market_sizes['Emissions Removal']/1e9:.2f} billion")
st.write(f"Climate Interventions Market: ${market_sizes['Climate Interventions']/1e9:.2f} billion")
st.caption("""
Note: These are rough estimates based on the area between the curves and the CO2 price. 
The Emissions Removal market size represents the potential value of reducing emissions from the 'Cut Emissions Aggressively' scenario to the 'Emissions Removal' scenario. 
The Climate Interventions market size represents the potential value of further reducing emissions from the 'Emissions Removal' scenario to the 'Climate Interventions' scenario.
These estimates are highly simplified and should be interpreted cautiously.

st.markdown("""
### Scenario Descriptions (based on IPCC AR6):
- **Business as Usual (SSP5-8.5)**: High emissions scenario - fossil-fuel development
- **Cut Emissions Aggressively (SSP2-4.5)**: Intermediate emissions scenario
- **Emissions Removal (SSP1-2.6)**: Low emissions scenario - sustainable development
- **Climate Interventions (SSP1-1.9)**: Very low emissions scenario with additional interventions

Note: This visualization is based on approximations of IPCC AR6 projections. The effects of user inputs are simplified representations and should not be considered as precise predictions. For the most accurate information, please refer to the full IPCC reports.
""")

st.markdown("""
Data source: Approximations based on the IPCC Sixth Assessment Report (AR6) projections. 
For more detailed and accurate data, please visit [IPCC AR6 WG1](https://www.ipcc.ch/report/ar6/wg1/).
""")