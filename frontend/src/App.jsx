import { useEffect, useMemo, useState } from "react";
import TradingViewChart from "./TradingViewChart";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const DEFAULT_ASSET_TYPES = [
  { value: "crypto", label: "Crypto" },
  { value: "forex", label: "Forex" },
];

function buildUrl(path) {
  return `${API_BASE}${path}`;
}

async function fetchJson(path, options) {
  const response = await fetch(buildUrl(path), options);
  const rawBody = await response.text();
  let data = {};

  if (rawBody) {
    try {
      data = JSON.parse(rawBody);
    } catch {
      if (response.ok) {
        throw new Error(
          "Server returned an invalid response format. Expected JSON.",
        );
      }

      throw new Error(
        `Request failed (${response.status}): ${rawBody.slice(0, 200)}`,
      );
    }
  }

  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }

  return data;
}

function formatSignal(signal) {
  if (!signal) {
    return "HOLD";
  }

  return signal.toUpperCase();
}

export default function App() {
  const [assetType, setAssetType] = useState("crypto");
  const [timeframes, setTimeframes] = useState([
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1w",
  ]);
  const [timeframe, setTimeframe] = useState("1h");
  const [search, setSearch] = useState("");
  const [symbols, setSymbols] = useState([]);
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [loadingSymbols, setLoadingSymbols] = useState(false);
  const [running, setRunning] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadTimeframes = async () => {
      try {
        const data = await fetchJson("/api/timeframes");

        if (
          !cancelled &&
          Array.isArray(data.timeframes) &&
          data.timeframes.length > 0
        ) {
          setTimeframes(data.timeframes);
          if (!data.timeframes.includes(timeframe)) {
            setTimeframe(data.timeframes[0]);
          }
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
        }
      }
    };

    loadTimeframes();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setSearch("");
  }, [assetType]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setLoadingSymbols(true);

      try {
        const data = await fetchJson(
          `/api/symbols?asset_type=${encodeURIComponent(assetType)}&search=${encodeURIComponent(search)}`,
        );

        if (!cancelled) {
          const nextSymbols = Array.isArray(data.symbols) ? data.symbols : [];
          setSymbols(nextSymbols);

          setSymbol((currentSymbol) => {
            if (nextSymbols.length === 0) {
              return currentSymbol;
            }

            return nextSymbols.includes(currentSymbol)
              ? currentSymbol
              : nextSymbols[0];
          });

          setError("");
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
          setSymbols([]);
        }
      } finally {
        if (!cancelled) {
          setLoadingSymbols(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [assetType, search]);

  const symbolOptions = useMemo(() => {
    if (symbol && !symbols.includes(symbol)) {
      return [symbol, ...symbols];
    }

    return symbols;
  }, [symbol, symbols]);

  const handleRunAnalysis = async () => {
    setRunning(true);
    setError("");

    try {
      const data = await fetchJson("/api/signal", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          asset_type: assetType,
          symbol,
          timeframe,
        }),
      });

      setAnalysis(data);
    } catch (requestError) {
      setAnalysis(null);
      setError(requestError.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <main className="layout">
        <section className="hero card">
          <div className="eyebrow">Crypto / Forex Intelligence</div>
          <h1>Signal generator with live market context</h1>
          <p>
            Choose an asset, set the timeframe, then run analysis to fetch the
            latest rule-based and ML-backed signal. The chart below stays synced
            with the selected market.
          </p>
        </section>

        <section className="controls card">
          <div className="section-title">
            <h2>Analysis Controls</h2>
            <span>Backend connected</span>
          </div>

          <div className="form-grid">
            <label>
              <span>Asset Type</span>
              <select
                value={assetType}
                onChange={(event) => setAssetType(event.target.value)}
              >
                {DEFAULT_ASSET_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Timeframe</span>
              <select
                value={timeframe}
                onChange={(event) => setTimeframe(event.target.value)}
              >
                {timeframes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label className="full-width">
              <span>Search Symbol</span>
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={
                  assetType === "crypto"
                    ? "Search BTC, ETH, SOL..."
                    : "Search EUR, GBP, JPY..."
                }
              />
            </label>

            <label className="full-width">
              <span>Symbol</span>
              <select
                value={symbol}
                onChange={(event) => setSymbol(event.target.value)}
              >
                {symbolOptions.length > 0 ? (
                  symbolOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))
                ) : (
                  <option value={symbol}>
                    {loadingSymbols ? "Loading..." : "No symbols found"}
                  </option>
                )}
              </select>
            </label>
          </div>

          <div className="actions-row">
            <button
              type="button"
              className="run-button"
              onClick={handleRunAnalysis}
              disabled={running}
            >
              {running ? "Running Analysis..." : "Run Analysis"}
            </button>
            <div className="helper-text">
              TradingView chart updates automatically for{" "}
              {assetType === "crypto" ? "crypto" : "forex"} assets.
            </div>
          </div>

          {error ? <div className="notice error">{error}</div> : null}
        </section>

        <section className="content-grid">
          <div className="card chart-card">
            <div className="section-title">
              <h2>TradingView Chart</h2>
              <span>
                {symbol} · {timeframe}
              </span>
            </div>
            <TradingViewChart
              assetType={assetType}
              symbol={symbol}
              timeframe={timeframe}
            />
          </div>

          <div className="card result-card">
            <div className="section-title">
              <h2>Latest Analysis</h2>
              <span>{analysis ? "Live result" : "Waiting for a run"}</span>
            </div>

            {analysis ? (
              <>
                <div
                  className={`signal-badge signal-${formatSignal(analysis.signal?.rule_signal || "HOLD").toLowerCase()}`}
                >
                  {formatSignal(analysis.signal?.rule_signal)}
                </div>

                <div className="result-grid">
                  <div>
                    <span>ML Signal</span>
                    <strong>{formatSignal(analysis.signal?.ml_signal)}</strong>
                  </div>
                  <div>
                    <span>Confidence</span>
                    <strong>{analysis.signal?.confidence ?? 0}%</strong>
                  </div>
                  <div>
                    <span>Price</span>
                    <strong>{analysis.signal?.price ?? "N/A"}</strong>
                  </div>
                  <div>
                    <span>RSI</span>
                    <strong>{analysis.signal?.rsi ?? "N/A"}</strong>
                  </div>
                  <div>
                    <span>EMA 20</span>
                    <strong>{analysis.signal?.ema ?? "N/A"}</strong>
                  </div>
                  <div>
                    <span>MACD</span>
                    <strong>{analysis.signal?.macd ?? "N/A"}</strong>
                  </div>
                </div>

                <div className="reason-box">
                  <span>Reason</span>
                  <p>{analysis.signal?.reason || "No reason returned."}</p>
                </div>
              </>
            ) : (
              <div className="empty-state">
                Run an analysis to see the generated signal, confidence, and
                indicator values here.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
