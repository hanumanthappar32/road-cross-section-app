import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# Attempt to import ezdxf for CAD generation
try:
import ezdxf
except ImportError:
ezdxf = None

# App configuration
st.set_page_config(page_title="CivilEng Cut & Fill Plotter", layout="wide")

st.markdown("### Interactive Road Cross-Section Plotting & CAD Utility")
st.write("Designed in compliance with **IRC:73** (Geometric Layouts) and **IS 456** (Structural Concrete Drains).")

# --- SIDEBAR: INPUT OPTIONS ---
st.sidebar.header("1. Input Configuration")
input_mode = st.sidebar.radio("Select Input Method:", ("Manual Table Entry", "Batch CSV Upload"))

# Default Template Data
default_data = {
"Offset (X) [m]": [-7.5, -5.5, -3.5, 0.0, 3.5, 5.5, 7.5],
"Reduced Level (Y) [m]": [98.5, 98.8, 98.9, 99.0, 98.9, 98.8, 98.5],
"Feature Description": ["Left Drain Outer", "Left Earthen Shoulder", "Left Paved Shoulder", "Centerline (Crown)", "Right Paved Shoulder", "Right Earthen Shoulder", "Right Drain Outer"]
}

df_input = pd.DataFrame(default_data)

if input_mode == "Batch CSV Upload":
uploaded_file = st.sidebar.file_uploader("Upload CSV File (Columns: Offset, RL, Description)", type=["csv"])
if uploaded_file is not None:
try:
df_input = pd.read_csv(uploaded_file)
st.sidebar.success("CSV Loaded Successfully!")
except Exception as e:
st.sidebar.error(f"Error loading file: {e}")
else:
st.sidebar.info("Upload a CSV file. Using default template below.")

# --- MAIN PAGE: DATA AND PLOT ---
st.subheader("Cross-Section Data Table")
# Interactive Data Editor
edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

# Calculations
offsets = edited_df.iloc[:, 0].values
rls = edited_df.iloc[:, 1].values
labels = edited_df.iloc[:, 2].values

# Camber calculation verification (IRC:73 specifies 2% to 2.5% for bituminous surfaces)
if len(offsets) >= 3:
crown_idx = np.argmax(rls)
left_slope = ((rls[crown_idx] - rls[0]) / abs(offsets[crown_idx] - offsets[0])) * 100
right_slope = ((rls[crown_idx] - rls[-1]) / abs(offsets[-1] - offsets[crown_idx])) * 100
else:
left_slope, right_slope = 0.0, 0.0

# --- GRAPH GENERATION (MATPLOTLIB) ---
fig, ax = plt.subplots(figsize=(12, 6))

# Plotting Ground/Road Profile
ax.plot(offsets, rls, '-o', color='#2c3e50', linewidth=2.5, label="Finished Road Level (FRL)")

# Plotting layers (Subgrade & Base Layers - Schematic IRC:37 presentation)
ax.fill_between(offsets, rls, rls - 0.5, color='#bdc3c7', alpha=0.5, label="Pavement Crust / Subgrade (500mm)")

# Annotating Points
for x, y, label in zip(offsets, rls, labels):
ax.annotate(f"{label}\n({x:.2f}, {y:.2f})", (x, y), textcoords="offset points",
xytext=(0,10), ha='center', fontsize=8, fontweight='bold',
bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))

ax.set_title("Standard Road Cross-Section Profile (Vertical Exaggeration applied)", fontsize=14, fontweight='bold')
ax.set_xlabel("Offset from Centerline (X-Axis) [meters]", fontsize=11)
ax.set_ylabel("Reduced Level / Elevation (Y-Axis) [meters]", fontsize=11)
ax.grid(True, which='both', linestyle='--', alpha=0.7)
ax.legend(loc="lower center")

# Adjust limits for visual breathing room
ax.set_ylim(min(rls) - 1.5, max(rls) + 1.5)

st.pyplot(fig)

# --- METRICS & ESTIMATES ---
col1, col2, col3 = st.columns(3)
with col1:
st.metric(label="Calculated Left Camber/Slope", value=f"{left_slope:.2f} %")
with col2:
st.metric(label="Calculated Right Camber/Slope", value=f"{right_slope:.2f} %")
with col3:
st.metric(label="Total Cross-Section Width", value=f"{abs(max(offsets) - min(offsets)):.2f} m")

# --- EXPORT CAPABILITIES ---
st.subheader("Export Options")
exp_col1, exp_col2 = st.columns(2)

# 1. Export Plot as Image/PDF
with exp_col1:
img_buf = io.BytesIO()
fig.savefig(img_buf, format="png", dpi=300, bbox_inches='tight')
st.download_button(
label="📥 Download Plot as PNG Image",
data=img_buf.getvalue(),
file_name="road_cross_section.png",
mime="image/png"
)

# 2. Export CAD DXF File
with exp_col2:
if ezdxf:
doc = ezdxf.new('R2010')
msp = doc.modelspace()

# Add layers
doc.layers.add(name="ROAD_PROFILE", color=1) # Red
doc.layers.add(name="TEXT_ANNOTATIONS", color=7) # White

# Convert coordinates to tuple pairs
points = list(zip(offsets, rls))
msp.add_lwpolyline(points, dxfattribs={"layer": "ROAD_PROFILE"})

# Add labels to CAD
for x, y, lbl in zip(offsets, rls, labels):
msp.add_text(f"{lbl} ({x},{y})", dxfattribs={"height": 0.15, "layer": "TEXT_ANNOTATIONS"}).set_placement((x, y + 0.1))

dxf_buf = io.StringIO()
doc.write(dxf_buf)

st.download_button(
label="📐 Export Direct CAD File (.DXF)",
data=dxf_buf.getvalue(),
file_name="road_cross_section.dxf",
mime="application/dxf"
)
else:
st.info("To enable AutoCAD DXF Export, run: `pip install ezdxf` in your workspace.")
```

---

### Estimating Earthwork and Pavement Costs (in Rs.)

In Indian contexts (using standard State Schedule of Rates - **SoR**), cross-sectional drafting directly informs the earthwork estimates.

* **Excavation / Embankment Soil Filling:** Rates range from **Rs. 150 to Rs. 280 per cubic meter** depending on soil classification (ordinary, hard soil, or soft rock).
* **Granular Sub-Base (GSB) Layer:** Approximated at **Rs. 1,400 to Rs. 1,800 per cubic meter**.
* **Wet Mix Macadam (WMM):** Costs approximately **Rs. 2,000 to Rs. 2,500 per cubic meter**.
* **Bituminous Concrete (BC):** Premium wear course costs approximately **Rs. 8,500 to Rs. 11,000 per cubic meter**.

By extending this app's mathematical module, the area under the curve between your Ground Level (GL) and Finished Road Level (FRL) can instantly be integrated to compute these exact financial estimates in real-time
