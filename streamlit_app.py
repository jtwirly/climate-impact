import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from openai import OpenAI
import json
import os

# Get the OpenAI API key from the environment variable
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    st.error("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Function to generate climate scenarios using OpenAI
def generate_climate_scenarios(client, co2_price, years_to_reduce, intervention_temp, intervention_duration):
    prompt = f"""
    Generate climate impact scenarios based on the following parameters:
    - CO2 price: ${co2_price} per ton
    - Years to reduce emissions by >90%: {years_to_reduce}
    - Temperature for climate interventions: {intervention_temp}°C above pre-industrial levels
    - Duration of climate interventions: {intervention_duration} years

    Provide data for four scenarios over 100 years:
    1. Business as Usual
    2. Cut Emissions Aggressively
    3. Emissions Removal
    4. Climate Interventions

    Use credible sources like IPCC reports for baseline data and projections.
    Format the response as a JSON object with keys for each scenario, containing arrays of 100 temperature values.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in climate science and data analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return json.loads(response.choices[0].message.content)

# Set page config
st.set_page_config(
    page_title='Climate Impact Scenarios',
    page_icon=':earth_americas:',
)

# Title
st.title('🌍 Climate Impact Scenarios')

st.write("""
This tool allows you to explore different climate impact scenarios based on various interventions.
Adjust the parameters below to see how they affect the projected climate impact over time.
""")

# User inputs
co2_price = st.slider("What do you think is the right price per ton of CO2e?", 0, 1000, 50, 10)
years_to_reduce = st.slider("How long do you think it will take to reduce annual GHG emissions by >90%?", 0, 100, 30)
intervention_temp = st.slider("At what temperature above pre-industrial levels should climate interventions start?", 1.0, 3.0, 1.5, 0.1)
intervention_duration = st.slider("How long do you think it will take from start to finish of relying on climate interventions?", 0, 100, 20)

if st.button("Generate Scenarios"):
    with st.spinner("Generating climate scenarios..."):
        scenarios = generate_climate_scenarios(client, co2_price, years_to_reduce, intervention_temp, intervention_duration)

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    years = np.arange(100)

    for scenario, data in scenarios.items():
        ax.plot(years, data, label=scenario)

    ax.fill_between(years, scenarios['Emissions Removal'], scenarios['Cut Emissions Aggressively'], alpha=0.3, label='Emissions Removal')
    ax.fill_between(years, scenarios['Climate Interventions'], scenarios['Emissions Removal'], alpha=0.3, label='Climate Interventions')

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