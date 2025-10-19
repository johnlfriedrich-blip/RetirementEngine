# src/student_t_distribution.py
from scipy.stats import t


def _generate_student_t_variates(df, mean, scale, num_samples):
    """
    Generate Student-t distributed random numbers.
    """
    return mean + scale * t.rvs(df, size=num_samples)
