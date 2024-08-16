import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

def generate_scenario(start, peak, end, years, peak_year, curve_type='custom'):
    x = np.linspace(0, years, years+1)
    if curve_type == 'custom':
        before_peak = start + (peak - start) * (x[:peak_year+1] / peak_year)**2
        after_peak = peak + (end - peak) * ((x[peak_year:] - peak_year) / (years - peak_year))**0.5
        y = np.concatenate([before_peak, after_peak[1:]])
    elif curve_type == 'exponential':
        y = start + (end - start) * (1 - np.exp(-3 * x / years)) / (1 - np.exp(-3))
    return y

def generate_climate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration):
    years = 100
    bau_end = 5.0 + (1 - co2_price / 1000)  # Higher CO2 price slightly reduces BAU endpoint
    cut_emissions_peak = 3.0 - (co2_price / 500)
    cut_emissions_end = cut_emissions_peak * (1 - min(years_to_reduce, 90) / 100)
    removal_peak = cut_emissions_peak * 0.9
    removal_end = cut_emissions_end * 0.8
    interventions_peak = removal_peak * 0.95
    interventions_end = max(0.5, removal_end * 0.6)

    scenarios = {
        'Business as Usual': generate_scenario(1, bau_end, bau_end, years, years, 'exponential'),
        'Cut Emissions Aggressively': generate_scenario(1, cut_emissions_peak, cut_emissions_end, years, 40),
        'Emissions Removal': generate_scenario(1, removal_peak, removal_end, years, 50),
        'Climate Interventions': generate_scenario(1, interventions_peak, interventions_end, years, 60)
    }

    # Apply intervention effect
    intervention_start = np.argmax(scenarios['Emissions Removal'] > intervention_temp)
    intervention_end = min(years, intervention_start + intervention_duration)
    intervention_effect = np.linspace(0, 1, intervention_end - intervention_start)
    scenarios['Climate Interventions'][intervention_start:intervention_end] -= intervention_effect * (scenarios['Climate Interventions'][intervention_start:intervention_end] - interventions_end)

    return scenarios

def update_plot(scenarios):
    fig, ax = plt.subplots(figsize=(12, 8))
    years = np.linspace(0, 100, 101)

    colors = {
        'Business as Usual': '#1f77b4',
        'Cut Emissions Aggressively': '#ff7f0e',
        'Emissions Removal': '#2ca02c',
        'Climate Interventions': '#d62728'
    }

    for i, (scenario, data) in enumerate(scenarios.items()):
        color = colors[scenario]
        spl = make_interp_spline(years, data, k=3)
        smooth_years = np.linspace(0, 100, 300)
        smooth_data = spl(smooth_years)
        ax.plot(smooth_years, smooth_data, label=scenario, color=color, linewidth=2)

        if i < len(scenarios) - 1:
            next_scenario = list(scenarios.keys())[i+1]
            next_data = scenarios[next_scenario]
            next_spl = make_interp_spline(years, next_data, k=3)
            next_smooth_data = next_spl(smooth_years)
            ax.fill_between(smooth_years, smooth_data, next_smooth_data, alpha=0.3, color=color)

    ax.set_xlabel('Time (Years)')
    ax.set_ylabel('Degrees above pre-industrial warming (°C)')
    ax.set_title('Climate Impact Scenarios')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0, top=6)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    st.pyplot(fig)

def calculate_market_sizes(scenarios, co2_price):
    years = np.linspace(0, 100, 101)
    emissions_removal_market = max(0, np.trapz(
        scenarios['Cut Emissions Aggressively'] - scenarios['Emissions Removal'], 
        years
    ) * co2_price * 1e9)

    climate_interventions_market = max(0, np.trapz(
        scenarios['Emissions Removal'] - scenarios['Climate Interventions'], 
        years
    ) * co2_price * 1e9)

    return {
        'Emissions Removal': emissions_removal_market,
        'Climate Interventions': climate_interventions_market
    }

# Streamlit app
st.title("Interactive Climate Impact Scenarios")

st.write("""
This tool allows you to explore different climate impact scenarios based on various interventions.
Adjust the parameters below to see how they affect the projected climate impact over time.
""")

# User inputs
co2_price = st.number_input("What do you think is the right price per ton of CO2e?", min_value=0, max_value=1000, value=50, step=10)
years_to_reduce = st.slider("How long do you think it will take to reduce annual GHG emissions by >90%?", 0, 100, 30)
intervention_temp = st.slider("At what temperature above pre-industrial levels should climate interventions start?", 1.0, 3.0, 1.5, 0.1)
intervention_duration = st.slider("How long do you think it will take from start to finish of relying on climate interventions?", 0, 100, 20)

# Generate scenarios and update plot
scenarios = generate_climate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration)
update_plot(scenarios)

# Calculate and display market sizes
market_sizes = calculate_market_sizes(scenarios, co2_price)
st.markdown(f"""
### Estimated Market Sizes
- Emissions Removal Market: ${market_sizes['Emissions Removal']/1e9:.2f} billion
- Climate Interventions Market: ${market_sizes['Climate Interventions']/1e9:.2f} billion

*Note: These are rough estimates based on the provided scenarios and user inputs.*
""")

# Add explanatory text
st.markdown("""
### Scenario Descriptions:
- **Business as Usual**: Continues current trends without significant changes in policy or behavior.
- **Cut Emissions Aggressively**: Implements strong policies and actions to reduce greenhouse gas emissions.
- **Emissions Removal**: Combines emission cuts with technologies to remove CO2 from the atmosphere.
- **Climate Interventions**: Explores potential geoengineering techniques to directly influence climate.

Note: This visualization is based on simplified models and should not be considered as precise predictions. Actual climate impacts may vary significantly.
""")