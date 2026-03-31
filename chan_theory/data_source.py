"""
Data source integration with Tushare (开源股票数据接口).

Tushare provides historical and real-time stock data for Chinese A-shares.
https://tushare.pro/

This module wraps tushare APIs to provide data in the format expected
by ChanAnalyzer.

Setup:
  1. pip install tushare
  2. Register at https://tushare.pro/ and get your API token
  3. Set token: ts.set_token('your_token')
     or pass it to TushareDataSource(token='your_token')
"""

from __future__ import annotations

from typing import Optional

from .data_types import RawKLine


class TushareDataSource:
    """
    Tushare data source for Chan Theory analysis.

    Provides methods to fetch K-line data at various frequencies
    and convert to RawKLine format for ChanAnalyzer.

    Usage:
        ds = TushareDataSource(token='your_tushare_token')
        klines = ds.get_daily('000001.SZ', '20240101', '20241231')

        from chan_theory import ChanAnalyzer
        analyzer = ChanAnalyzer()
        analyzer.load(klines)
        analyzer.analyze()
    """

    def __init__(self, token: Optional[str] = None) -> None:
        try:
            import tushare as ts
        except ImportError:
            raise ImportError(
                "tushare is required. Install with: pip install tushare\n"
                "Then register at https://tushare.pro/ to get an API token."
            )

        if token:
            ts.set_token(token)

        self._pro = ts.pro_api()
        self._ts = ts

    def get_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        adj: str = "qfq",
    ) -> list[RawKLine]:
        """
        Fetch daily K-line data.

        Args:
            ts_code: Stock code, e.g. '000001.SZ', '600519.SH'
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format
            adj: Adjustment type: 'qfq'(前复权), 'hfq'(后复权), ''(不复权)

        Returns:
            List of RawKLine objects sorted by date ascending
        """
        df = self._ts.pro_bar(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            adj=adj,
            freq="D",
        )

        if df is None or df.empty:
            return []

        # tushare returns data in descending order; reverse it
        df = df.sort_values("trade_date").reset_index(drop=True)

        return self._df_to_raw_klines(df)

    def get_weekly(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        adj: str = "qfq",
    ) -> list[RawKLine]:
        """Fetch weekly K-line data."""
        df = self._ts.pro_bar(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            adj=adj,
            freq="W",
        )

        if df is None or df.empty:
            return []

        df = df.sort_values("trade_date").reset_index(drop=True)
        return self._df_to_raw_klines(df)

    def get_monthly(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        adj: str = "qfq",
    ) -> list[RawKLine]:
        """Fetch monthly K-line data."""
        df = self._ts.pro_bar(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            adj=adj,
            freq="M",
        )

        if df is None or df.empty:
            return []

        df = df.sort_values("trade_date").reset_index(drop=True)
        return self._df_to_raw_klines(df)

    def get_minutes(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        freq: str = "5min",
        adj: str = "qfq",
    ) -> list[RawKLine]:
        """
        Fetch minute-level K-line data.

        Args:
            ts_code: Stock code
            start_date: Start date
            end_date: End date
            freq: Frequency - '1min', '5min', '15min', '30min', '60min'
            adj: Adjustment type
        """
        df = self._ts.pro_bar(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            adj=adj,
            freq=freq,
        )

        if df is None or df.empty:
            return []

        df = df.sort_values("trade_date").reset_index(drop=True)
        return self._df_to_raw_klines(df)

    def get_multi_level_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        levels: Optional[list[str]] = None,
        adj: str = "qfq",
    ) -> dict[str, list[RawKLine]]:
        """
        Fetch K-line data at multiple timeframe levels for multi-level analysis.

        Args:
            ts_code: Stock code
            start_date: Start date
            end_date: End date
            levels: List of frequencies. Defaults to ['daily', 'weekly']
            adj: Adjustment type

        Returns:
            Dict mapping level name to list of RawKLine
        """
        if levels is None:
            levels = ["daily", "weekly"]

        freq_map = {
            "1min": "1min",
            "5min": "5min",
            "15min": "15min",
            "30min": "30min",
            "60min": "60min",
            "daily": "D",
            "weekly": "W",
            "monthly": "M",
        }

        result = {}
        for level in levels:
            freq = freq_map.get(level, level)
            df = self._ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj,
                freq=freq,
            )

            if df is not None and not df.empty:
                df = df.sort_values("trade_date").reset_index(drop=True)
                result[level] = self._df_to_raw_klines(df)
            else:
                result[level] = []

        return result

    def search_stock(self, keyword: str) -> list[dict]:
        """
        Search for stock by name or code.

        Returns list of matching stocks with ts_code and name.
        """
        df = self._pro.stock_basic(
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,list_date",
        )

        if df is None or df.empty:
            return []

        mask = (
            df["ts_code"].str.contains(keyword, case=False, na=False) |
            df["name"].str.contains(keyword, case=False, na=False) |
            df["symbol"].str.contains(keyword, case=False, na=False)
        )
        matches = df[mask].head(20)

        return matches.to_dict("records")

    @staticmethod
    def _df_to_raw_klines(df) -> list[RawKLine]:
        """Convert tushare DataFrame to list of RawKLine."""
        klines = []
        for i, row in df.iterrows():
            klines.append(RawKLine(
                index=int(i),
                dt=str(row.get("trade_date", "")),
                open=float(row.get("open", 0)),
                close=float(row.get("close", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                volume=float(row.get("vol", 0)),
            ))
        return klines

    @staticmethod
    def from_csv(
        filepath: str,
        dt_col: str = "trade_date",
        open_col: str = "open",
        close_col: str = "close",
        high_col: str = "high",
        low_col: str = "low",
        vol_col: str = "vol",
    ) -> list[RawKLine]:
        """
        Load K-line data from a CSV file (for offline / no-token usage).

        The CSV should have columns for date, OHLCV data.
        This enables working without a tushare token.
        """
        import csv

        klines = []
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                klines.append(RawKLine(
                    index=i,
                    dt=row[dt_col],
                    open=float(row[open_col]),
                    close=float(row[close_col]),
                    high=float(row[high_col]),
                    low=float(row[low_col]),
                    volume=float(row.get(vol_col, 0)),
                ))

        return klines

    @staticmethod
    def from_dataframe(df, dt_col: str = "trade_date") -> list[RawKLine]:
        """
        Convert any pandas DataFrame with OHLCV columns to RawKLine list.

        Expected columns: trade_date (or dt_col), open, close, high, low, vol
        """
        klines = []
        for i, row in df.iterrows():
            klines.append(RawKLine(
                index=int(i) if isinstance(i, (int, float)) else 0,
                dt=str(row.get(dt_col, "")),
                open=float(row.get("open", 0)),
                close=float(row.get("close", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                volume=float(row.get("vol", row.get("volume", 0))),
            ))
        return klines
