# withdrawal_strategies.py


def fixed_withdrawal(initial_balance, rate, n_periods):
    """Withdraw a fixed % of initial balance each year."""
    annual_amount = initial_balance * rate
    return [annual_amount] * n_periods


def inflation_adjusted_withdrawal(initial_balance, rate, return_series, sp500_weight):
    withdrawals = []
    base = initial_balance * rate

    for r in return_series:
        sp500_r, bonds_r = r
        blended_r = sp500_weight * sp500_r + (1 - sp500_weight) * bonds_r
        base *= 1 + blended_r
        withdrawals.append(base)

    return withdrawals


"""
def inflation_adjusted_withdrawal(initial_balance, rate, inflation_series):
    #Withdraw a fixed real amount adjusted for inflation.
    base = initial_balance * rate
    return [base * (1 + inflation_series[i]) for i in range(len(inflation_series))]
"""


def dynamic_percent_withdrawal(balance_series, rate):
    """Withdraw a % of current portfolio balance each year."""
    return [b * rate for b in balance_series]


def guardrails_withdrawal(balances, min_pct=0.03, max_pct=0.06):
    withdrawals = []
    for b in balances:
        if (
            not isinstance(b, (int, float)) or b <= 0 or b == float("inf") or b != b
        ):  # b != b catches nan
            withdrawals.append(0.0)
            continue

        # Scale between min and max based on balance (example logic)
        pct = min_pct + (max_pct - min_pct) * min(b / 1_000_000, 1)

        withdrawal = b * pct
        if (
            not (0 <= withdrawal <= b)
            or withdrawal == float("inf")
            or withdrawal != withdrawal
        ):
            print(
                f"[ERROR] Guardrails produced invalid withdrawal: {withdrawal} from balance {b}"
            )
            withdrawal = 0.0

        withdrawals.append(withdrawal)
    return withdrawals


def compute_expected_guardrails(balances, min_pct, max_pct):
    expected = []
    for b in balances:
        if b > 2_500_000:
            pct = max_pct
        elif b < 750_000:
            pct = min_pct
        else:
            scale = (b - 500_000) / 500_000
            pct = min_pct + scale * (max_pct - min_pct)
        expected.append(b * pct)
    return expected


def pause_after_loss_withdrawal(balance_series, return_windows, rate, sp500_weight):
    """
    Withdraw normally unless prior year had a negative blended return.
    Pause withdrawals until a positive year resumes.

    Parameters:
        balance_series: list of yearly balances
        return_windows: list of lists, each inner list is 365 daily (sp500_r, bonds_r) tuples for the prior year
        rate: base withdrawal rate (e.g., 0.04)
        sp500_weight: float between 0 and 1

    Returns:
        List of yearly withdrawals
    """
    withdrawals = []
    paused = False

    for i, balance in enumerate(balance_series):
        if i == 0:
            withdrawals.append(balance * rate)
            continue

        trailing_returns = return_windows[i - 1]
        cumulative = 1.0
        for sp500_r, bonds_r in trailing_returns:
            blended_r = sp500_weight * sp500_r + (1 - sp500_weight) * bonds_r
            cumulative *= 1 + blended_r
        annual_return = cumulative - 1

        if paused:
            if annual_return > 0:
                withdrawals.append(balance * rate)
                paused = False
            else:
                withdrawals.append(0.0)
        else:
            if annual_return < 0:
                withdrawals.append(0.0)
                paused = True
            else:
                withdrawals.append(balance * rate)

    return withdrawals
