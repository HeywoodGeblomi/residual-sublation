# Residual Sublation Layer (RSL)

A small, general-purpose decision module for adaptive residual handling.

It treats residual disorder and the system’s own diagnostic competence as a dual signal, maintains a hidden polarity state, and elevates into a restricted disposition when both signals co-occur under correlation. The elevation is designed to be non-reducible to ordinary residual + confidence + hysteresis monitors.

## Status (v0.1.0)

- Formal non-reducibility argument (hidden parity)
- Explicit senility hard-case separation
- Sketch-level residual potential under elevation
- Minimal C11/C++ header
- Empirical harness showing dual-active window + lower cumulative residual error on a recoverable senility schedule

This is a research-grade module, not a production drop-in replacement for existing residual logic.

## Files

| File | Description |
|------|-------------|
| `residual_sublation.h` | Standalone header (init / step / rewrite) |
| `rsl_senility_harness.py` | Self-contained empirical stress test |
| `RSL_DESIGN_NOTE.md` | Design rationale, non-reducibility argument, lineage |

## Quick use

```c
#include "residual_sublation.h"

rsl_state_t st;
rsl_init(&st);

rsl_step(&st, &RSL_DEFAULTS, r_fresh, k_fresh, r_corr);
if (rsl_rewrite(&st, &RSL_DEFAULTS, r_corr)) {
    /* restricted policy π_λ */
} else {
    /* ordinary residual menu */
}
```

## Credit

Inspired by and builds upon residual and adaptive-sorting infrastructure developed by Heywood Geblomi (Photonic residual menu, residual_automaton / CycleGuard patterns, and the framing of residual instability under diagnostic degradation). The dual-signal elevation construction and hidden-parity non-reducibility argument are original to this module.

## License

MIT
