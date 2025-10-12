def test_extreme_inputs_withdrawal_strategies():
    from retirement_engine.withdrawal_strategies import (
        fixed_withdrawal,
        inflation_adjusted_withdrawal,
        dynamic_percent_withdrawal,
        guardrails_withdrawal,
        compute_expected_guardrails,
        pause_after_loss_withdrawal,
    )

    # Extreme scenario: flat market, high withdrawal rate
    balances = [1_000_000] * 5
    returns = [[0.0, 0.0]] * 4  # SP500 and BONDS both zero
    scalar_returns = [0.0] * 5
    rate = 0.10  # 10% withdrawal rate
    sp500_weight = 0.5

    # Fixed withdrawal
    fixed = fixed_withdrawal(balances[0], rate, len(balances))
    assert fixed == [100_000] * 5

    # Inflation-adjusted (flat inflation)
    inflation = inflation_adjusted_withdrawal(
        balances[0], rate, [0.0, 0.0], sp500_weight
    )
    assert all(abs(w - 100_000) < 1 for w in inflation)

    # Dynamic percent (10% of flat balance)
    dynamic = dynamic_percent_withdrawal(balances, rate)
    assert dynamic == [100_000] * 5

    # Guardrails (should scale linearly)
    guardrails = guardrails_withdrawal(balances, min_pct=0.05, max_pct=0.10)

    expected_guardrails = []
    for b in balances:
        if b > 2_500_000:
            pct = 0.10
        elif b < 750_000:
            pct = 0.03
        else:
            scale = (b - 500_000) / 500_000
            pct = 0.03 + scale * (0.10 - 0.03)
        expected_guardrails.append(b * pct)

    for i, (actual, expected) in enumerate(zip(guardrails, expected_guardrails)):
        print(f"[DEBUG] Year {i}: Actual=${actual:,.2f}, Expected=${expected:,.2f}")

    assert all(abs(a - b) < 1 for a, b in zip(guardrails, expected_guardrails))

    # Pause after loss (no loss, so no pause)
    pause = pause_after_loss_withdrawal(balances, returns, rate, sp500_weight)
    assert pause == [100_000] * 5
