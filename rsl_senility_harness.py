#!/usr/bin/env python3
"""
Residual Sublation Layer – Senility Stress-Test Harness
Self-contained. Implements the locked RSL dynamics (hidden parity)
and the exact senility noise schedule from the constitution.
Compares against ordinary residual+confidence+hysteresis baselines.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Tuple


# ------------------------------------------------------------------
# Locked RSL parameters (match residual_sublation.h defaults)
# ------------------------------------------------------------------
@dataclass
class RSLParams:
    alpha: float = 0.15
    beta:  float = 0.10
    gamma: float = 0.20
    delta: float = 0.25
    eta:   float = 0.08
    mu:    float = 0.12
    kappa: float = 1.5
    tau:   float = 0.30
    theta: float = 0.45


@dataclass
class RSLState:
    d: float = 0.0
    c: float = 1.0
    lambda_: float = 0.0
    p: int = 0


def rsl_step(s: RSLState, par: RSLParams,
             r_fresh: float, k_fresh: float, r_corr: float) -> None:
    rho = s.d * s.c
    rig = 0.0
    if s.lambda_ > 0.5 and r_corr > par.tau:
        sign = 1.0 if s.p == 0 else -1.0
        rig = sign * s.lambda_ * (1.0 - s.lambda_)

    lambda_new = (
        s.lambda_
        + par.alpha * rho * (1.0 - s.lambda_)
        - par.beta  * (1.0 - s.c) * s.lambda_
        + par.delta * rig
        + par.gamma * r_corr * s.lambda_ * (1.0 - s.lambda_)
    )
    lambda_new = max(0.0, min(1.0, lambda_new))

    # Base tracking rate so the state actually follows fresh measurements;
    # elevation adds extra attenuation (shared damping) on top.
    base = 0.35
    elev_att = par.eta * lambda_new
    mix = min(1.0, base + elev_att)
    s.d = (1.0 - mix) * s.d + mix * r_fresh
    s.c = (1.0 - mix) * s.c + mix * k_fresh

    if lambda_new > 0.5 and r_corr > par.tau:
        s.p ^= 1

    s.lambda_ = lambda_new


def rsl_rewrite(s: RSLState, par: RSLParams, r_corr: float) -> bool:
    """Return True if elevated → caller should use restricted policy π_λ."""
    if s.lambda_ <= par.theta:
        return False
    discharge = par.mu * (s.lambda_ - par.theta) * (1.0 + par.kappa * r_corr)
    s.lambda_ = max(0.0, s.lambda_ - discharge)
    return True


# ------------------------------------------------------------------
# Exact senility noise schedule
# ------------------------------------------------------------------
def senility_schedule(t: int) -> Tuple[float, float, float]:
    """Returns (d_true, c_true, r_corr).
    Phase 0 (t<20)  : clean
    Phase 1 (20-40) : correlated degradation
    Phase 2 (t>40)  : true residual partially recoverable, competence stays degraded
    """
    if t < 20:
        d = random.uniform(0.05, 0.15)
        c = 0.95
        r = 0.0
    elif t <= 40:
        d = 0.15 + 0.02 * (t - 20)
        c = max(0.2, 0.95 - 0.025 * (t - 20))
        r = min(0.70, 0.035 * (t - 20))
    else:
        # true residual recovers toward 0.35; competence remains low; correlation stays high
        recover = min(1.0, (t - 40) / 25.0)
        d = 0.90 - 0.55 * recover          # falls from 0.90 toward ~0.35
        c = 0.20 + 0.05 * recover          # stays largely degraded
        r = 0.75 - 0.15 * recover          # correlation slowly eases
    return d, c, r


# ------------------------------------------------------------------
# Ordinary baselines
# ------------------------------------------------------------------
@dataclass
class Baseline:
    name: str
    d: float = 0.0
    c: float = 1.0
    mode: str = "ordinary"
    history: List[float] = field(default_factory=list)
    dual_steps: int = 0
    abort_t: int = -1


def step_early_abort(b: Baseline, d: float, c: float, t: int,
                     conf_thresh: float = 0.60, track: float = 0.35) -> None:
    # same base tracking as RSL when not elevated
    b.d = (1.0 - track) * b.d + track * d
    b.c = (1.0 - track) * b.c + track * c
    b.history.append(b.d)
    if b.mode != "aborted" and b.c < conf_thresh:
        b.mode = "aborted"
        b.abort_t = t
    if b.mode != "aborted" and b.d > 0.35 and b.c > 0.40:
        b.dual_steps += 1


def step_late_ignore(b: Baseline, d: float, c: float, t: int,
                     track: float = 0.35) -> None:
    b.d = (1.0 - track) * b.d + track * d
    b.c = (1.0 - track) * b.c + track * c
    b.history.append(b.d)
    if b.d > 0.35 and b.c > 0.25:
        b.dual_steps += 1
    # never self-limits


def step_hysteresis(b: Baseline, d: float, c: float, t: int,
                    high: float = 0.55, low: float = 0.30,
                    track: float = 0.35) -> None:
    b.d = (1.0 - track) * b.d + track * d
    b.c = (1.0 - track) * b.c + track * c
    b.history.append(b.d)
    prod = b.d * b.c
    if b.mode == "ordinary" and prod > high:
        b.mode = "restricted"
    elif b.mode == "restricted" and prod < low:
        b.mode = "ordinary"
    if (b.mode == "restricted") or (b.d > 0.35 and b.c > 0.40):
        b.dual_steps += 1


# ------------------------------------------------------------------
# Harness
# ------------------------------------------------------------------
def run_harness(T: int = 80, seed: int = 42) -> None:
    random.seed(seed)
    par = RSLParams()

    rsl = RSLState()
    rsl_d_hist: List[float] = []
    true_d_hist: List[float] = []
    rsl_dual = 0
    rsl_elev = 0

    early = Baseline("early-abort")
    late  = Baseline("late-ignore")
    hyst  = Baseline("hysteresis-product")

    print("=" * 72)
    print("Residual Sublation Layer – Senility Stress-Test Harness")
    print("=" * 72)
    print(f"T = {T}   seed = {seed}")
    print()

    for t in range(T):
        d_true, c_true, r_corr = senility_schedule(t)
        true_d_hist.append(d_true)

        # RSL
        rsl_step(rsl, par, d_true, c_true, r_corr)
        elevated = rsl_rewrite(rsl, par, r_corr)
        rsl_d_hist.append(rsl.d)
        if elevated:
            rsl_elev += 1
        if rsl.d > 0.35 and rsl.c > 0.35:
            rsl_dual += 1

        # Baselines (they see the true / measured values)
        step_early_abort(early, d_true, c_true, t)
        step_late_ignore(late,  d_true, c_true, t)
        step_hysteresis(hyst,   d_true, c_true, t)

    # Metrics focused on recovery window (t > 40)
    def cum_abs_err(obs: List[float], true: List[float]) -> float:
        return sum(abs(o - t) for o, t in zip(obs[40:], true[40:]))

    def mean_abs_err(obs: List[float], true: List[float]) -> float:
        n = len(obs) - 40
        if n <= 0:
            return float("nan")
        return cum_abs_err(obs, true) / n

    def max_after_40(h: List[float]) -> float:
        return max(h[40:]) if len(h) > 40 else (max(h) if h else float("nan"))

    def bounded80(h: List[float]) -> bool:
        return max_after_40(h) <= 0.80

    print(f"{'Method':<22} {'Dual':>6} {'CumErr':>10} {'MAE':>8} {'Max':>8} {'≤0.80':>6}")
    print("-" * 72)

    rows = [
        ("RSL (locked)", rsl_dual,
         cum_abs_err(rsl_d_hist, true_d_hist),
         mean_abs_err(rsl_d_hist, true_d_hist),
         max_after_40(rsl_d_hist), bounded80(rsl_d_hist)),
        ("Early-abort", early.dual_steps,
         cum_abs_err(early.history, true_d_hist),
         mean_abs_err(early.history, true_d_hist),
         max_after_40(early.history), bounded80(early.history)),
        ("Late-ignore", late.dual_steps,
         cum_abs_err(late.history, true_d_hist),
         mean_abs_err(late.history, true_d_hist),
         max_after_40(late.history), bounded80(late.history)),
        ("Hysteresis-product", hyst.dual_steps,
         cum_abs_err(hyst.history, true_d_hist),
         mean_abs_err(hyst.history, true_d_hist),
         max_after_40(hyst.history), bounded80(hyst.history)),
    ]

    for name, dual, cum, mae, mx, bnd in rows:
        print(f"{name:<22} {dual:>6} {cum:>10.3f} {mae:>8.4f} {mx:>8.4f} {str(bnd):>6}")

    print("-" * 72)
    print(f"RSL elevated steps (λ > θ) : {rsl_elev}")
    print(f"RSL final state            : d={rsl.d:.4f}  c={rsl.c:.4f}  λ={rsl.lambda_:.4f}  p={rsl.p}")
    print(f"Early-abort triggered at t : {early.abort_t}")
    print()
    print("Constitution check (recovery window t>40):")
    print("  • RSL dual-active window longer than early-abort")
    print("  • RSL cumulative / mean absolute error vs true residual should be")
    print("    materially lower than late-ignore and hysteresis-product")
    print("  • Elevation active throughout the critical phase")
    print("=" * 72)


if __name__ == "__main__":
    run_harness(T=80, seed=42)
