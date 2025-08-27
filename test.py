#  --- Imports & setup ----------------------------------------------------------
try:
    import sionna.rt
except ImportError:
    import os
    os.system("pip install sionna-rt")
    import sionna.rt

import numpy as np
import time

from sionna.rt import (
    load_scene, PlanarArray, Transmitter, Receiver,
    PathSolver, RadioMapSolver, subcarrier_frequencies
)

# --- Load scene ---------------------------------------------------------------
scene = load_scene(sionna.rt.scene.munich, merge_shapes=True)
# Clean up any pre-existing TX/RX in the example scene
scene.remove("tx")
scene.remove("rx")

# --- OFDM / NR-ish parameters -------------------------------------------------
TTI = 10
num_ofdm_symbols_per_TTI = 28
num_ofdm_symbols = TTI * num_ofdm_symbols_per_TTI
num_subcarriers = 4096
subcarrier_spacing = 30e3  # Hz

ofdm_symbol_duration = 1 / subcarrier_spacing
delay_resolution = ofdm_symbol_duration / num_subcarriers
doppler_resolution = subcarrier_spacing / num_ofdm_symbols

# Optional overall bandwidth (kept commented as in the photo)
# scene.bandwidth = 100 * 1e6  # 100 MHz

# --- Antenna array for all TXs ------------------------------------------------
scene.tx_array = PlanarArray(
    num_rows=8,
    num_cols=4,
    vertical_spacing=0.5,
    horizontal_spacing=0.5,
    pattern="tr38901",
    polarization="cross"
)

scene.rx_array = PlanarArray(num_rows=2,
                             num_cols=1,
                             vertical_spacing=0.5,
                             horizontal_spacing=0.5,
                             pattern="dipole",
                             polarization="cross")

# --- Create/Add one transmitter ----------------------------------------------
tx = Transmitter(
    name="tx",
    position=[8.5, 21, 27],
    display_radius=2
)
scene.add(tx)

# Set TX velocity
tx_velocity = [30, 0, 0]
scene.get("tx").velocity = tx_velocity

# --- Solvers ------------------------------------------------------------------
rm_solver = RadioMapSolver()
p_solver  = PathSolver()

# Configure radio map sampling region (from the screenshot)
rm = rm_solver(
    scene,
    max_depth=5,
    samples_per_tx=10**7,
    cell_size=(5, 5),
    center=[0, 0, 0],
    size=[400, 400],
    orientation=[0, 0, 0]
)

# --- Sample receiver positions ------------------------------------------------
# pos, cell_ids = rm.sample_positions(
#     num_pos=1,              # Number of random positions per receiver
#     metric="sinr",          # Metric used for constraints / TX association
#     min_val_db=-3,          # Minimum value for chosen metric
#     max_val_db=10000,       # Maximum value for chosen metric
#     min_dist=5,             # Min distance from transmitter
#     max_dist=200,           # Max distance from transmitter
#     tx_association=True,    # Choose positions associated with best TX
#     center_pos=False
# )



pos = np.array([[-59.9067, -67.074, 0]])
# Remove any existing receivers if present
for key in list(scene.receivers.keys()):
    scene.remove(str(key))


for pos_idx, rx_position in enumerate(np.squeeze(pos)):
    # Create a receiver
    rx = Receiver(
        name=f"rx_{pos_idx}",         # 인덱스로 이름 생성
        position=rx_position.tolist() if hasattr(rx_position, "tolist") else rx_position,
        display_radius=2
    )
    # Add receiver to the scene
    scene.add(rx)

time_data = []
for idx in range(10):
    start_time = time.time()
    paths = p_solver(scene=scene, max_depth=1, refraction=False)
    print(3)
    frequencies = subcarrier_frequencies(num_subcarriers, subcarrier_spacing)
    # Channel frequency response with time evolution
    h = paths.cfr(
        frequencies=frequencies,
        sampling_frequency=1 / ofdm_symbol_duration,
        num_time_steps=num_ofdm_symbols,
        normalize_delays=False,
        normalize=True,
        out_type="numpy"
    )

    end_time = time.time()
    runtime = end_time - start_time
    print(f" 코드 런타임: {runtime:.3f} 초")
    time_data.append(runtime)
print(f" 코드 평균 런타임: {runtime/10:.3f} 초")
