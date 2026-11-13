import json
from dataclasses import asdict
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import Parameters, simulate

st.set_page_config(page_title='Lunar Thermal Lab', page_icon='🌒', layout='wide')
st.markdown('''<style>.stApp {background: #0b1220;} h1,h2,h3 {color:#e9f1ff;} [data-testid="stMetric"] {background:#162236;padding:16px;border-radius:12px;} </style>''', unsafe_allow_html=True)
st.caption('LUNAR THERMAL LAB  /  MICROWAVE HEATING')
st.title('Explore heat beneath the lunar surface')
st.write('Adjust a regolith slab and microwave source to explore an illustrative, uniform-temperature energy balance.')
with st.sidebar:
    st.header('Experiment controls')
    st.caption('Changes recalculate automatically. All inputs use SI units.')
    st.subheader('Regolith')
    density = st.number_input('Bulk density (kg/m³)', 100., 5000., 1500., 50.)
    cp = st.number_input('Specific heat capacity (J/kg/K)', 10., 3000., 750., 25.)
    k = st.number_input('Thermal conductivity (W/m/K)', 0., 10., 0.02, 0.01, format='%.3f')
    loss = st.number_input('Dielectric loss factor ε″ (dimensionless)', 0., 10., 0.1, 0.01, format='%.3f')
    er = st.number_input('Relative permittivity ε′', 1., 30., 3., 0.1)
    st.subheader('Microwave source')
    power = st.number_input('Incident microwave power (W)', 0., 10000., 1000., 50.)
    frequency = st.number_input('Frequency (GHz)', 0.1, 30., 2.45, 0.05)
    coupling = st.slider('Coupling fraction', 0., 1., 0.7, 0.01, help='Fraction of source power entering the slab; includes reflection and applicator losses.')
    st.subheader('Geometry & boundaries')
    area = st.number_input('Slab area (m²)', 0.001, 1., 0.01, 0.001, format='%.3f')
    thickness = st.number_input('Slab thickness (m)', 0.001, 1., 0.05, 0.005, format='%.3f')
    initial = st.number_input('Initial temperature (K)', 1., 2000., 250., 10.)
    duration = st.slider('Heating duration (minutes)', 1, 120, 30)
    conduction = st.checkbox('Conduct heat to a fixed-temperature base', True)
    base = st.number_input('Base temperature (K)', 1., 2000., 250., 10., disabled=not conduction)
    radiation = st.checkbox('Radiate from the top surface', True)
    emissivity = st.slider('Emissivity', 0., 1., 0.9, 0.01, disabled=not radiation)
    surroundings = st.number_input('Radiative surroundings (K)', 1., 2000., 100., 10., disabled=not radiation)
p = Parameters(density=density, specific_heat=cp, conductivity=k, power=power, loss_factor=loss,
               relative_permittivity=er, frequency_ghz=frequency, coupling=coupling, area=area,
               thickness=thickness, initial_k=initial, base_k=base, surroundings_k=surroundings,
               duration_s=duration*60, conduction=conduction, radiation=radiation, emissivity=emissivity)
try:
    r = simulate(p)
except (ValueError, RuntimeError) as e:
    st.error(str(e))
    st.stop()
a,b,c = st.columns(3)
a.metric('Final temperature', f'{r["temperature_k"][-1]:,.1f} K', f'{r["temperature_k"][-1]-initial:+,.1f} K')
b.metric('Absorbed microwave power', f'{p.absorbed_power:,.1f} W', f'{100*p.absorbed_power/power if power else 0:.1f}% of source', delta_color='off')
c.metric('Sample mass', f'{p.mass:.3f} kg')
fig=go.Figure(go.Scatter(x=r['time_s']/60,y=r['temperature_k'],name='Regolith',line=dict(color='#f6b55b',width=3),fill='tozeroy',fillcolor='rgba(246,181,91,0.08)'))
fig.update_layout(template='plotly_dark',xaxis_title='Time (minutes)',yaxis_title='Temperature (K)',height=420,margin=dict(l=10,r=10,t=15,b=10),paper_bgcolor='#0b1220',plot_bgcolor='#0b1220')
st.plotly_chart(fig, width='stretch')
if np.max(r['temperature_k']) > 1000:
    st.warning('The trajectory exceeds 1000 K. Constant properties become especially unreliable; this model does not include sintering, melting, or thermal runaway.')
diffusion = density*cp*thickness**2/k if k else float('inf')
st.caption(f'Through-thickness diffusion time L²ρcₚ/k: {diffusion/60:,.1f} min. Compare with the {duration} min run; a long diffusion time suggests substantial internal temperature gradients.')
tab1,tab2,tab3 = st.tabs(['Energy budget','Model & assumptions','Export'])
with tab1:
    fig2=go.Figure()
    for name,label in [('absorbed_j','Absorbed'),('stored_j','Stored heat'),('conducted_j','To base'),('radiated_j','Radiated')]:
        fig2.add_scatter(x=r['time_s']/60,y=r[name]/1000,name=label)
    fig2.update_layout(template='plotly_dark',xaxis_title='Time (minutes)',yaxis_title='Cumulative energy (kJ)',height=350,legend=dict(orientation='h'),margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig2,width='stretch')
    st.write(f'Maximum numerical energy imbalance: {np.max(np.abs(r["residual_j"])):.3g} J. Negative boundary energy means heat entered the sample.')
with tab2:
    st.latex(r'\rho A L c_p\frac{dT}{dt}=P_{\rm abs}-\frac{kA}{L}(T-T_b)-\epsilon\sigma A(T^4-T_{\rm surr}^4)')
    st.latex(r'P_{\rm abs}=\eta P(1-e^{-2\alpha L}),\quad \alpha=\frac{2\pi f}{c}\sqrt{\frac{\sqrt{\epsilon^{\prime 2}+\epsilon^{\prime\prime 2}}-\epsilon^\prime}{2}}')
    st.markdown('''- **Uniform slab temperature:** one thermal node; no depth or lateral gradients are resolved. Conductivity defines an effective thermal link of length L to a fixed-temperature base, not a solved temperature profile.
- **Constant properties:** bulk density, heat capacity, conductivity, complex permittivity, and emissivity are fixed. Defaults are illustrative, not calibrated lunar measurements.
- **Microwaves:** homogeneous, nonmagnetic dielectric; ε″ is relative permittivity's loss component, not loss tangent (tan δ = ε″/ε′). Single-pass attenuation of power, with α the field attenuation coefficient. Coupling η represents entry losses. Transmitted power leaves the sample; no cavity modes, interference, or temperature-dependent absorption.
- **Boundaries:** top radiates to a fixed effective surroundings temperature with view factor one; base conducts over L. Sides are insulated. No convection in vacuum, sunlight, or other heat sources.
- **No phase changes:** no latent heat, sintering, outgassing, material transport, or chemistry. High-temperature predictions require a richer model and measured properties.
- **Numerics:** adaptive implicit Radau integration; cumulative boundary energies are integrated with temperature. Energy residual = absorbed − stored − conducted − radiated. Temperatures use kelvin throughout.''')
    st.info('This is an exploratory model, not a validated microwave applicator or lunar process design tool. A short heating time relative to the diffusion time or shallow microwave penetration can invalidate the uniform-temperature approximation.')
    st.write(f'Power penetration depth 1/(2α): {1/(2*p.attenuation):.4g} m' if p.attenuation else 'Power penetration depth: infinite (zero dielectric absorption).')
with tab3:
    st.download_button('Download time history (CSV)',pd.DataFrame(r).to_csv(index=False),'regolith_history.csv','text/csv')
    st.download_button('Download model inputs (JSON)',json.dumps(asdict(p),indent=2),'regolith_inputs.json','application/json')
    st.caption('CSV includes temperatures, cumulative energies, and energy residuals. JSON records all inputs in SI units except frequency in GHz.')
