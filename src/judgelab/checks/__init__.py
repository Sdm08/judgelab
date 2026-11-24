"""Check registry."""
from judgelab.checks.position_bias import run as position_bias
from judgelab.checks.verbosity_bias import run as verbosity_bias
from judgelab.checks.agreement import run as agreement
from judgelab.checks.self_preference import run as self_preference
from judgelab.checks.style_bias import run as style_bias
from judgelab.checks.rubric_stability import run as rubric_stability
from judgelab.checks.test_retest import run as test_retest

registry = {
    "position_bias": position_bias,
    "verbosity_bias": verbosity_bias,
    "agreement": agreement,
    "self_preference": self_preference,
    "style_bias": style_bias,
    "rubric_stability": rubric_stability,
    "test_retest": test_retest,
}
