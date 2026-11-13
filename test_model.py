from dataclasses import replace
import numpy as np
import pytest
from model import Parameters, simulate


def test_adiabatic_matches_analytic():
    p = Parameters(conduction=False, radiation=False)
    r = simulate(p)
    expected = p.initial_k + p.absorbed_power*r['time_s']/(p.mass*p.specific_heat)
    np.testing.assert_allclose(r['temperature_k'], expected, rtol=1e-8)


def test_zero_absorption_and_no_losses():
    p = Parameters(loss_factor=0, conduction=False, radiation=False)
    assert p.absorbed_power == 0
    np.testing.assert_allclose(simulate(p)['temperature_k'], p.initial_k)


def test_energy_conservation_and_passivity():
    p = Parameters()
    r = simulate(p)
    assert 0 < p.absorbed_power < p.power*p.coupling
    assert np.max(np.abs(r['residual_j'])) < 1e-3
    assert p.initial_k < r['temperature_k'][-1]
    assert r['temperature_k'][-1] < p.initial_k+p.absorbed_power*p.duration_s/(p.mass*p.specific_heat)


def test_boundary_can_warm_sample():
    p = Parameters(power=0, initial_k=100, base_k=300, radiation=False)
    assert simulate(p)['temperature_k'][-1] > 100


def test_conduction_matches_exponential():
    p = Parameters(power=0, initial_k=500, radiation=False, conductivity=1)
    r = simulate(p)
    tau = p.mass*p.specific_heat/(p.conductivity*p.area/p.thickness)
    np.testing.assert_allclose(r['temperature_k'], p.base_k+(p.initial_k-p.base_k)*np.exp(-r['time_s']/tau),rtol=1e-7)


def test_invalid_inputs():
    for field,value in [('density',0),('loss_factor',-1),('coupling',2),('power',float('nan'))]:
        with pytest.raises(ValueError):
            simulate(replace(Parameters(), **{field:value}))


def test_streamlit_interaction():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file('app.py').run(timeout=30)
    assert not app.exception
    initial = app.metric[0].value
    next(x for x in app.number_input if x.label == 'Incident microwave power (W)').set_value(0.0)
    app.run()
    assert not app.exception
    assert app.metric[0].value != initial
    next(x for x in app.number_input if x.label == 'Dielectric loss factor ε″ (dimensionless)').set_value(0.0)
    app.run()
    assert not app.exception
    assert app.metric[1].value == '0.0 W'
