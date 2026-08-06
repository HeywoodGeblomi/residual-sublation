# Dynamic Commitment Layer (DCL)

**Design Note — v0.2.1**  
Status: Core claim formalized. Empirical ablation + literature + limitations added.  
Previous identity: Residual Sublation Layer (historical).

## 1. Core Claim

There exist residual-diagnostic processes whose correct long-horizon behavior is impossible without a dynamic hidden variable that simultaneously:

1. stores memory the visible system is structurally forbidden to retain,  
2. collapses ambiguity by selecting among multiple futures consistent with the observations, and  
3. maintains an internal model of the process.

Once this variable is admitted, the joint process becomes well-posed.  
Any monitor limited to the visible residual and competence signals is information-theoretically incomplete.

The Dynamic Commitment Layer supplies that variable explicitly and makes its necessity legible.

## 2. State

```c
typedef struct {
    double d;       /* visible residual disorder           [0,1] */
    double c;       /* visible diagnostic competence       [0,1] */
    double lambda;  /* commitment tension                  [0,1] */
    int    chi;     /* dynamic commitment variable χ       0/1  */
} dcl_state_t;
```

* (d, c) — the only observables available to any external monitor.  
* λ — commitment tension (determines when a commitment act is forced).  
* χ — the hidden commitment variable. Its transitions are commitment acts.

## 3. Three Roles of χ

| Role | Function |
|------|----------|
| **B – Forbidden Memory** | χ retains information that the visible pair ((d,c)) is structurally incapable of carrying forward. |
| **C – Future Selection** | When multiple futures remain consistent with the observations, a transition of χ selects one. |
| **D – Internal Model** | χ functions as a minimal internal predictor / state estimate of the residual process. |

These three roles are executed by the same bit. The non-reducibility result rests on the fact that no function of finite windows of ((d,c)) can perform all three simultaneously.

## 4. Non-Reducibility (Formalized)

### 4.1 Class of Processes

Consider residual-diagnostic processes of the following form. At each discrete time \( t \):

- Visible signals: \( (d_t, c_t) \in [0,1]^2 \).
- Hidden commitment state: \( \chi_t \in \{0,1\} \).
- Commitment tension: \( \lambda_t \in [0,1] \).
- Dynamics: \( \lambda_{t+1} = f(\lambda_t, d_t, c_t, r_t^{\text{corr}}, \chi_t) \),  
  \( \chi_{t+1} = \chi_t \oplus \mathbf{1}_{\{\lambda_{t+1}>0.5 \land r_t^{\text{corr}}>\tau\}} \),  
  and the observation update itself depends on the current \( \chi \) through a polarity/rigidity term (exactly as implemented in `dcl_step`).

The required long-horizon behavior is that the monitor must eventually adopt the correct restricted disposition after an odd number of commitment transitions; adopting the wrong polarity produces permanently elevated residual error.

### 4.2 Observable-Only Monitors

Any monitor restricted to the visible signals maintains a state that is a (possibly stochastic) function of a finite history window of length \( k < \infty \):

\[
s_{t+1} = g(s_t, d_t, c_t), \qquad \text{action}_t = h(s_t, d_t, c_t).
\]

Such a monitor is a finite-memory function of the observable pair only.

### 4.3 Concrete Counter-Example Process

Define a two-phase synthetic process (the “parity trap”):

- Phase 1 ( \( t = 0\dots T_1 \) ): Generate identical observable trajectories under both \( \chi=0 \) and \( \chi=1 \). The pair \( (d_t,c_t) \) and the correlation signal \( r_t^{\text{corr}} \) are statistically indistinguishable.
- At a critical instant \( T_1 \) a commitment-eligible event occurs ( \( \lambda \) crosses threshold and \( r^{\text{corr}} > \tau \) ). The true process flips \( \chi \).
- Phase 2 ( \( t > T_1 \) ): The correct polarity of the rigidity term is required. Using the wrong polarity produces a sustained positive bias in residual disorder of size \( \Delta > 0 \) that cannot be corrected by any subsequent observable-only action.

Because the observable histories up to \( T_1 \) are identical for both values of \( \chi \), every finite-memory function \( g,h \) produces the same internal state \( s_{T_1} \) and therefore the same (incorrect) polarity thereafter. Its trajectory therefore diverges permanently from the true process after the odd-numbered flip. The information gap is irreducible: no amount of post-processing of the visible window recovers the parity bit that was required at the critical instant.

### 4.4 Consequence

The joint process \( (d,c,\lambda,\chi) \) is non-reducible to any finite-memory function of the observables alone. The explicit dynamic variable \( \chi \) is necessary for well-posed long-horizon residual-diagnostic behavior under the defined class of processes.

## 5. Operational Skeleton

* `dcl_init` — initialise visible state, set χ = 0, λ = 0.  
* `dcl_step` — update commitment tension; execute a commitment act (possible transition of χ) when the joint condition is met; apply the consequences of the current commitment to the observation channels.  
* `dcl_commit` — when commitment tension exceeds threshold, enforce the committed disposition and discharge tension.

Control flow remains minimal. The meaning of every transition has been re-aimed at the three roles.

## 6. Historical Note

This module was previously released as the Residual Sublation Layer (v0.1.0). The surgical rewrite retains the repository, the header-only C implementation style, and the hidden-variable DNA while discarding the elevation/sublation framing in favour of explicit dynamic commitment.

## 7. Relation to Existing Work

Classic residual generation for fault detection and isolation relies on observers, parity equations, or Kalman/IMM filters (see, e.g., the observer-based residual literature). These methods recover state estimates from the visible signals under the assumption that the residual generator itself remains observable or that discrete modes can be tracked from the innovation sequence. The internal-model principle likewise supplies the dynamics needed to cancel known exogenous signals, but again assumes those dynamics are either known a priori or identifiable from the observables.

The present construction addresses a narrower but sharper regime: long-horizon residual monitoring under progressive diagnostic degradation, where the correct commitment polarity is information-theoretically invisible from any finite window of residual-disorder and competence signals. In that regime the hidden bit is not recoverable by any finite-memory observer or mode estimator that sees only \( (d,c) \). The contribution is therefore complementary: it isolates a concrete situation in which an explicit, non-reducible internal commitment variable is required.

## 8. Limitations and Applicability

- The current module is deliberately minimal (binary \( \chi \), scalar tension). Extension to richer discrete or continuous internal state is left open.
- Empirical support remains synthetic. Realistic residual scenarios (sensor degradation on physical plant data, multi-fault isolation) are required before strong claims of practical utility.
- The non-reducibility result is specific to the class of processes defined in §4; it does not claim that every residual-diagnostic problem needs a hidden commitment variable.
- No formal sample-complexity or regret analysis is provided.
