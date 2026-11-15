# Draft email to the professor: approval for H3

**Not sent.** Draft for the team to review, sign and send. Nothing in the
repository records an approval; add the reply here once received. Until then H3
is reported as "pending approval" and can be removed from the comparison without
affecting any other model.

---

**Subject:** Group project (vote transfers): approval for one calibrated parameter

Dear Professor,

The project brief asks us to check with you before using machine learning or
advanced statistics. We would like your approval for one model that fits a single
parameter.

**Context.** Our question is which assumption about voter behaviour best explains
second-round results in French presidential elections (2002–2022). Each
assumption maps the supporters of eliminated first-round candidates to the two
finalists, blank/invalid ballots and abstention, per reporting area, in shares of
registered voters.

**What we compare first, with no fitting at all.** Two baselines (eliminated
supporters split in proportion to first-round shares, with or without
abstention), "nearest finalist" on a seven-point left–right scale (H1), and the
same rule with a fixed distance threshold beyond which voters abstain or vote
blank (H2). These rules have no parameter, so every election is a test for them.
We start with them because the question is about assumptions simple enough to
state in one sentence, and because they must be beaten before anything more
flexible is worth considering.

**The model we ask about (H3).** A share `p` of each eliminated group does not
follow the proximity rule and splits as in the baseline instead:

`H3 = (1 − p) × (H1 or H2) + p × baseline`, with `0 ≤ p ≤ 1`.

- `p` is the only fitted quantity. We find it by a grid search in steps of 0.01,
  minimising our error score (mean absolute error in percentage points).
- Validation is leave-one-election-out: `p` is fitted on four elections and the
  model is scored on the fifth, for each election in turn. Areas of one election
  are never split between training and test, and we report held-out scores only.
- There is no regression, no regularisation and no model selection beyond this.

**Why we think it is justified.** It asks one question the parameter-free rules
cannot: is the truth between "everyone follows proximity" and "nobody does"? It
also serves as a check on our own results, since a fitted `p` near 1 says the
proximity rule is not supported.

**What we would report.** The fitted `p` for each fold, the held-out scores next
to the parameter-free models, and the limits: five elections give five folds, so
we make no significance claim. In our current draft results H3 does not improve
on the simpler models, and we would say so.

If you prefer that we leave H3 out, the rest of the analysis stands without it.

Thank you,

[names]
