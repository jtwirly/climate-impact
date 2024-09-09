import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load IPCC data from CSV
def load_ipcc_data():
    df = pd.read_csv('data/CMIP6_Atlas_WarmingLevels.csv')
    
    # Convert 9999 to NaN
    df = df.replace(9999, np.nan)
    
    # Calculate the mean year for each warming level and scenario
    scenarios = ['ssp126', 'ssp245', 'ssp370', 'ssp585']
    warming_levels = [1.5, 2, 3, 4]
    
    result = {}
    for scenario in scenarios:
        scenario_data = []
        for level in warming_levels:
            col = f'{level}_{scenario}'
            mean_year = df[col].mean()
            scenario_data.append((level, mean_year))
        
        # Sort by year and remove NaN values
        scenario_data = sorted([(level, year) for level, year in scenario_data if not np.isnan(year)])
        
        # Interpolate to get yearly data
        years = range(2000, 2101)
        temperatures = np.interp(years, 
                                 [2000] + [year for _, year in scenario_data], 
                                 [0] + [level for level, _ in scenario_data])
        
        result[scenario] = temperatures
    
    return pd.DataFrame(result, index=years)

ipcc_data = load_ipcc_data()

def generate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration):
    years = range(2000, 2101)
    bau = ipcc_data['ssp585']
    cut_emissions = ipcc_data['ssp245']
    emissions_removal = ipcc_data['ssp126']
    climate_interventions = ipcc_data['ssp126'].copy()  # Using SSP1-2.6 as a base for interventions

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
    
    ax.plot(years, bau, label='SSP5-8.5 (Fossil-fueled Development)', color='red')
    ax.plot(years, cut_emissions, label='SSP2-4.5 (Middle of the Road)', color='orange')
    ax.plot(years, emissions_removal, label='SSP1-2.6 (Sustainability)', color='green')
    ax.plot(years, climate_interventions, label='Climate Interventions', color='blue')
    
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
    ax.set_ylim(bottom=0, top=5)
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
The baseline data is derived from multiple climate models as reported in the IPCC AR6.
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
The Emissions Removal market size represents the potential value of reducing emissions from the 'SSP2-4.5' scenario to the 'SSP1-2.6' scenario. 
The Climate Interventions market size represents the potential value of further reducing emissions from the 'SSP1-2.6' scenario to the 'Climate Interventions' scenario.
These estimates are highly simplified and should be interpreted cautiously.
""")

st.markdown("""
### Scenario Descriptions (based on IPCC AR6):
- **SSP5-8.5**: Fossil-fueled Development - High emissions scenario
- **SSP2-4.5**: Middle of the Road - Intermediate emissions scenario
- **SSP1-2.6**: Sustainability - Low emissions scenario
- **Climate Interventions**: Custom scenario based on SSP1-2.6 with additional interventions

Note: This visualization is based on IPCC AR6 projections from multiple climate models. The effects of user inputs are simplified representations and should be interpreted cautiously.
""")

st.markdown("""
Data source: IPCC Sixth Assessment Report (AR6) projections. 
For more detailed information, please visit [IPCC AR6 WG1](https://www.ipcc.ch/report/ar6/wg1/).

**Citation:**

Iturbide, M., Fernández, J., Gutiérrez, J.M., Bedia, J., Cimadevilla, E., Díez-Sierra, J., Manzanas, R., Casanueva, A., Baño-Medina, J., Milovac, J., Herrera, S., Cofiño, A.S., San Martín, D., García-Díez, M., Hauser, M., Huard, D., Yelekci, Ö. (2021) Repository supporting the implementation of FAIR principles in the IPCC-WG1 Atlas. Zenodo, DOI: 10.5281/zenodo.3691645. Available from: https://github.com/IPCC-WG1/Atlas
""")
