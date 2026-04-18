import { useEffect, useMemo, useRef } from "react";

const INTERVAL_MAP = {
  "15m": "15",
  "30m": "30",
  "1h": "60",
  "4h": "240",
  "1d": "D",
  "1w": "W",
};

function buildTradingViewSymbol(assetType, symbol) {
  if (assetType === "forex") {
    return `FX:${symbol.replace("/", "")}`;
  }

  return `BINANCE:${symbol}`;
}

export default function TradingViewChart({ assetType, symbol, timeframe }) {
  const chartRef = useRef(null);
  const containerId = useMemo(
    () =>
      `tradingview_${assetType}_${symbol}_${timeframe}`.replace(
        /[^a-zA-Z0-9_\-]/g,
        "_",
      ),
    [assetType, symbol, timeframe],
  );

  useEffect(() => {
    const container = chartRef.current;

    if (!container) {
      return undefined;
    }

    container.innerHTML = "";

    const createWidget = () => {
      if (!window.TradingView || !window.TradingView.widget) {
        return;
      }

      new window.TradingView.widget({
        autosize: true,
        symbol: buildTradingViewSymbol(assetType, symbol),
        interval: INTERVAL_MAP[timeframe] || "60",
        timezone: "Etc/UTC",
        theme: "light",
        style: "1",
        locale: "en",
        enable_publishing: false,
        allow_symbol_change: false,
        container_id: containerId,
        hide_top_toolbar: false,
        hide_legend: false,
        save_image: false,
        studies: [
          "EMA@tv-basicstudies!EMA1",
          "EMA@tv-basicstudies!EMA2",
          "RSI@tv-basicstudies"
        ],
        studies_overrides: [
          {
            "EMA@tv-basicstudies!EMA1.Plot.linewidth": 2,
            "EMA@tv-basicstudies!EMA1.Plot.color": "#FF5733",
            "EMA@tv-basicstudies!EMA1.length": 20,
            "EMA@tv-basicstudies!EMA2.Plot.linewidth": 2,
            "EMA@tv-basicstudies!EMA2.Plot.color": "#FFA500",
            "EMA@tv-basicstudies!EMA2.length": 50,
            "RSI@tv-basicstudies.RSI.linewidth": 2,
            "RSI@tv-basicstudies.RSI.color": "#FF6B35",
            "RSI@tv-basicstudies.length": 14,
          }
        ],
      });
    };

    if (!document.querySelector("script[data-tradingview-widget]")) {
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/tv.js";
      script.async = true;
      script.dataset.tradingviewWidget = "true";
      script.onload = createWidget;
      document.body.appendChild(script);
    } else if (window.TradingView && window.TradingView.widget) {
      createWidget();
    } else {
      const timer = window.setTimeout(createWidget, 250);
      return () => window.clearTimeout(timer);
    }

    return () => {
      container.innerHTML = "";
    };
  }, [assetType, symbol, timeframe, containerId]);

  return <div className="tv-chart" id={containerId} ref={chartRef} />;
}
