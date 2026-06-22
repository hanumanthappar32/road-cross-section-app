import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
import io

# Page Configuration
st.set_page_config(page_title="CivilEng Road Analyst", layout="wide")

st.markdown("### 🛣️ CivilEng Road Cross-Section & Drainage Design Utility")
st.write("Conforming to **IRC:73** (Geometric Design) and **IS 456:2000** (Structural Concrete)")

# Sidebar - Engineering Design Parameters
st.sidebar.markdown("### 🛠️ Design Parameters")
road_width = st.sidebar.number_input("Carriageway Width (m)", min_value=3.0, max_value=30.0, value=7.0, step=0.5)
target_camber = st.sidebar.slider("Target Camber (%) as per IRC:73", min_value=1.0, max_value=4.0, value=2.5, step=0.1)
shoulder_width = st.sidebar.number_input("Shoulder Width (m)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)

st.sidebar.markdown("### 🪟 Boundary Concrete Drain (IS 456)")
include_drain = st.sidebar.checkbox("Include Side Drains", value=True)
drain_depth = st.sidebar.number_input("Drain Depth (m)", min_value=0.3, max_value=2.0, value=0.6, step=0.1)
drain_width = st.sidebar.number_input("Drain Width (m)", min_value=0.3, max_value=2.0, value=0.5, step=0.1)

# Default input data
default_data = {
"Offset (m)": [-5.0, -3.5, 0.0, 3.5, 5.0],
"Reduced Level (m)": [98.50, 98.53, 98.60, 98.53, 98.50]
}

st.markdown("### 📊 Input Field Survey Data")
st.write("Modify the survey offsets and Reduced Levels (RL) below. Offset `0.0` represents the Crown/Center Line.")

# Editable Data Table
df = pd.DataFrame(default_data)
edited_df = st.data_editor(df, num_rows="dynamic")

# Engineering Calculations & Camber Verification
st.markdown("### 🔍 Engineering Verification (IRC:73 Standards)")

# Calculate real-time slopes
# Ensure this block is indented inside your main function (usually 4 or 8 spaces)
try:
# Exactly 8 spaces of indentation from the left margin
crown_row = edited_df[edited_df["Offset (m)"] == 0.0]
left_edge = edited_df[edited_df["Offset (m)"] < 0.0].iloc[-1]
right_edge = edited_df[edited_df["Offset (m)"] > 0.0].iloc[0]
except Exception as e:
st.error(f"Geometric extraction failed: {e}")
st.error(f"Error extracting geometric parameters: {e}")
st.error("Error: Please ensure your data has negative offsets for the Left Edge and positive offsets for the Right Edge.")
except Exception as e:
st.error(f"Geometric extraction failed: {e}")ulation
right_edge = edited_df[edited_df["Offset (m)"] > 0.0].iloc[0]
right_slope = abs((right_edge["Reduced Level (m)"] - crown_rl) / right_edge["Offset (m)"]) * 100

col1, col2 = st.columns(2)
with col1:
st.metric("Computed Left Camber", f"{left_slope:.2f} %")
if abs(left_slope - target_camber) <= 0.2:
st.success("✅ Left Camber complies with IRC:73 guidelines.")
else:
st.warning("⚠️ Adjust Left levels to meet the IRC:73 target camber.")

with col2:
st.metric("Computed Right Camber", f"{right_slope:.2f} %")
if abs(right_slope - target_camber) <= 0.2:
st.success("✅ Right Camber complies with IRC:73 guidelines.")
else:
st.warning("⚠️ Adjust Right levels to meet the IRC:73 target camber.")
except Exception as e:
st.error("Please ensure you have valid offsets including a '0.0' center crown offset for analysis.")

# Matplotlib Plotting
st.markdown("### 📉 Cross-Section Visualizer")
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(edited_df["Offset (m)"], edited_df["Reduced Level (m)"], 'o-', color='#1f77b4', label="Pavement Profile")

# Draw Drains if checked (IS 456 check visual aid)
if include_drain:
leftmost_offset = edited_df["Offset (m)"].min() - shoulder_width
rightmost_offset = edited_df["Offset (m)"].max() + shoulder_width
lowest_rl = edited_df["Reduced Level (m)"].min()

# Left Drain Box Drawing
ax.plot([leftmost_offset, leftmost_offset - drain_width, leftmost_offset - drain_width, leftmost_offset],
[lowest_rl, lowest_rl, lowest_rl - drain_depth, lowest_rl - drain_depth], color='red', linestyle='--', label="Concrete Drain (IS 456)")
# Right Drain Box Drawing
ax.plot([rightmost_offset, rightmost_offset + drain_width, rightmost_offset + drain_width, rightmost_offset],
[lowest_rl, lowest_rl, lowest_rl - drain_depth, lowest_rl - drain_depth], color='red', linestyle='--')

ax.set_xlabel("Offset from Center Line (m)")
ax.set_ylabel("Reduced Level (RL) (m)")
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend()
st.pyplot(fig)

# DXF Export Logic using ezdxf
def generate_dxf(data, draw_drain, d_width, d_depth):
doc = ezdxf.new('R2010')
msp = doc.modelspace()

# Draw Pavement Profile
points = list(zip(data["Offset (m)"], data["Reduced Level (m)"]))
for i in range(len(points) - 1):
msp.add_line(points[i], points[i+1], dxfattribs={'layer': 'ROAD_PROFILE', 'color': 1}) # Red Line

# Draw Drains in CAD format
if draw_drain:
l_offset = data["Offset (m)"].min() - 1.5
r_offset = data["Offset (m)"].max() + 1.5
base_rl = data["Reduced Level (m)"].min()

# Left Drain CAD Lines
ld1 = (l_offset, base_rl)
ld2 = (l_offset - d_width, base_rl)
ld3 = (l_offset - d_width, base_rl - d_depth)
ld4 = (l_offset, base_rl - d_depth)
for p1, p2 in [(ld1, ld2), (ld2, ld3), (ld3, ld4), (ld4, ld1)]:
msp.add_line(p1, p2, dxfattribs={'layer': 'CONCRETE_DRAIN', 'color': 3}) # Green Line

# Right Drain CAD Lines
rd1 = (r_offset, base_rl)
rd2 = (r_offset + d_width, base_rl)
rd3 = (r_offset + d_width, base_rl - d_depth)
rd4 = (r_offset, base_rl - d_depth)
for p1, p2 in [(rd1, rd2), (rd2, rd3), (rd3, rd4), (rd4, rd1)]:
msp.add_line(p1, p2, dxfattribs={'layer': 'CONCRETE_DRAIN', 'color': 3})

out_stream = io.StringIO()
doc.write(out_stream)
return out_stream.getvalue()

st.markdown("### 💾 Export deliverables")
dxf_string = generate_dxf(edited_df, include_drain, drain_width, drain_depth)
st.download_button(
label="📥 Download CAD Cross-Section (DXF File)",
data=dxf_string,
file_name="road_cross_section.dxf",
mime="application/dxf"
)


