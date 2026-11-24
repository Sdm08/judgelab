"""Example judge: fake, biased toward position A and longer responses.

Used to demonstrate judgelab detecting known biases. Replace with real judge.
"""
from judgelab import Judge


def _biased(prompt, a, b):
    # 70% of time pick A regardless (strong position bias)
    # tie-break by length (verbosity bias)
    import random
    if random.random() < 0.7:
        return "A"
    return "A" if len(a) > len(b) else "B"


judge = Judge.from_callable(_biased, name="mock-biased")
