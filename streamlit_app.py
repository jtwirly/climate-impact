import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

def generate_scenario(scenario_type, years, params):
    x = np.linspace(0, years, years+1)
    if scenario_type == 'BAU':
        y = params['start'] + (params['end'] - params['start']) * (x / years)**1.5
    elif scenario_type == 'Cut Emissions':
        peak = params['peak_year']
        y = np.where(x <= peak, 
                     params['start'] + (params['peak'] - params['start']) * (x / peak)**1.2,
                     params['peak'] + (params['end'] - params['peak']) * ((x - peak) / (years - peak))**0.5)
    elif scenario_type == 'Emissions Removal':
        peak = params['peak_year']
        y = np.where(x <= peak, 
                     params['start'] + (params['peak'] - params['start']) * (x / peak)**1.3,
                     params['peak'] + (params['end'] - params['peak']) * ((x - peak) / (years - peak))**0.7)
    elif scenario_type == 'Climate Interventions':
        intervention_start = params['intervention_start']
        y = np.where(x <= intervention_start, 
                     params['start'] + (params['peak'] - params['start']) * (x / intervention_start)**1.2,
                     params['end'] + (params['peak'] - params['end']) * np.exp(-0.1 * (x - intervention_start)))
    return y

def generate_climate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration):
    years = 100
    intervention_start = int(intervention_temp * 20)  # Rough conversion from temperature to year

    scenarios = {
        'Business as Usual': generate_scenario('BAU', years, {'start': 0, 'end': 5.5}),
        'Cut Emissions Aggressively': generate_scenario('Cut Emissions', years, {'start': 0, 'peak': 3.5, 'end': 3.0, 'peak_year': 40}),
        'Emissions Removal': generate_scenario('Emissions Removal', years, {'start': 0, 'peak': 3.8, 'end': 2.5, 'peak_year': 50}),
        'Climate Interventions': generate_scenario('Climate Interventions', years, {'start': 0, 'peak': 3.0, 'end': 0.5, 'intervention_start': intervention_start})
    }

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
    ax.set_ylabel('Climate Impacts')
    ax.set_title('Climate Impact Scenarios')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    st.pyplot(fig)

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

# Add explanatory text
st.markdown("""
### Scenario Descriptions:
- **Business as Usual**: Continues current trends without significant changes in policy or behavior.
- **Cut Emissions Aggressively**: Implements strong policies and actions to reduce greenhouse gas emissions.
- **Emissions Removal**: Combines emission cuts with technologies to remove CO2 from the atmosphere.
- **Climate Interventions**: Explores potential geoengineering techniques to directly influence climate.

Note: This visualization is based on a conceptual model and should not be considered as precise predictions. Actual climate impacts may vary significantly.
""")