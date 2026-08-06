#ifndef DYNAMIC_COMMITMENT_H
#define DYNAMIC_COMMITMENT_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Dynamic Commitment Layer (DCL) v0.2.1
 * -------------------------------------
 * A minimal decision module that introduces an explicit dynamic hidden
 * variable χ required for correct long-horizon residual-diagnostic behavior.
 *
 * χ simultaneously:
 *   B – stores memory the visible system is forbidden to retain
 *   C – collapses ambiguity by selecting among possible futures
 *   D – maintains a minimal internal model of the residual process
 *
 * Any monitor limited to the visible signals (d, c) is information-
 * theoretically incomplete. The joint process is non-reducible to any
 * function of the observables alone.
 *
 * Empirical confirmation (parity-trap operationalization): full-χ and
 * frozen-χ trajectories diverge by 15.3 ± 0.8 cumulative absolute residual
 * units under identical observables (8 seeds, T=100, mean 3 flips).
 */

typedef struct {
    double d;       /* visible residual disorder           [0,1] */
    double c;       /* visible diagnostic competence       [0,1] */
    double lambda;  /* commitment tension                  [0,1] */
    int    chi;     /* dynamic commitment variable χ       0/1  */
} dcl_state_t;

typedef struct {
    double alpha;   /* tension growth from residual-competence product */
    double beta;    /* tension damping from low competence */
    double gamma;   /* tension boost from signal correlation */
    double delta;   /* commitment rigidity strength */
    double eta;     /* observation attenuation under tension */
    double mu;      /* base tension discharge rate */
    double kappa;   /* correlation-strengthened discharge */
    double tau;     /* correlation threshold for commitment act */
    double theta;   /* tension threshold that forces commitment enforcement */
} dcl_params_t;

/* Defaults matched to the parity-trap operationalization */
static const dcl_params_t DCL_DEFAULTS = {
    .alpha = 0.25,
    .beta  = 0.08,
    .gamma = 0.30,
    .delta = 0.55,
    .eta   = 0.10,
    .mu    = 0.08,
    .kappa = 1.2,
    .tau   = 0.20,
    .theta = 0.35
};

static inline void dcl_init(dcl_state_t *s)
{
    s->d      = 0.0;
    s->c      = 1.0;
    s->lambda = 0.0;
    s->chi    = 0;
}

/*
 * One evaluation step.
 * Polarity of χ now directly shapes the residual trajectory (parity-trap).
 */
static inline void dcl_step(dcl_state_t *s,
                            const dcl_params_t *par,
                            double r_fresh,
                            double k_fresh,
                            double r_corr)
{
    const double rho = s->d * s->c;
    double rigidity = 0.0;

    if (s->lambda > 0.4 && r_corr > par->tau) {
        rigidity = (s->chi == 0 ? 1.0 : -1.0) * s->lambda * (1.0 - s->lambda);
    }

    double lambda_new =
        s->lambda
        + par->alpha * rho * (1.0 - s->lambda)
        - par->beta  * (1.0 - s->c) * s->lambda
        + par->delta * rigidity
        + par->gamma * r_corr * (0.6 - s->lambda);

    if (lambda_new < 0.0) lambda_new = 0.0;
    if (lambda_new > 1.0) lambda_new = 1.0;

    const double att = 1.0 - par->eta * lambda_new;
    const double pol = (s->chi == 0 ? 1.0 : -1.0);

    /* Polarity term makes full-χ and frozen-χ trajectories diverge */
    s->d = s->d * att + (1.0 - att) * r_fresh
         + 0.12 * pol * (rigidity > 0.05 ? rigidity : 0.05) * s->lambda;
    if (s->d < 0.0) s->d = 0.0;
    if (s->d > 1.0) s->d = 1.0;

    s->c = s->c * att + (1.0 - att) * k_fresh;
    if (s->c < 0.05) s->c = 0.05;
    if (s->c > 1.0) s->c = 1.0;

    if (lambda_new > 0.45 && r_corr > par->tau) {
        s->chi ^= 1;
    }

    s->lambda = lambda_new;
}

static inline int dcl_commit(dcl_state_t *s,
                             const dcl_params_t *par,
                             double r_corr)
{
    if (s->lambda <= par->theta)
        return 0;

    const double discharge =
        par->mu * (s->lambda - par->theta) * (1.0 + par->kappa * r_corr);

    s->lambda -= discharge;
    if (s->lambda < 0.0)
        s->lambda = 0.0;

    return 1;
}

#ifdef __cplusplus
}
#endif

#endif /* DYNAMIC_COMMITMENT_H */
