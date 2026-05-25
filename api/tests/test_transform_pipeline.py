from io import StringIO

import pandas as pd

from app.services.transforms.normalization.periods import period_from_dataframe


def test_period_from_dataframe_uses_dates():
    df = pd.read_csv(
        StringIO("customer_id,amount,due_date\nC1,100,2026-03-15\n")
    )
    period = period_from_dataframe(df)
    assert period == "2026-03"
