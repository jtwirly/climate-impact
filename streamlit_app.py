import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from openai import OpenAI
import os
import ast

# Get the OpenAI API key from the environment variable
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    st.error("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

def normalize_data(data, target_length=100):
    """Normalize data to target length by padding or trimming."""
    if len(data) < target_length:
        return data + [data[-1]] * (target_length - len(data))
    return data[:target_length]

def generate_climate_scenarios(client, co2_price, years_to_reduce, intervention_temp, intervention_duration):
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

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in climate science and data analysis. Provide only the requested dictionary in your response, no other text."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        scenarios = ast.literal_eval(response.choices[0].message.content)
        if not isinstance(scenarios, dict) or len(scenarios) != 4:
            raise ValueError("Invalid response format: not a dictionary with 4 scenarios")
        
        normalized_scenarios = {}
        correct_order = ['Business as Usual', 'Cut Emissions Aggressively', 'Emissions Removal', 'Climate Interventions']
        
        for correct_name in correct_order:
            matched_key = next((key for key in scenarios.keys() if correct_name in key), None)
            if matched_key is None:
                raise ValueError(f"Missing scenario: {correct_name}")
            
            data = scenarios[matched_key]
            if not isinstance(data, list):
                raise ValueError(f"Invalid data for scenario '{matched_key}': expected list of values")
            
            normalized_data = normalize_data(data)
            # Ensure no negative values and cap at 6°C
            normalized_data = [min(max(0, value), 6) for value in normalized_data]
            normalized_scenarios[correct_name] = normalized_data
        
        # Ensure scenarios are in descending order of warming
        for i in range(len(correct_order) - 1):
            if normalized_scenarios[correct_order[i]][-1] <= normalized_scenarios[correct_order[i+1]][-1]:
                raise ValueError(f"Scenario {correct_order[i]} should show more warming than {correct_order[i+1]}")
        
        return normalized_scenarios
    except Exception as e:
        st.error(f"Failed to parse the response: {e}")
        st.write("API Response:", response.choices[0].message.content)
        return None

def update_plot():
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
    scenario_names = list(st.session_state.scenarios.keys())
    for i, scenario in enumerate(scenario_names):
        try:
            data = st.session_state.scenarios[scenario]
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
                next_data = st.session_state.scenarios[next_scenario]
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
    ax.set_ylim(bottom=0, top=min(10, max_temp * 1.1))  # Set top of y-axis to 10°C or 110% of max temperature, whichever is lower

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    st.pyplot(fig)
    plt.close(fig)

    try:
        # Calculate and update market sizes
        emissions_removal_market = max(0, np.trapz(
            np.array(st.session_state.scenarios['Cut Emissions Aggressively']) - 
            np.array(st.session_state.scenarios['Emissions Removal']), 
            years
        ) * st.session_state.co2_price * 1e9)

        climate_interventions_market = max(0, np.trapz(
            np.array(st.session_state.scenarios['Emissions Removal']) - 
            np.array(st.session_state.scenarios['Climate Interventions']), 
            years
        ) * st.session_state.co2_price * 1e9)

        st.markdown(f"""
        ### Estimated Market Sizes
        - Emissions Removal Market: ${emissions_removal_market/1e9:.2f} billion
        - Climate Interventions Market: ${climate_interventions_market/1e9:.2f} billion

        *Note: These are rough estimates based on the provided scenarios and user inputs.*
        """)
    except Exception as e:
        st.error(f"Error calculating market sizes: {str(e)}")

# Streamlit app
st.title("Interactive Climate Impact Scenarios")

st.write("""
This tool allows you to explore different climate impact scenarios based on various interventions.
Adjust the parameters below to see how they affect the projected climate impact over time.
""")

# Initialize session state
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = None

# User inputs
st.session_state.co2_price = st.number_input("What do you think is the right price per ton of CO2e?", min_value=0, max_value=1000, value=50, step=10)
st.session_state.years_to_reduce = st.slider("How long do you think it will take to reduce annual GHG emissions by >90%?", 0, 100, 30)
st.session_state.intervention_temp = st.slider("At what temperature above pre-industrial levels should climate interventions start?", 1.0, 3.0, 1.5, 0.1)
st.session_state.intervention_duration = st.slider("How long do you think it will take from start to finish of relying on climate interventions?", 0, 100, 20)

# Generate scenarios button
if st.button("Generate Scenarios") or st.session_state.scenarios is None:
    with st.spinner("Generating climate scenarios..."):
        st.session_state.scenarios = generate_climate_scenarios(
            client, 
            st.session_state.co2_price, 
            st.session_state.years_to_reduce, 
            st.session_state.intervention_temp, 
            st.session_state.intervention_duration
        )

if st.session_state.scenarios:
    update_plot()
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