"""Check registry."""
from judgelab.checks.position_bias import run as position_bias
from judgelab.checks.verbosity_bias import run as verbosity_bias
from judgelab.checks.agreement import run as agreement

registry = {
    "position_bias": position_bias,
    "verbosity_bias": verbosity_bias,
    "agreement": agreement,
}
