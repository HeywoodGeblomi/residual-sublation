#ifndef DYNAMIC_COMMITMENT_REVEAL_H
#define DYNAMIC_COMMITMENT_REVEAL_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Dynamic Commitment Layer + Revealing Channel
 * --------------------------------------------
 * Extends DCL with a privileged revealing signal r_chi
 * that allows recovery of χ while preserving non-reducibility
 * with respect to the original visible signals (d, c).
 *
 * Recommended default: alpha_r = 0.20
 * Measured recovery: accuracy ≈ 0.85–0.90, lag ≈ 0.3–0.4 steps
 */

typedef struct {
    double d;        /* visible residual disorder        [0,1] */
    double c;        /* visible diagnostic competence    [0,1] */
    double lambda;   /* commitment tension               [0,1] */
    int    chi;      /* dynamic commitment variable χ    0/1  */
    double r_chi;    /* revealing channel                */
} dcl_reveal_state_t;

typedef struct {
    double alpha;    /* tension growth */
    double beta;     /* competence damping */
    double gamma;    /* correlation boost */
    double delta;    /* rigidity strength */
    double eta;      /* observation attenuation */
    double mu;       /* discharge rate */
    double kappa;    /* correlation-strengthened discharge */
    double tau;      /* commitment threshold */
    double theta;    /* commit enforcement threshold */
    double alpha_r;  /* revealing channel leak rate */
} dcl_reveal_params_t;

static const dcl_reveal_params_t DCL_REVEAL_DEFAULTS = {
    .alpha   = 0.15,
    .beta    = 0.10,
    .gamma   = 0.20,
    .delta   = 0.25,
    .eta     = 0.08,
    .mu      = 0.12,
    .kappa   = 1.5,
    .tau     = 0.30,
    .theta   = 0.45,
    .alpha_r = 0.20     /* revealing channel leak */
};

static inline void dcl_reveal_init(dcl_reveal_state_t *s)
{
    s->d      = 0.0;
    s->c      = 1.0;
    s->lambda = 0.0;
    s->chi    = 0;
    s->r_chi  = 0.0;
}

static inline void dcl_reveal_step(dcl_reveal_state_t *s,
                                   const dcl_reveal_params_t *par,
                                   double r_fresh,
                                   double k_fresh,
                                   double r_corr)
{
    const double rho = s->d * s->c;
    double rigidity = 0.0;

    if (s->lambda > 0.5 && r_corr > par->tau) {
        rigidity = (s->chi == 0 ? 1.0 : -1.0) * s->lambda * (1.0 - s->lambda);
    }

    double lambda_new =
        s->lambda
        + par->alpha * rho * (1.0 - s->lambda)
        - par->beta  * (1.0 - s->c) * s->lambda
        + par->delta * rigidity
        + par->gamma * r_corr * s->lambda * (1.0 - s->lambda);

    if (lambda_new < 0.0) lambda_new = 0.0;
    if (lambda_new > 1.0) lambda_new = 1.0;

    const double att = 1.0 - par->eta * lambda_new;
    s->d = s->d * att + (1.0 - att) * r_fresh;
    s->c = s->c * att + (1.0 - att) * k_fresh;

    if (lambda_new > 0.5 && r_corr > par->tau) {
        s->chi ^= 1;
    }

    s->lambda = lambda_new;

    /* Revealing channel update */
    double s_chi = (s->chi == 1) ? 1.0 : -1.0;
    s->r_chi = (1.0 - par->alpha_r) * s->r_chi + par->alpha_r * s_chi;
}

static inline int dcl_reveal_commit(dcl_reveal_state_t *s,
                                    const dcl_reveal_params_t *par,
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

static inline int dcl_recover_chi(const dcl_reveal_state_t *s)
{
    return (s->r_chi > 0.0) ? 1 : 0;
}

static inline double dcl_recover_chi_soft(const dcl_reveal_state_t *s, double beta)
{
    double x = beta * s->r_chi;
    if (x > 20.0) return 1.0;
    if (x < -20.0) return 0.0;
    return 1.0 / (1.0 + exp(-x));
}

#ifdef __cplusplus
}
#endif

#endif /* DYNAMIC_COMMITMENT_REVEAL_H */
