import streamlit as st
import numpy as np
import plotly.graph_objects as go
from keras.models import load_model  # or tensorflow.keras.models if consistent

# Load the ESG model
def load_esg_model():
    try:
        model = load_model("esg_model.h5")
        return model
    except Exception as e:
        st.error(f"Error loading ESG model: {e}")
        return None

# ESG suggestions function (updated for 3-output model)
def get_esg_suggestions(input_data, prediction):
    suggestions = []

    environmental_risk = prediction[0][0]
    social_risk = prediction[0][1]
    governance_risk = prediction[0][2]

    # Thresholds
    environmental_threshold = 0.6
    social_threshold = 0.5
    governance_threshold = 0.4

    # ---- Environmental ----
    if environmental_risk > environmental_threshold or input_data[0] > 70:
        suggestions.append("🌱 Reduce carbon footprint by adopting renewable energy sources and optimizing logistics.")
    if input_data[1] < 50:
        suggestions.append("💡 Improve energy efficiency with smart automation and LED lighting.")
    if input_data[2] < 50:
        suggestions.append("♻️ Implement better waste management and recycling programs.")
    if input_data[3] < 50:
        suggestions.append("🧪 Use more eco-friendly materials in production.")

    # ---- Social ----
    if social_risk > social_threshold:
        suggestions.append("🤝 Improve social responsibility by addressing employee wellbeing and community outreach.")
    if input_data[4] < 50:
        suggestions.append("🦺 Increase workplace safety measures and provide employee training.")
    if input_data[5] < 50:
        suggestions.append("👩‍💼 Promote diversity and inclusion in hiring and leadership roles.")
    if input_data[6] < 50:
        suggestions.append("🏡 Strengthen CSR initiatives and community involvement.")

    # ---- Governance ----
    if governance_risk > governance_threshold:
        suggestions.append("📜 Strengthen governance with stricter compliance, audits, and transparency.")
    if input_data[7] < 50:
        suggestions.append("🔍 Improve policy adherence and regulatory compliance.")
    if input_data[8] < 50:
        suggestions.append("🧾 Publish detailed sustainability reports.")
    if input_data[9] < 50:
        suggestions.append("📈 Improve enterprise risk management practices.")

    return suggestions

# Chart functions
def create_radar_chart(input_data):
    categories = ['Carbon Emissions', 'Energy Efficiency', 'Waste Management', 'Eco-Friendly Materials',
                  'Worker Safety', 'Diversity & Inclusion', 'CSR Activities', 'Policy Compliance',
                  'Transparency', 'Risk Management']
    fig = go.Figure(go.Scatterpolar(
        r=input_data + [input_data[0]],
        theta=categories + [categories[0]],
        fill='toself'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    return fig

def create_bar_chart(prediction):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Bar(
        x=["Environmental", "Social", "Governance"],
        y=prediction[0]
    )])
    fig.update_layout(title='Predicted ESG Risk (3 Pillars)', yaxis_title='Risk Score')
    return fig



# Main function to show ESG dashboard
def show_esg_dashboard():
    st.title("🌍 ESG Risk Assessment Dashboard")
    st.markdown("Analyze ESG parameters and get recommendations to improve your **sustainability score**.")

    model = load_esg_model()
    if model is None:
        return

    # Sidebar sliders
    st.sidebar.header("Input ESG Parameters")
    col1, col2 = st.sidebar.columns(2)
    carbon_emissions = col1.slider("Carbon Emissions", 0, 100, 50)
    energy_efficiency = col2.slider("Energy Efficiency", 0, 100, 50)
    waste_management = col1.slider("Waste Management", 0, 100, 50)
    eco_friendly_materials = col2.slider("Eco-Friendly Materials", 0, 100, 50)
    worker_safety = col1.slider("Worker Safety", 0, 100, 50)
    diversity_inclusion = col2.slider("Diversity & Inclusion", 0, 100, 50)
    csr_activities = col1.slider("CSR Activities", 0, 100, 50)
    policy_compliance = col2.slider("Policy Compliance", 0, 100, 50)
    transparency_score = col1.slider("Transparency Score", 0, 100, 50)
    risk_management = col2.slider("Risk Management", 0, 100, 50)

    input_data = [
        carbon_emissions, energy_efficiency, waste_management, eco_friendly_materials,
        worker_safety, diversity_inclusion, csr_activities, policy_compliance,
        transparency_score, risk_management
    ]

    if st.sidebar.button("🔍 Predict Risk Level"):
        input_array = np.array(input_data).reshape(1, -1)
        prediction = model.predict(input_array)

        col3, col4 = st.columns(2)
        col3.plotly_chart(create_radar_chart(input_data), use_container_width=True)
        col4.plotly_chart(create_bar_chart(prediction), use_container_width=True)

        st.subheader("📊 Prediction Probabilities")
        pillars = ["Environmental", "Social", "Governance"]
        for i, prob in enumerate(prediction[0]):
            st.write(f"- **{pillars[i]}**: `{prob:.4f}`")

        st.subheader("💡 Suggestions for Improvement")
        suggestions = get_esg_suggestions(input_data, prediction)
        if suggestions:
            for s in suggestions:
                st.markdown(f"✅ {s}")
        else:
            st.success("🎉 Your ESG profile looks excellent!")
