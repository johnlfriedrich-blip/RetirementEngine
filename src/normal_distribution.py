# src/normal_distribution.py
import math
import numpy as np


def _generate_normal_by_box_muller(mean, std_dev, num_samples):
    """
    Generate normally distributed random numbers using the Box-Muller transform.
    """
    # Ensure we generate pairs of numbers.
    # If num_samples is odd, we'll generate one extra and discard it.
    num_pairs = math.ceil(num_samples / 2)

    # Generate uniform random numbers in (0, 1]
    u1 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)
    u2 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)

    # Apply the Box-Muller transform to get standard normal variables
    log_u1 = np.log(u1)
    z0 = np.sqrt(-2.0 * log_u1) * np.cos(2.0 * np.pi * u2)
    z1 = np.sqrt(-2.0 * log_u1) * np.sin(2.0 * np.pi * u2)

    # Combine the pairs and truncate to the desired number of samples
    standard_normal = np.stack((z0, z1), axis=-1).flatten()[:num_samples]

    # Scale by mean and standard deviation
    return mean + standard_normal * std_dev
