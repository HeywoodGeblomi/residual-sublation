#!/usr/bin/env python3
"""
dcl_harness.py — Dynamic Commitment Layer
Realistic residual scenario (plant + progressive sensor bias + polarity disturbance)
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple

# ----------------------------------------------------------------------
# DCL core (v0.2.1 polarity-aware)
# ----------------------------------------------------------------------
@dataclass
class DCLParams:
    alpha: float = 0.25
    beta: float = 0.08
    gamma: float = 0.30
    delta: float = 0.55
    eta: float = 0.10
    mu: float = 0.08
    kappa: float = 1.2
    tau: float = 0.20
    theta: float = 0.35

@dataclass
class DCLState:
    d: float = 0.0
    c: float = 1.0
    lambda_: float = 0.0
    chi: int = 0

def dcl_init() -> DCLState:
    return DCLState()

def dcl_step(s: DCLState, par: DCLParams, r_fresh: float, k_fresh: float,
             r_corr: float, force_chi: int = None):
    rho = s.d * s.c
    rigidity = 0.0
    if s.lambda_ > 0.4 and r_corr > par.tau:
        sign = 1.0 if s.chi == 0 else -1.0
        rigidity = sign * s.lambda_ * (1.0 - s.lambda_)

    lambda_new = (
        s.lambda_
        + par.alpha * rho * (1.0 - s.lambda_)
        - par.beta * (1.0 - s.c) * s.lambda_
        + par.delta * rigidity
        + par.gamma * r_corr * (0.6 - s.lambda_)
    )
    lambda_new = max(0.0, min(1.0, lambda_new))

    att = 1.0 - par.eta * lambda_new
    pol = 1.0 if s.chi == 0 else -1.0
    s.d = s.d * att + (1.0 - att) * r_fresh + 0.12 * pol * max(rigidity, 0.05) * s.lambda_
    s.d = float(np.clip(s.d, 0.0, 1.0))
    s.c = s.c * att + (1.0 - att) * k_fresh
    s.c = float(np.clip(s.c, 0.05, 1.0))

    if force_chi is None:
        if lambda_new > 0.45 and r_corr > par.tau:
            s.chi ^= 1
    else:
        s.chi = force_chi

    s.lambda_ = lambda_new

def dcl_commit(s: DCLState, par: DCLParams, r_corr: float) -> bool:
    if s.lambda_ <= par.theta:
        return False
    discharge = par.mu * (s.lambda_ - par.theta) * (1.0 + par.kappa * r_corr)
    s.lambda_ = max(0.0, s.lambda_ - discharge)
    return True

# ----------------------------------------------------------------------
# Realistic residual scenario
# ----------------------------------------------------------------------
def realistic_residual_scenario(T: int = 150, seed: int = 42
                               ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Scalar plant + progressive sensor bias + intermittent polarity disturbance.
    Returns the three signals expected by DCL: d, c, r_corr.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(T)

    # Plant
    a = 0.92
    x = np.zeros(T)
    for i in range(1, T):
        x[i] = a * x[i-1] + rng.normal(0, 0.01)

    # Progressive sensor bias (diagnostic degradation)
    bias = 0.004 * t

    # Intermittent polarity flips of an additive disturbance
    true_pol = np.zeros(T, dtype=int)
    pol = 0
    flip_times = [40, 70, 100, 130]
    for i in range(1, T):
        if i in flip_times:
            pol ^= 1
        true_pol[i] = pol
    disturb = 0.25 * (2 * true_pol - 1) * (t > 30)

    # Measurement
    y = x + bias + disturb + rng.normal(0, 0.05, T)

    # Simple residual generator (one-step predictor)
    xhat = np.zeros(T)
    residual = np.zeros(T)
    for i in range(1, T):
        xhat[i] = a * xhat[i-1]
        residual[i] = y[i] - xhat[i]
        xhat[i] = 0.7 * xhat[i] + 0.3 * y[i]

    # Visible signals for DCL
    d = np.clip(np.abs(residual) / 1.5, 0.0, 1.0)
    c = np.clip(1.0 - 0.7 * (bias / (bias[-1] + 1e-8)) + rng.normal(0, 0.02, T), 0.05, 1.0)
    r_corr = np.clip(
        0.15 + 0.55 * np.abs(np.gradient(residual)) * 5.0
        + 0.40 * np.isin(t, flip_times).astype(float),
        0.0, 1.0
    )

    return d, c, r_corr

# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------
def run_monitor(d_in, c_in, r_corr, freeze_chi: bool = False):
    par = DCLParams()
    s = dcl_init()
    d_out = []
    flips = 0
    for i in range(len(d_in)):
        prev = s.chi
        force = 0 if freeze_chi else None
        dcl_step(s, par, d_in[i], c_in[i], r_corr[i], force_chi=force)
        dcl_commit(s, par, r_corr[i])
        if s.chi != prev:
            flips += 1
        d_out.append(s.d)
    return np.array(d_out), flips

def evaluate_divergence(d_full, d_abl, start: int = 50):
    div = np.abs(d_full[start:] - d_abl[start:])
    return float(np.sum(div)), float(np.mean(div))

def multi_seed_realistic(n_seeds: int = 8, T: int = 150):
    divs = []
    flips_list = []
    print("=" * 64)
    print("Realistic Residual Scenario — full-χ vs frozen-χ")
    print("=" * 64)
    for seed in range(n_seeds):
        d_in, c_in, r_corr = realistic_residual_scenario(T, seed)
        d_full, flips = run_monitor(d_in, c_in, r_corr, freeze_chi=False)
        d_abl, _     = run_monitor(d_in, c_in, r_corr, freeze_chi=True)
        cum_div, mae_div = evaluate_divergence(d_full, d_abl)
        divs.append(cum_div)
        flips_list.append(flips)
        print(f"Seed {seed:2d}: flips={flips}, cum_div={cum_div:7.3f}, mae_div={mae_div:.4f}")
    arr = np.array(divs)
    print("-" * 64)
    print(f"Mean cum divergence : {arr.mean():.3f} ± {arr.std():.3f}")
    print(f"Mean flips          : {np.mean(flips_list):.1f}")
    print("=" * 64)
    return arr

if __name__ == "__main__":
    multi_seed_realistic()