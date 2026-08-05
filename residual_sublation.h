#ifndef RESIDUAL_SUBLATION_H
#define RESIDUAL_SUBLATION_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    double d;       /* residual disorder [0,1] */
    double c;       /* diagnostic competence [0,1] */
    double lambda;  /* elevation tension [0,1] */
    int    p;       /* hidden parity 0/1 */
} rsl_state_t;

typedef struct {
    double alpha;   /* product growth */
    double beta;    /* competence damping */
    double gamma;   /* parallel-repetition boost */
    double delta;   /* rigidity strength */
    double eta;     /* shared attenuation */
    double mu;      /* base discharge */
    double kappa;   /* correlation-strengthened discharge */
    double tau;     /* correlation threshold for Rig / flip */
    double theta;   /* elevation threshold */
} rsl_params_t;

/* Sensible defaults – override as needed */
static const rsl_params_t RSL_DEFAULTS = {
    .alpha = 0.15,
    .beta  = 0.10,
    .gamma = 0.20,
    .delta = 0.25,
    .eta   = 0.08,
    .mu    = 0.12,
    .kappa = 1.5,
    .tau   = 0.30,
    .theta = 0.45
};

/* Initialise a fresh state */
static inline void rsl_init(rsl_state_t *s)
{
    s->d      = 0.0;
    s->c      = 1.0;
    s->lambda = 0.0;
    s->p      = 0;
}

/*
 * One residual-evaluation step.
 * r_fresh  – newest raw residual estimate
 * k_fresh  – newest competence estimate
 * r_corr   – windowed correlation of the dual signal (caller computes)
 */
static inline void rsl_step(rsl_state_t *s,
                            const rsl_params_t *par,
                            double r_fresh,
                            double k_fresh,
                            double r_corr)
{
    const double rho = s->d * s->c;
    double rig = 0.0;

    if (s->lambda > 0.5 && r_corr > par->tau) {
        rig = (s->p == 0 ? 1.0 : -1.0) * s->lambda * (1.0 - s->lambda);
    }

    double lambda_new =
        s->lambda
        + par->alpha * rho * (1.0 - s->lambda)
        - par->beta  * (1.0 - s->c) * s->lambda
        + par->delta * rig
        + par->gamma * r_corr * s->lambda * (1.0 - s->lambda);

    if (lambda_new < 0.0) lambda_new = 0.0;
    if (lambda_new > 1.0) lambda_new = 1.0;

    const double att = 1.0 - par->eta * lambda_new;
    s->d = s->d * att + (1.0 - att) * r_fresh;
    s->c = s->c * att + (1.0 - att) * k_fresh;

    if (lambda_new > 0.5 && r_corr > par->tau)
        s->p ^= 1;

    s->lambda = lambda_new;
}

/*
 * Rewrite check + correlation-strengthened discharge.
 * Returns 1 → caller must use restricted policy π_λ
 * Returns 0 → ordinary residual menu
 */
static inline int rsl_rewrite(rsl_state_t *s,
                              const rsl_params_t *par,
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

#endif /* RESIDUAL_SUBLATION_H */
