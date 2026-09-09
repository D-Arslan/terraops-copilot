# Drift report — design notes (module docstring of src/drift_report.py)

Data-drift report: the committed reference vs a window of production traffic.

Reads: monitoring/reference.json (frozen train statistics, built by
drift_reference.py) and the monitoring.predictions table written by the API.
Produces: an Evidently HTML report for humans, and a compact JSON summary that
the CT trigger can act on without parsing HTML.

Why the statistical test is PINNED in params.yaml
--------------------------------------------------
Evidently picks a test automatically based on sample size and column type. That
default is sensible, but "sensible and invisible" is the wrong property for the
number that decides whether a retraining pipeline fires. So monitor.stattest is
explicit, and it is `wasserstein` — an EFFECT SIZE, normalized by the reference
standard deviation, not a p-value.

The reason is the failure mode that kills most drift dashboards: a p-value test
answers "am I sure the distributions differ?", and with a large enough window the
answer is always yes, because two real samples are never exactly co-distributed.
At n = 500k a KS test rejects on a 0.2% difference between CDFs — statistically
significant, practically irrelevant, and the alert fires every day until someone
mutes it. Wasserstein answers "by how much", in units of the reference's own
spread, and that number does not inflate with volume.

The window is capped (monitor.current_window) for the same reason, and a floor
(monitor.min_current_rows) makes the report REFUSE to conclude on thin traffic
rather than emit a confident verdict built on eighty rows.

What this report can and cannot say
-----------------------------------
It compares INPUT distributions. It cannot measure accuracy, because production
has no labels — that is the whole premise of the sprint. A drifted verdict means
"the incoming data no longer resembles what the model learned from", which is a
reason to investigate and possibly retrain; it is never, by itself, proof that
predictions got worse. The experiment in experiments/ is what calibrates how
much one implies the other.
