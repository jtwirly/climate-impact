import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from openai import OpenAI
import os
import json
from typing import Dict, List

# Get the OpenAI API key from the environment variable
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    st.error("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

def generate_climate_scenarios(co2_price: float, years_to_reduce: int, intervention_temp: float, intervention_duration: int) -> Dict[str, List[float]]:
    prompt = f"""
    Generate realistic climate impact scenarios based on the following parameters:
    - CO2 price: ${co2_price} per ton
    - Years to reduce emissions by >90%: {years_to_reduce}
    - Temperature for climate interventions: {intervention_temp}°C above pre-industrial levels
    - Duration of climate interventions: {intervention_duration} years

    Provide numerical data for four scenarios over 100 years, with temperature increases in °C:
    1. Business as Usual (BAU): Assume no new climate policies.
    2. Cut Emissions Aggressively: Implement strong emission reduction policies.
    3. Emissions Removal: Combine emission cuts with carbon removal technologies.
    4. Climate Interventions: Add geoengineering techniques to other mitigation efforts.

    Ensure the data follows these guidelines:
    - BAU should show the highest temperature increase, typically between 3-6°C by 2100.
    - Each subsequent scenario should show progressively less warming.
    - No scenario should show cooling below pre-industrial levels (i.e., negative values).
    - Climate Interventions should show the least warming, but not below 1°C by 2100.
    - Maximum temperature increase should not exceed 6°C for any scenario.

    Return ONLY a Python dictionary with scenario names as keys and lists of 100 temperature values as values.
    Use the latest IPCC reports for baseline data and projections.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in climate science and data analysis. Provide only the requested dictionary in your response, no other text."},
                {"role": "user", "content": prompt}
            ]
        )

        # Sanitize and parse JSON response
        sanitized_response = response.choices[0].message.content.strip()
        if sanitized_response.startswith("{"):
            sanitized_response = sanitized_response.replace("'", '"')  # Replace single quotes with double quotes
        scenarios = json.loads(sanitized_response)

        # Validate and process scenarios
        if len(scenarios) != 4:
            raise ValueError("Invalid response format: not a dictionary with 4 scenarios")

        normalized_scenarios = {}
        correct_order = ['Business as Usual', 'Cut Emissions Aggressively', 'Emissions Removal', 'Climate Interventions']

        for i, correct_name in enumerate(correct_order):
            matched_key = next((key for key in scenarios.keys() if correct_name.lower() in key.lower()), None)
            if matched_key is None or len(scenarios[matched_key]) < 100:
                # Generate default data if missing or incomplete
                data = np.linspace(0, 6 - i, 100)
            else:
                data = scenarios[matched_key][:100]  # Ensure we have 100 data points

            # Ensure no negative values and cap at 6°C
            normalized_data = np.clip(data, 0, 6).tolist()
            normalized_scenarios[correct_name] = normalized_data

        # Ensure scenarios are in descending order of warming
        for i in range(len(correct_order) - 1):
            if normalized_scenarios[correct_order[i]][-1] <= normalized_scenarios[correct_order[i+1]][-1]:
                # Adjust the data to ensure correct order
                factor = normalized_scenarios[correct_order[i]][-1] / normalized_scenarios[correct_order[i+1]][-1]
                normalized_scenarios[correct_order[i+1]] = [value / factor for value in normalized_scenarios[correct_order[i+1]]]

        return normalized_scenarios
    except Exception as e:
        st.error(f"Failed to generate scenarios: {str(e)}")
        st.write("API Response:", response.choices[0].message.content)
        return None

def update_plot(scenarios: Dict[str, List[float]]):
    fig, ax = plt.subplots(figsize=(12, 8))
    years = np.linspace(0, 100, 100)

    # Define colors
    colors = {
        'Business as Usual': '#1f77b4',  # Blue
        'Cut Emissions Aggressively': '#ff7f0e',  # Orange
        'Emissions Removal': '#2ca02c',  # Green
        'Climate Interventions': '#d62728'  # Red
    }

    max_temp = 0
    # Plot smooth curves and shaded areas
    scenario_names = list(scenarios.keys())
    for i, scenario in enumerate(scenario_names):
        try:
            data = scenarios[scenario]
            max_temp = max(max_temp, max(data))
            
            # Create smooth curve
            spl = make_interp_spline(years, data, k=3)
            smooth_years = np.linspace(0, 100, 300)
            smooth_data = spl(smooth_years)
            
            # Get color, use a default if not found
            color = colors.get(scenario, f'C{i}')  # Use matplotlib's default color cycle if not found
            
            # Plot the smooth curve
            ax.plot(smooth_years, smooth_data, label=scenario, color=color, linewidth=2)
            
            # Add shaded area
            if i < len(scenario_names) - 1:
                next_scenario = scenario_names[i + 1]
                next_data = scenarios[next_scenario]
                next_spl = make_interp_spline(years, next_data, k=3)
                next_smooth_data = next_spl(smooth_years)
                ax.fill_between(smooth_years, smooth_data, next_smooth_data, alpha=0.3, color=color)
        except Exception as e:
            st.error(f"Error plotting scenario '{scenario}': {str(e)}")

    ax.set_xlabel('Time (Years)')
    ax.set_ylabel('Degrees above pre-industrial warming (°C)')
    ax.set_title('Climate Impact Scenarios')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0, top=min(6, max_temp * 1.1))  # Set top of y-axis to 6°C or 110% of max temperature, whichever is lower

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    st.pyplot(fig)
    plt.close(fig)

def calculate_market_sizes(scenarios: Dict[str, List[float]], co2_price: float) -> Dict[str, float]:
    years = np.linspace(0, 100, 100)
    emissions_removal_market = max(0, np.trapz(
        np.array(scenarios['Cut Emissions Aggressively']) - 
        np.array(scenarios['Emissions Removal']), 
        years
    ) * co2_price * 1e9)

    climate_interventions_market = max(0, np.trapz(
        np.array(scenarios['Emissions Removal']) - 
        np.array(scenarios['Climate Interventions']), 
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

# Generate scenarios button
if st.button("Generate Scenarios"):
    with st.spinner("Generating climate scenarios..."):
        scenarios = generate_climate_scenarios(co2_price, years_to_reduce, intervention_temp, intervention_duration)
    
    if scenarios:
        update_plot(scenarios)
        market_sizes = calculate_market_sizes(scenarios, co2_price)
        
        st.markdown(f"""
        ### Estimated Market Sizes
        - Emissions Removal Market: ${market_sizes['Emissions Removal']/1e9:.2f} billion
        - Climate Interventions Market: ${market_sizes['Climate Interventions']/1e9:.2f} billion

        *Note: These are rough estimates based on the provided scenarios and user inputs.*
        """)
    else:
        st.error("Failed to generate scenarios. Please try again.")

# Add explanatory text
st.markdown("""
### Scenario Descriptions:
- **Business as Usual**: Continues current trends without significant changes in policy or behavior.
- **Cut Emissions Aggressively**: Implements strong policies and actions to reduce greenhouse gas emissions.
- **Emissions Removal**: Combines emission cuts with technologies to remove CO2 from the atmosphere.
- **Climate Interventions**: Explores potential geoengineering techniques to directly influence climate.

Note: This visualization is based on IPCC-inspired data and projections, interpreted through an AI model. Actual climate impacts may vary.
""")