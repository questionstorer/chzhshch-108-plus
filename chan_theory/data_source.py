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
        # Try pro_bar first; fall back to pro.daily() if permission denied
        df = None
        try:
            df = self._ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj,
                freq="D",
            )
        except Exception:
            pass

        if df is None or df.empty:
            try:
                df = self._pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception:
                return []

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
        # Try pro_bar first; fall back to pro.weekly() if permission denied
        df = None
        try:
            df = self._ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj,
                freq="W",
            )
        except Exception:
            pass

        if df is None or df.empty:
            try:
                df = self._pro.weekly(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception:
                return []

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
        df = None
        try:
            df = self._ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj,
                freq="M",
            )
        except Exception:
            pass

        if df is None or df.empty:
            try:
                df = self._pro.monthly(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception:
                return []

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
        df = None
        try:
            df = self._ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj,
                freq=freq,
            )
        except Exception:
            return []

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

        pro_fallback = {
            "D": "daily",
            "W": "weekly",
            "M": "monthly",
        }

        result = {}
        for level in levels:
            freq = freq_map.get(level, level)
            df = None
            try:
                df = self._ts.pro_bar(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    adj=adj,
                    freq=freq,
                )
            except Exception:
                pass

            if (df is None or df.empty) and freq in pro_fallback:
                try:
                    api_method = getattr(self._pro, pro_fallback[freq])
                    df = api_method(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                    )
                except Exception:
                    pass

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


class AshareDataSource:
    """
    Free data source using Ashare (Sina/Tencent backends, no token needed).

    Ashare fetches data from public Sina and Tencent finance APIs.
    See: https://github.com/mpquant/Ashare

    Usage:
        ds = AshareDataSource()
        klines = ds.get_daily('sz300014', count=500)

    Code formats:
        sh000001   - Shanghai index
        sz300014   - Shenzhen stock
        sh600519   - Shanghai stock
        000001.XSHG / 300014.XSHE  - JoinQuant format
    """

    def __init__(self) -> None:
        # Import Ashare from workspace
        import importlib.util
        import os

        ashare_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Ashare", "Ashare.py",
        )
        if not os.path.exists(ashare_path):
            raise ImportError(
                "Ashare not found. Clone it into workspace:\n"
                "  git clone https://github.com/mpquant/Ashare.git"
            )
        spec = importlib.util.spec_from_file_location("Ashare", ashare_path)
        self._ashare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self._ashare)

    @staticmethod
    def convert_code(ts_code: str) -> str:
        """
        Convert tushare-style code to Ashare format.

        '300014.SZ' -> 'sz300014'
        '600519.SH' -> 'sh600519'
        '000001.SZ' -> 'sz000001'
        Already-formatted codes like 'sh600519' pass through.
        """
        if "." in ts_code:
            parts = ts_code.split(".")
            symbol = parts[0]
            suffix = parts[1].upper()
            if suffix in ("SZ", "XSHE"):
                return "sz" + symbol
            elif suffix in ("SH", "XSHG"):
                return "sh" + symbol
        return ts_code

    @staticmethod
    def _df_to_raw_klines(df) -> list[RawKLine]:
        """Convert Ashare DataFrame (datetime index, OHLCV columns) to RawKLine list."""
        klines = []
        df = df.reset_index()
        date_col = df.columns[0]  # first column is the datetime index
        for i, row in df.iterrows():
            dt_val = row[date_col]
            # Convert to YYYYMMDD string
            if hasattr(dt_val, "strftime"):
                dt_str = dt_val.strftime("%Y%m%d")
            else:
                dt_str = str(dt_val).replace("-", "")[:8]
            klines.append(RawKLine(
                index=int(i),
                dt=dt_str,
                open=float(row["open"]),
                close=float(row["close"]),
                high=float(row["high"]),
                low=float(row["low"]),
                volume=float(row.get("volume", 0)),
            ))
        return klines

    def get_daily(
        self,
        code: str,
        count: int = 500,
        end_date: str = "",
    ) -> list[RawKLine]:
        """
        Fetch daily K-line data.

        Args:
            code: Stock code (any format: 'sz300014', '300014.SZ', etc.)
            count: Number of bars to fetch
            end_date: Optional end date ('YYYY-MM-DD' or 'YYYYMMDD')

        Returns:
            List of RawKLine sorted ascending by date
        """
        ashare_code = self.convert_code(code)
        ed = end_date
        if ed and len(ed) == 8 and "-" not in ed:
            ed = f"{ed[:4]}-{ed[4:6]}-{ed[6:8]}"
        df = self._ashare.get_price(
            ashare_code, end_date=ed, count=count, frequency="1d",
        )
        return self._df_to_raw_klines(df)

    def get_weekly(
        self,
        code: str,
        count: int = 200,
        end_date: str = "",
    ) -> list[RawKLine]:
        """Fetch weekly K-line data."""
        ashare_code = self.convert_code(code)
        ed = end_date
        if ed and len(ed) == 8 and "-" not in ed:
            ed = f"{ed[:4]}-{ed[4:6]}-{ed[6:8]}"
        df = self._ashare.get_price(
            ashare_code, end_date=ed, count=count, frequency="1w",
        )
        return self._df_to_raw_klines(df)

    def get_monthly(
        self,
        code: str,
        count: int = 120,
        end_date: str = "",
    ) -> list[RawKLine]:
        """Fetch monthly K-line data."""
        ashare_code = self.convert_code(code)
        ed = end_date
        if ed and len(ed) == 8 and "-" not in ed:
            ed = f"{ed[:4]}-{ed[4:6]}-{ed[6:8]}"
        df = self._ashare.get_price(
            ashare_code, end_date=ed, count=count, frequency="1M",
        )
        return self._df_to_raw_klines(df)

    def get_minutes(
        self,
        code: str,
        count: int = 200,
        frequency: str = "60m",
    ) -> list[RawKLine]:
        """
        Fetch minute-level K-line data.

        Args:
            code: Stock code
            count: Number of bars
            frequency: '1m', '5m', '15m', '30m', '60m'
        """
        ashare_code = self.convert_code(code)
        df = self._ashare.get_price(
            ashare_code, count=count, frequency=frequency,
        )
        return self._df_to_raw_klines(df)
