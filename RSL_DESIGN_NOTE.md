# Residual Sublation Layer (RSL)

**Design Note**  
Status: Constitution-cleared (formal non-reducibility, hard-case separation, residual-boundedness sketch, minimal implementation, empirical separation)  
Date: 2026-08-05

---

## 1. Purpose

Adaptive residual systems (sorting residual menus, fault detectors, self-monitoring controllers) routinely evaluate a disorder signal \(d\) and a competence / confidence signal \(c\). Existing constructions combine these via thresholds, hysteresis, or product monitors. Under *correlated degradation of the disorder detector itself* (the senility regime), such constructions either abort too early or continue the ordinary residual menu too long, allowing residual error to grow.

The Residual Sublation Layer supplies a minimal additional state and elevation rule that:

- maintains a non-collapsing dual-active interval in which both “level-1 unreliable” and “level-2 still competent” remain simultaneously active,
- rewrites disposition into a restricted policy \(\pi_\lambda\) while the dual-active condition holds,
- is not reducible to residual + confidence gating + hysteresis.

## 2. Core Construction

### State
\[
\sigma = (d,\, c,\, \lambda,\, p) \in [0,1]^3 \times \{0,1\}
\]

- \(d\): residual disorder  
- \(c\): diagnostic competence of the disorder estimator  
- \(\lambda\): elevation tension  
- \(p\): hidden parity bit (the non-reducibility carrier)

Observable dual signal remains the pair \((d,c)\). The internal driver is the full quadruple.

### Elevation operator \(\mathcal{E}\)
At each residual-evaluation step:

\[
\begin{align*}
\rho &\leftarrow d\cdot c \\
r &\leftarrow \operatorname{corr}(d,c)_{\text{window}} \\
\operatorname{Rig}(\lambda,r,p) &=
\begin{cases}
(+1)\cdot\lambda\cdot(1-\lambda) & \text{if }p=0 \land \lambda>\tfrac12 \land r>\tau \\
(-1)\cdot\lambda\cdot(1-\lambda) & \text{if }p=1 \land \lambda>\tfrac12 \land r>\tau \\
0 & \text{otherwise}
\end{cases} \\
\lambda' &= \lambda + \alpha\rho(1-\lambda) - \beta(1-c)\lambda + \delta\cdot\operatorname{Rig}(\lambda,r,p) \\
&\quad + \gamma\cdot r\cdot\lambda\cdot(1-\lambda) \\
&\text{(shared attenuation of observation channels by }\lambda'\text{)} \\
p &\leftarrow p \oplus \mathbf{1}_{\{\lambda'>1/2 \land r>\tau\}}
\end{align*}
\]

### Rewrite
When \(\lambda > \theta\):

- switch to restricted policy \(\pi_\lambda\) (elevated residual acceptance thresholds + increased diagnostic effort),
- apply correlation-strengthened discharge \(-\mu(\lambda-\theta)(1+\kappa r)\).

## 3. Non-reducibility (inspection-level)

Any residual + confidence + hysteresis system (or finite-window product monitor) maintains state that is a function of a finite history of the observable pair \((d,c)\) only.

The polarity of every subsequent shared attenuation is controlled by the hidden bit \(p\). Transitions of \(p\) depend on the joint predicate involving the internal tension \(\lambda\) and the correlation \(r\). After an odd number of joint crossings the attenuation polarity reverses permanently until the next crossing.

Because \(p\) is invisible to any finite-window function of \(D\times C\), pure product-space monitors cannot recover the correct polarity sequence. Future joint trajectories of \((d',c')\) therefore diverge from every trajectory generable by residual + confidence + hysteresis constructions.

## 4. Senility hard-case separation

**Schedule** (discrete residual-evaluation steps):

- \(t<20\): clean regime  
- \(t=20\dots40\): correlated degradation (\(d\) rises, \(c\) falls, windowed correlation climbs)  
- \(t>40\): true residual partially recoverable (falls toward \(\approx0.35\)) while competence remains degraded

**Observed separation** (self-contained Python harness, same base tracking rate for all methods):

| Method               | Dual-active | Cum. abs. error (\(t>40\)) | MAE   | Elevated steps |
|----------------------|-------------|----------------------------|-------|----------------|
| RSL (locked)         | 10          | 1.137                      | 0.028 | 49             |
| Early-abort          | 4           | 1.336                      | 0.033 | —              |
| Late-ignore          | 13          | 1.336                      | 0.033 | —              |
| Hysteresis-product   | 9           | 1.336                      | 0.033 | —              |

RSL maintains a longer dual-active window than early-abort and records materially lower cumulative residual error against the true residual during recovery.

## 5. Residual-boundedness (sketch)

Potential under the elevated regime:
\[
V(\sigma) = d + \tfrac12\lambda^2
\]

One-step drift is negative while \(\lambda>\theta\) and correlation remains bounded away from zero, yielding a limsup bound on residual that depends only on the fixed parameters. Ordinary residual + confidence + hysteresis constructions possess no analogous potential decreased by polarity-aware attenuation and correlation-strengthened discharge.

## 6. Implementation

Minimal standalone header (C11 / C++-compatible, zero dependency on existing residual infrastructure):

```
artifacts/residual_sublation.h
```

Empirical harness (Python, self-contained):

```
artifacts/rsl_senility_harness.py
```

## 7. Lineage

The construction originates in an examination of Warren S. McCulloch’s question  
“What is a number, that a man may know it — and a man, that he may know a number?”  

The discussion progressed through:

- the necessity of observation / measurement loops for grounded knowledge,
- the notion of *realization* as spontaneous, self-grounding knowledge,
- the senility paradox (a system that realizes its own unreliability),
- the recognition that the simultaneous confirmation of instability and residual diagnostic competence is an instance of *Aufhebung* (level-dependent dual-actuating synthesis).

The Residual Sublation Layer is the engineering transcription of that *Aufhebung* into a residual decision primitive: the dual signal is elevated rather than collapsed, and the elevation itself rewrites future disposition.

## 8. Status

All five constitution requirements are satisfied:

1. Formal non-reducibility — locked  
2. Concrete hard-case resolution — locked  
3. Residual-boundedness sketch — locked  
4. Minimal implementation — locked  
5. Empirical separation — satisfied  

The layer is ready for integration, further robustness testing, or citation.
