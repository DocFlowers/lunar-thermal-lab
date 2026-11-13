"""SI-unit lumped energy balance for an illustrative regolith slab."""
from dataclasses import dataclass, asdict
import math
import numpy as np
from scipy.integrate import solve_ivp

SIGMA = 5.670374419e-8
C = 299792458.0

@dataclass(frozen=True)
class Parameters:
    density: float = 1500
    specific_heat: float = 750
    conductivity: float = 0.02
    power: float = 1000
    loss_factor: float = 0.1
    relative_permittivity: float = 3
    frequency_ghz: float = 2.45
    coupling: float = 0.7
    area: float = 0.01
    thickness: float = 0.05
    emissivity: float = 0.9
    initial_k: float = 250
    base_k: float = 250
    surroundings_k: float = 100
    duration_s: float = 1800
    radiation: bool = True
    conduction: bool = True

    def validate(self):
        for key, value in asdict(self).items():
            if not isinstance(value, bool) and not math.isfinite(value):
                raise ValueError(f'{key} must be finite')
        for key in ('density','specific_heat','relative_permittivity','frequency_ghz','area','thickness','initial_k','base_k','surroundings_k','duration_s'):
            if getattr(self, key) <= 0:
                raise ValueError(f'{key} must be positive')
        if min(self.conductivity, self.power, self.loss_factor) < 0:
            raise ValueError('Conductivity, power and loss factor must be nonnegative')
        if not 0 <= self.coupling <= 1 or not 0 <= self.emissivity <= 1:
            raise ValueError('Coupling and emissivity must lie in [0,1]')

    @property
    def mass(self):
        return self.density * self.area * self.thickness

    @property
    def attenuation(self):
        # Stable exact attenuation for a nonmagnetic homogeneous lossy dielectric.
        er, ei = self.relative_permittivity, self.loss_factor
        root = math.hypot(er, ei)
        return 2 * math.pi * self.frequency_ghz * 1e9 / C * ei / math.sqrt(2 * (root + er))

    @property
    def absorbed_power(self):
        return self.power * self.coupling * (-math.expm1(-2*self.attenuation*self.thickness))


def simulate(p: Parameters, points=601):
    p.validate()
    if points < 2:
        raise ValueError('At least two output points required')
    capacity = p.mass * p.specific_heat
    def rhs(t, state):
        temp = state[0]
        cond = p.conductivity*p.area/p.thickness*(temp-p.base_k) if p.conduction else 0
        rad = p.emissivity*SIGMA*p.area*(temp**4-p.surroundings_k**4) if p.radiation else 0
        return [(p.absorbed_power-cond-rad)/capacity, cond, rad]
    sol = solve_ivp(rhs, (0,p.duration_s), [p.initial_k,0,0], method='Radau',
                    t_eval=np.linspace(0,p.duration_s,points), rtol=1e-8, atol=[1e-7,1e-5,1e-5])
    if not sol.success:
        raise RuntimeError(sol.message)
    temp, conducted, radiated = sol.y
    absorbed = p.absorbed_power*sol.t
    stored = capacity*(temp-p.initial_k)
    return dict(time_s=sol.t, temperature_k=temp, absorbed_j=absorbed, stored_j=stored,
                conducted_j=conducted, radiated_j=radiated,
                residual_j=absorbed-stored-conducted-radiated)
