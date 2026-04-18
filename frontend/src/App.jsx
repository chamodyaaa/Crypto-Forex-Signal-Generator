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
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysisSymbol, setSelectedAnalysisSymbol] = useState(null);
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
    setAnalyses([]);
    setSelectedAnalysisSymbol(null);

    try {
      // Parse comma-separated symbols from search or use single symbol
      let symbolsToAnalyze = [];

      if (search.trim()) {
        // Parse comma-separated symbols
        symbolsToAnalyze = search
          .split(",")
          .map((s) => s.trim().toUpperCase())
          .filter((s) => s.length > 0);
      } else {
        // Use currently selected symbol
        symbolsToAnalyze = [symbol];
      }

      // Fetch analysis for each symbol
      const results = [];
      for (const sym of symbolsToAnalyze) {
        try {
          const data = await fetchJson("/api/signal", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              asset_type: assetType,
              symbol: sym,
              timeframe,
            }),
          });
          results.push({ symbol: sym, data });
        } catch (err) {
          results.push({ symbol: sym, error: err.message });
        }
      }

      // Set analyses results
      setAnalyses(results);

      // Select first successful analysis or first one if all failed
      const firstValid = results.find((r) => !r.error);
      if (firstValid) {
        setSelectedAnalysisSymbol(firstValid.symbol);
        setSymbol(firstValid.symbol);
        setAnalysis(firstValid.data);
      } else if (results.length > 0) {
        setSelectedAnalysisSymbol(results[0].symbol);
        setAnalysis(null);
      }
    } catch (requestError) {
      setAnalyses([]);
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
              <span>Search Symbol(s) - Enter any crypto/forex pair</span>
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={
                  assetType === "crypto"
                    ? "Examples: BTCUSDT, ETHUSDT, ADAUSDT, SOLUSDT (or any pair)"
                    : "Examples: EUR/USD, GBP/USD, USD/JPY (or any pair)"
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
              💡 Type any symbol in the search field above to analyze, or select
              from dropdown. Use commas to analyze multiple pairs:
              ETHUSDT,BNBUSDT or EUR/USD,GBP/USD
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
              <span>
                {analyses.length > 0
                  ? `${analyses.length} result${analyses.length > 1 ? "s" : ""}`
                  : "Waiting for a run"}
              </span>
            </div>

            {analyses.length > 0 ? (
              <>
                {/* Symbol tabs for multiple analyses */}
                {analyses.length > 1 && (
                  <div className="symbol-tabs">
                    {analyses.map((result) => (
                      <button
                        key={result.symbol}
                        className={`tab ${selectedAnalysisSymbol === result.symbol ? "active" : ""} ${result.error ? "error" : ""}`}
                        onClick={() => {
                          setSelectedAnalysisSymbol(result.symbol);
                          setSymbol(result.symbol);
                          setAnalysis(result.data);
                        }}
                      >
                        {result.symbol}
                      </button>
                    ))}
                  </div>
                )}

                {/* Display selected analysis or first one */}
                {(() => {
                  const current = selectedAnalysisSymbol
                    ? analyses.find((r) => r.symbol === selectedAnalysisSymbol)
                    : analyses[0];

                  if (!current) return null;

                  if (current.error) {
                    return (
                      <div className="notice error">
                        Error analyzing {current.symbol}: {current.error}
                      </div>
                    );
                  }

                  const analysisData = current.data;
                  const finalSignal =
                    analysisData.signal?.final_signal ||
                    analysisData.signal?.rule_signal ||
                    "HOLD";

                  return (
                    <>
                      {/* Final Combined Signal Badge */}
                      <div
                        className={`signal-badge signal-${formatSignal(finalSignal).toLowerCase()}`}
                      >
                        {formatSignal(finalSignal)}
                      </div>

                      {/* Signal Signals Comparison */}
                      <div className="signals-comparison">
                        <div className="signal-item">
                          <span className="label">Rule-Based</span>
                          <strong
                            className={`signal-text signal-${formatSignal(analysisData.signal?.rule_signal).toLowerCase()}`}
                          >
                            {formatSignal(analysisData.signal?.rule_signal)}
                          </strong>
                        </div>
                        <div className="signal-item">
                          <span className="label">ML Prediction</span>
                          <strong
                            className={`signal-text signal-${formatSignal(analysisData.signal?.ml_signal).toLowerCase()}`}
                          >
                            {formatSignal(analysisData.signal?.ml_signal)}
                          </strong>
                        </div>
                        <div className="signal-item">
                          <span className="label">Final Decision</span>
                          <strong
                            className={`signal-text signal-${formatSignal(finalSignal).toLowerCase()}`}
                          >
                            {formatSignal(finalSignal)}
                          </strong>
                        </div>
                      </div>

                      <div className="result-grid">
                        <div>
                          <span>Rule-Based Confidence</span>
                          <strong>
                            {analysisData.signal?.rule_confidence ?? 0}%
                          </strong>
                        </div>
                        <div>
                          <span>ML Confidence</span>
                          <strong>
                            {analysisData.signal?.ml_confidence ?? 0}%
                          </strong>
                        </div>
                        <div>
                          <span>Combined Confidence</span>
                          <strong>
                            {analysisData.signal?.combined_confidence ?? 0}%
                          </strong>
                        </div>
                        <div>
                          <span>Price</span>
                          <strong>{analysisData.signal?.price ?? "N/A"}</strong>
                        </div>
                        <div>
                          <span>RSI</span>
                          <strong>{analysisData.signal?.rsi ?? "N/A"}</strong>
                        </div>
                        <div>
                          <span>EMA 20</span>
                          <strong>
                            {analysisData.signal?.ema_20 ??
                              analysisData.signal?.ema ??
                              "N/A"}
                          </strong>
                        </div>
                        <div>
                          <span>EMA 50</span>
                          <strong>
                            {analysisData.signal?.ema_50 ?? "N/A"}
                          </strong>
                        </div>
                      </div>

                      {/* Combined Reason */}
                      <div className="reason-box">
                        <span>Decision Logic</span>
                        <p>
                          {analysisData.signal?.combined_reason ||
                            analysisData.signal?.reason ||
                            "No reason returned."}
                        </p>
                      </div>
                    </>
                  );
                })()}
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
