"""
This module contains common utility functions.

Copyright 2021 David Kim. All rights reserved.
"""

# Imports
import math


def split(x, n):
    """
    Splits a number x into n integer parts. Algorithm credit -> GeeksForGeeks.

    Args:
        x (int): The number to be split.
        n (int): The number of parts for x.
    
    Returns:
        list: Stores each split part.
    """

    # If we cannot split the number into exactly n parts
    if (x < n):
        raise ValueError("Not possible to split")

    # If x % n == 0 then the minimum difference is 0 and all numbers are x / n
    elif (x % n == 0):
        out = []
        for i in range(n):
            out.append(x // n)
        return out

    else:
        # The first n - (x % n) values -> x / n
        # After that, the rest of the values -> x / n + 1
        zp = n - (x % n)
        pp = x // n

        high = n - zp
        if high > zp:
            cd = math.gcd(high, zp)
        else:
            cd = math.gcd(zp, high)

        hi = int(high / cd)
        lo = int(zp / cd)

        i = 0
        out = []
        while i < n:
            # Reorder the parts to be more evenly split back-and-forth
            if hi > lo:
                for l in range(lo):
                    out.append(pp)
                    out.append(pp + 1)
                for h in range(hi - lo):
                    out.append(pp + 1)
            else:
                for l in range(hi):
                    out.append(pp)
                    out.append(pp + 1)
                for h in range(lo - hi):
                    out.append(pp)

            i += lo + hi

    return out
