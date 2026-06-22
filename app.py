import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(page_title="Pavement Camber Analyzer", layout="wide")

st.markdown("### 📐 Road Cross-Section & Camber Analyzer")
st.write(
"This utility computes road cross-falls (camber) based on user-defined offsets and elevations "
"to ensure compliance with Indian Road Congress (IRC) standards."
)

# 1. Provide a clean, default cross-section (7.0m Carriageway with 2.5% standard cross-fall)
default_data = {
"Offset (m)": [-7.0, -3.5, 0.0, 3.5, 7.0],
"Elevation (m)": [99.825, 99.912, 100.000, 99.912, 99.825]
}
df_default = pd.DataFrame(default_data)

st.markdown("#### 📝 Edit Cross-Section Coordinates")
st.write("Double-click cells to modify. Ensure 'Offset (m)' contains negative values, exactly 0.0 (Crown), and positive values.")

# Dynamic data editor
edited_df = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)

# Clean and sort inputs to ensure geometry calculations align perfectly
edited_df = edited_df.dropna().sort_values(by="Offset (m)").reset_index(drop=True)

# 2. Safety Check & Structural Geometric Extraction
try:
# Extract the crown and side parameters
crown_row = edited_df[edited_df["Offset (m)"] == 0.0]
left_side = edited_df[edited_df["Offset (m)"] < 0.0]
right_side = edited_df[edited_df["Offset (m)"] > 0.0]

if crown_row.empty:
st.error("❌ Critical Error: Crown point (Offset = 0.0) is missing. Please add a row with Offset = 0.0.")
elif left_side.empty or right_side.empty:
st.warning("⚠️ Warning: Please input both negative (Left) and positive (Right) offsets to compute bilateral cross-slopes.")
else:
# Extract key design points
crown_elev = crown_row["Elevation (m)"].values[0]
left_edge = left_side.iloc[-1] # Closest left point to crown
right_edge = right_side.iloc[0] # Closest right point to crown

# Extract values
l_offset, l_elev = left_edge["Offset (m)"], left_edge["Elevation (m)"]
r_offset, r_elev = right_edge["Offset (m)"], right_edge["Elevation (m)"]

# Calculate distances and falls
left_distance = abs(l_offset)
right_distance = abs(r_offset)

left_fall = crown_elev - l_elev
right_fall = crown_elev - r_elev

# Camber calculation in percentage
left_camber = (left_fall / left_distance) * 100
right_camber = (right_fall / right_distance) * 100

# Display Metrics in Columns
col1, col2, col3 = st.columns(3)
with col1:
st.metric("Crown Elevation", f"{crown_elev:.3f} m")
with col2:
st.metric("Left Camber", f"{left_camber:.2f}%", delta=f"{left_camber - 2.5:.2f}% vs 2.5% Target")
with col3:
st.metric("Right Camber", f"{right_camber:.2f}%", delta=f"{right_camber - 2.5:.2f}% vs 2.5% Target")

# Plotting the cross-section
st.markdown("#### 📊 Pavement Profile Preview")
st.line_chart(data=edited_df, x="Offset (m)", y="Elevation (m)", use_container_width=True)

# 3. Structural Compliance Verification
st.markdown("#### ⚖️ IRC Compliance Assessment")

# Verify against IRC:73 recommended minimum camber of 2.0% - 2.5%
if abs(left_camber) < 2.0 or abs(right_camber) < 2.0:
st.error("🛑 NON-COMPLIANT: Camber is below 2.0%. High risk of water ponding and hydroplaning (IRC:73).")
elif abs(left_camber) > 3.0 or abs(right_camber) > 3.0:
st.warning("⚠️ WARNING: Camber exceeds 3.0%. High risk of vehicle lateral slip and rapid shoulder erosion.")
else:
st.success("✅ COMPLIANT: Camber is within the optimal 2.0% - 2.5% safety envelope.")

except Exception as e:
st.error(f"❌ Structural parser runtime error: {str(e)}")
st.info("Ensure all coordinate inputs are valid numbers and non-empty.")
