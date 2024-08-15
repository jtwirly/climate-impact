import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
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
    Generate climate impact scenarios based on the following parameters:
    - CO2 price: ${co2_price} per ton
    - Years to reduce emissions by >90%: {years_to_reduce}
    - Temperature for climate interventions: {intervention_temp}°C above pre-industrial levels
    - Duration of climate interventions: {intervention_duration} years

    Provide numerical data for four scenarios over 100 years:
    1. Business as Usual
    2. Cut Emissions Aggressively
    3. Emissions Removal
    4. Climate Interventions

    Return ONLY a Python dictionary with scenario names as keys and lists of temperature values as values.
    Use credible sources like IPCC reports for baseline data and projections.
    The dictionary should look like this:
    {{"Business as Usual": [list of values], "Cut Emissions Aggressively": [list of values], ...}}
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
        for scenario, data in scenarios.items():
            if not isinstance(data, list):
                raise ValueError(f"Invalid data for scenario '{scenario}': expected list of values")
            normalized_scenarios[scenario] = normalize_data(data)
        
        return normalized_scenarios
    except Exception as e:
        st.error(f"Failed to parse the response: {e}")
        st.write("API Response:", response.choices[0].message.content)
        return None

def update_plot():
    fig, ax = plt.subplots(figsize=(12, 8))
    years = np.arange(100)

    for scenario, base_data in st.session_state.scenarios.items():
        # Apply the scaling factors to the data
        scaled_data = np.array(base_data) * st.session_state[f"{scenario}_scale"]
        ax.plot(years, scaled_data, label=scenario)

    ax.set_xlabel('Time (Years)')
    ax.set_ylabel('Degrees above pre-industrial warming')
    ax.set_title('Climate Impact Scenarios')
    ax.legend()
    ax.grid(True)

    st.session_state.plot_placeholder.pyplot(fig)
    plt.close(fig)

    # Calculate and update market sizes
    emissions_removal_market = np.trapz(
        np.array(st.session_state.scenarios['Cut Emissions Aggressively']) * st.session_state['Cut Emissions Aggressively_scale'] - 
        np.array(st.session_state.scenarios['Emissions Removal']) * st.session_state['Emissions Removal_scale'], 
        years
    ) * st.session_state.co2_price * 1e9

    climate_interventions_market = np.trapz(
        np.array(st.session_state.scenarios['Emissions Removal']) * st.session_state['Emissions Removal_scale'] - 
        np.array(st.session_state.scenarios['Climate Interventions']) * st.session_state['Climate Interventions_scale'], 
        years
    ) * st.session_state.co2_price * 1e9

    st.session_state.market_sizes.markdown(f"""
    ### Estimated Market Sizes
    - Emissions Removal Market: ${emissions_removal_market/1e9:.2f} billion
    - Climate Interventions Market: ${climate_interventions_market/1e9:.2f} billion

    *Note: These are rough estimates based on the provided scenarios and user inputs.*
    """)

# Set page config
st.set_page_config(page_title='Climate Impact Scenarios', page_icon=':earth_americas:')

# Title
st.title('Climate Impact Scenarios')

st.write("""
This tool allows you to explore different climate impact scenarios based on various interventions.
Adjust the parameters below to see how they affect the projected climate impact over time.
""")

# Initialize session state
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = None

# User inputs
st.session_state.co2_price = st.number_input("What do you think is the right price per ton of CO2e?", min_value=0, max_value=1000, value=50, step=10)
years_to_reduce = st.slider("How long do you think it will take to reduce annual GHG emissions by >90%?", 0, 100, 30)
intervention_temp = st.slider("At what temperature above pre-industrial levels should climate interventions start?", 1.0, 3.0, 1.5, 0.1)
intervention_duration = st.slider("How long do you think it will take from start to finish of relying on climate interventions?", 0, 100, 20)

# Generate scenarios button
if st.button("Generate Scenarios") or st.session_state.scenarios is None:
    with st.spinner("Generating climate scenarios..."):
        st.session_state.scenarios = generate_climate_scenarios(client, st.session_state.co2_price, years_to_reduce, intervention_temp, intervention_duration)

if st.session_state.scenarios:
    # Create sliders for each scenario
    for scenario in st.session_state.scenarios.keys():
        if f"{scenario}_scale" not in st.session_state:
            st.session_state[f"{scenario}_scale"] = 1.0
        st.session_state[f"{scenario}_scale"] = st.slider(f"Adjust {scenario} impact", 0.5, 2.0, 1.0, 0.1, key=f"{scenario}_scale_slider")

    # Create placeholders for the plot and market sizes
    if 'plot_placeholder' not in st.session_state:
        st.session_state.plot_placeholder = st.empty()
    if 'market_sizes' not in st.session_state:
        st.session_state.market_sizes = st.empty()

    # Update the plot
    update_plot()
else:
    st.error("Failed to generate scenarios. Please try again.")