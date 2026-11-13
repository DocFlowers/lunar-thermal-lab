# Lunar Thermal Lab

A responsive Streamlit application for an illustrative lumped microwave heating model. Python 3.11 or newer recommended.

## Run on a computer

Open a terminal in this folder:

```sh
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 0.0.0.0
```

Open http://localhost:8501 on that computer. Keep the terminal running.

## Use from an iPhone

Python runs on a computer or hosting service; Safari provides the interface.

### Same Wi-Fi

1. Start the app on your computer using the command above.
2. Find the computer's private LAN IPv4 address in its network settings (for example 192.168.1.42).
3. Connect the iPhone to the same Wi-Fi and open `http://192.168.1.42:8501` in Safari, substituting the real address. `localhost` on the phone refers to the phone, not the computer.
4. If needed, allow Python/port 8501 through the computer's firewall for the private network. Guest Wi-Fi or client isolation can prevent access. Keep the computer awake.

This local service has no sign-in. Use it on a trusted network; do not forward your router's public port 8501.

### Hosted HTTPS link (works away from home)

1. Put `app.py`, `model.py`, and `requirements.txt` in a GitHub repository.
2. Sign in at https://share.streamlit.io and create an app from that repository, selecting `app.py` as the entrypoint. Follow the current hosting plan and repository-access prompts.
3. Open the assigned `https://…streamlit.app` link in Safari. Configure the hosting service's access settings for your intended audience.

No hosted URL is bundled with this project. A running cloud development environment is not a permanent iPhone host.

### Interaction

On a narrow screen, tap the sidebar arrow at the upper left to open experiment controls; close it to view the plots. Change density, heat capacity, conductivity, power, or ε″ and the plots recalculate automatically. Pinch/drag plot controls as supported by Plotly; tap legend entries to hide energy curves. Open the model tab for equations and assumptions. Download CSV histories and JSON settings from Export. Safari's Share menu can add the hosted link to your Home Screen.

## Model

`ρALcₚ dT/dt = P_abs − kA/L (T − T_base) − εσA(T⁴ − T_surroundings⁴)`

Switches can remove conduction or radiation. `P_abs = ηP [1 − exp(−2αL)]`; α is the field attenuation coefficient of a homogeneous nonmagnetic dielectric at the selected frequency. ε″ is a relative dielectric loss factor, not tan δ. A numerically stable equivalent expression for α avoids cancellation near zero loss. Geometry is a slab with top radiation, effective base conduction, and insulated sides. Negative boundary flux represents incoming heat. Energy is integrated alongside temperature using SciPy's Radau solver.

Assumptions: uniform temperature; constant illustrative material properties; single-pass microwave attenuation and a user-set coupling fraction; fixed base and surroundings temperatures; no convection, phase changes, sunlight, cavity field structure, or temperature feedback on dielectric properties. Conductivity is an effective thermal link, not a spatial solution. Diffusion time and penetration depth are displayed to help assess model limitations. Defaults are not a measured lunar dataset. High-temperature trajectories need temperature-dependent properties and phase changes; use this as an exploratory tool.

## Test

```sh
python -m pip install pytest
python -m pytest -q
```

Tests cover analytic adiabatic heating, exponential conductive cooling, zero absorption, warming from the base, energy conservation, invalid inputs, and live Streamlit widget recalculation.
