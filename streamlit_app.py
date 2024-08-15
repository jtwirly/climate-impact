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
        # Use ast.literal_eval to safely evaluate the string as a Python expression
        scenarios = ast.literal_eval(response.choices[0].message.content)
        if not isinstance(scenarios, dict) or len(scenarios) != 4:
            raise ValueError("Invalid response format: not a dictionary with 4 scenarios")
        
        # Normalize data for each scenario
        normalized_scenarios = {}
        for scenario, data in scenarios.items():
            if not isinstance(data, list):
                raise ValueError(f"Invalid data for scenario '{scenario}': expected list of values")
            normalized_scenarios[scenario] = normalize_data(data)
        
        return normalized_scenarios
    except Exception as e:
        st.error(f"Failed to parse the response: {e}")
        st.write("API Response:", response.choices[0].message.content)  # Debugging info
        return None

# Set page config
st.set_page_config(page_title='Climate Impact Scenarios', page_icon=':earth_americas:')

# Title
st.title('Climate Impact Scenarios')

st.write("""
This tool allows you to explore different climate impact scenarios based on various interventions.
Adjust the parameters below to see how they affect the projected climate impact over time.
""")

# User inputs
co2_price = st.number_input("What do you think is the right price per ton of CO2e?", min_value=0, max_value=1000, value=50, step=10)
years_to_reduce = st.slider("How long do you think it will take to reduce annual GHG emissions by >90%?", 0, 100, 30)
intervention_temp = st.slider("At what temperature above pre-industrial levels should climate interventions start?", 1.0, 3.0, 1.5, 0.1)
intervention_duration = st.slider("How long do you think it will take from start to finish of relying on climate interventions?", 0, 100, 20)

if st.button("Generate Scenarios"):
    with st.spinner("Generating climate scenarios..."):
        scenarios = generate_climate_scenarios(client, co2_price, years_to_reduce, intervention_temp, intervention_duration)

    if scenarios is None:
        st.error("Failed to generate scenarios. Please try again.")
    else:
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        years = np.arange(100)

        for scenario, data in scenarios.items():
            ax.plot(years, data, label=scenario)

        ax.set_xlabel('Time (Years)')
        ax.set_ylabel('Degrees above pre-industrial warming')
        ax.set_title('Climate Impact Scenarios')
        ax.legend()
        ax.grid(True)

        # Display the plot
        st.pyplot(fig)

        # Calculate market sizes
        emissions_removal_market = np.trapz(np.array(scenarios['Cut Emissions Aggressively']) - np.array(scenarios['Emissions Removal']), years) * co2_price * 1e9
        climate_interventions_market = np.trapz(np.array(scenarios['Emissions Removal']) - np.array(scenarios['Climate Interventions']), years) * co2_price * 1e9

        st.subheader('Estimated Market Sizes')
        st.write(f"Emissions Removal Market: ${emissions_removal_market/1e9:.2f} billion")
        st.write(f"Climate Interventions Market: ${climate_interventions_market/1e9:.2f} billion")

        st.caption("Note: These are rough estimates based on the provided scenarios and user inputs.")