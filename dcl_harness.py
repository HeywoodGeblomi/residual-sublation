#!/usr/bin/env python3
"""
dcl_harness.py — Empirical stress test for the Dynamic Commitment Layer (DCL) v0.2.1

Tests the claim that an explicit dynamic hidden variable χ
(performing forbidden memory + future selection + internal model)
produces measurably better residual-diagnostic behavior under
degradation than monitors limited to the visible signals alone,
and than an ablated DCL that is denied transitions of χ.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple

@dataclass
class DCLParams:
    alpha: float = 0.15
    beta: float = 0.10
    gamma: float = 0.20
    delta: float = 0.25
    eta: float = 0.08
    mu: float = 0.12
    kappa: float = 1.5
    tau: float = 0.30
    theta: float = 0.45

@dataclass
class DCLState:
    d: float = 0.0
    c: float = 1.0
    lambda_: float = 0.0
    chi: int = 0

def dcl_init() -> DCLState:
    return DCLState()

def dcl_step(s: DCLState, par: DCLParams, r_fresh: float, k_fresh: float, r_corr: float, allow_flip: bool = True):
    rho = s.d * s.c
    rigidity = 0.0

    if s.lambda_ > 0.5 and r_corr > par.tau:
        sign = 1.0 if s.chi == 0 else -1.0
        rigidity = sign * s.lambda_ * (1.0 - s.lambda_)

    lambda_new = (
        s.lambda_
        + par.alpha * rho * (1.0 - s.lambda_)
        - par.beta * (1.0 - s.c) * s.lambda_
        + par.delta * rigidity
        + par.gamma * r_corr * s.lambda_ * (1.0 - s.lambda_)
    )
    lambda_new = max(0.0, min(1.0, lambda_new))

    att = 1.0 - par.eta * lambda_new
    s.d = s.d * att + (1.0 - att) * r_fresh
    s.c = s.c * att + (1.0 - att) * k_fresh

    if allow_flip and lambda_new > 0.5 and r_corr > par.tau:
        s.chi ^= 1

    s.lambda_ = lambda_new

def dcl_commit(s: DCLState, par: DCLParams, r_corr: float) -> bool:
    if s.lambda_ <= par.theta:
        return False
    discharge = par.mu * (s.lambda_ - par.theta) * (1.0 + par.kappa * r_corr)
    s.lambda_ = max(0.0, s.lambda_ - discharge)
    return True

def senility_schedule(T: int = 80, seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.arange(T)

    d_true = 0.15 + 0.55 * (1 / (1 + np.exp(-(t - 25) / 4))) - 0.25 * (1 / (1 + np.exp(-(t - 55) / 5)))
    d_true = np.clip(d_true + rng.normal(0, 0.03, T), 0, 1)

    c_true = 0.95 - 0.55 * (1 / (1 + np.exp(-(t - 22) / 3.5))) + 0.25 * (1 / (1 + np.exp(-(t - 58) / 4)))
    c_true = np.clip(c_true + rng.normal(0, 0.025, T), 0.05, 1)

    r_corr = np.clip(0.2 + 0.6 * np.abs(np.gradient(d_true)) * np.abs(np.gradient(c_true)) * 8, 0, 1)
    r_corr += rng.normal(0, 0.04, T)
    r_corr = np.clip(r_corr, 0, 1)

    return d_true, c_true, r_corr

def run_early_abort(d_true, c_true, threshold=0.45):
    d_obs = []
    aborted = False
    d = 0.0
    for dt, ct in zip(d_true, c_true):
        if not aborted:
            d = 0.85 * d + 0.15 * dt
            if ct < threshold:
                aborted = True
        d_obs.append(d)
    return np.array(d_obs)

def run_late_ignore(d_true, c_true):
    d = 0.0
    d_obs = []
    for dt, ct in zip(d_true, c_true):
        d = 0.85 * d + 0.15 * dt
        d_obs.append(d)
    return np.array(d_obs)

def run_hysteresis_product(d_true, c_true, low=0.25, high=0.55):
    d = 0.0
    mode = "normal"
    d_obs = []
    for dt, ct in zip(d_true, c_true):
        prod = dt * ct
        if mode == "normal" and prod < low:
            mode = "restricted"
        elif mode == "restricted" and prod > high:
            mode = "normal"
        alpha = 0.10 if mode == "restricted" else 0.18
        d = (1 - alpha) * d + alpha * dt
        d_obs.append(d)
    return np.array(d_obs)

def run_dcl(d_true, c_true, r_corr, par=None, allow_flip=True):
    if par is None:
        par = DCLParams()
    s = dcl_init()
    d_obs = []
    commits = 0
    for dt, ct, rc in zip(d_true, c_true, r_corr):
        dcl_step(s, par, dt, ct, rc, allow_flip=allow_flip)
        if dcl_commit(s, par, rc):
            commits += 1
        d_obs.append(s.d)
    return np.array(d_obs), commits, s.chi

def evaluate(d_obs, d_true, start=40):
    err = np.abs(d_obs[start:] - d_true[start:])
    return {
        "cum_abs_err": float(np.sum(err)),
        "mae": float(np.mean(err)),
        "max_d": float(np.max(d_obs[start:])),
    }

def main():
    T = 80
    seeds = [42, 43, 44, 45, 46]

    results = {
        "DCL (with χ)": [],
        "DCL ablated (χ frozen)": [],
        "Early-abort": [],
        "Late-ignore": [],
        "Hysteresis-product": [],
    }

    for seed in seeds:
        d_true, c_true, r_corr = senility_schedule(T, seed=seed)

        dcl_obs, commits, final_chi = run_dcl(d_true, c_true, r_corr, allow_flip=True)
        ablated_obs, _, _ = run_dcl(d_true, c_true, r_corr, allow_flip=False)
        early_obs = run_early_abort(d_true, c_true)
        late_obs = run_late_ignore(d_true, c_true)
        hyst_obs = run_hysteresis_product(d_true, c_true)

        results["DCL (with χ)"].append(evaluate(dcl_obs, d_true)["cum_abs_err"])
        results["DCL ablated (χ frozen)"].append(evaluate(ablated_obs, d_true)["cum_abs_err"])
        results["Early-abort"].append(evaluate(early_obs, d_true)["cum_abs_err"])
        results["Late-ignore"].append(evaluate(late_obs, d_true)["cum_abs_err"])
        results["Hysteresis-product"].append(evaluate(hyst_obs, d_true)["cum_abs_err"])

    print("=" * 72)
    print("Dynamic Commitment Layer — Empirical Harness (v0.2.1)")
    print("Mean ± std cumulative absolute error after t=40 (5 seeds)")
    print("=" * 72)
    print(f"{'Method':<28} {'Mean CumAbsErr':>14} {'Std':>8}")
    print("-" * 72)
    for name, vals in results.items():
        mean = np.mean(vals)
        std = np.std(vals)
        print(f"{name:<28} {mean:14.3f} {std:8.3f}")
    print("-" * 72)
    print()
    print("Interpretation:")
    print("  Lower cumulative error under degradation indicates that the")
    print("  dynamic hidden variable χ is doing useful work that pure")
    print("  visible-signal monitors (and the ablated DCL) cannot replicate.")
    print("=" * 72)

if __name__ == "__main__":
    main()
