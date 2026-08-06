# Dynamic Commitment Layer (DCL)

**Design Note — v0.2.0 (surgical rewrite)**  
Status: Core claim locked. Implementation rewrite complete.  
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

## 4. Non-Reducibility

Any residual + confidence + hysteresis construction (or finite-window product monitor) maintains state that is a function of a finite history of the observable pair ((d,c)) only.

The value of χ controls both the polarity and the timing of subsequent commitment acts. After an odd number of commitment transitions, the future trajectory of the joint process diverges from every trajectory generable by a pure function of the observables.

Because χ is invisible and its transitions depend on the internal tension λ jointly with the visible signals, the information gap is permanent. The joint process (d, c, λ, χ) is therefore non-reducible to any function of the observables alone.

## 5. Operational Skeleton

* `dcl_init` — initialise visible state, set χ = 0, λ = 0.  
* `dcl_step` — update commitment tension; execute a commitment act (possible transition of χ) when the joint condition is met; apply the consequences of the current commitment to the observation channels.  
* `dcl_commit` — when commitment tension exceeds threshold, enforce the committed disposition and discharge tension.

Control flow remains minimal. The meaning of every transition has been re-aimed at the three roles.

## 6. Historical Note

This module was previously released as the Residual Sublation Layer (v0.1.0). The surgical rewrite retains the repository, the header-only C implementation style, and the hidden-variable DNA while discarding the elevation/sublation framing in favour of explicit dynamic commitment.
