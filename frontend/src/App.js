import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = (process.env.REACT_APP_API_URL || "http://localhost:8000").replace(/\/+$/, "");

function App() {
  const [portfolio, setPortfolio] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
  //console.log("useEffect fired, API_URL:", API_URL);

  fetch(`${API_URL}/assets/defaults`)
    .then((response) => {
      console.log("Fetch response status:", response.status);
      return response.json();
    })
    .then((data) => {
      console.log("Defaults response:", data);

      const initialPortfolio = Object.fromEntries(
        Object.entries(data).map(([asset, weight]) => [
          asset,
          (weight * 100).toFixed(2),
        ])
      );
      setPortfolio(initialPortfolio);
    })
    .catch((err) => console.error("Error fetching defaults:", err));
}, []);


  const handlePortfolioChange = (asset, value) => {
    setPortfolio({
      ...portfolio,
      [asset]: parseFloat(value) || 0,
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setLoading(true);

    const totalWeight = Object.values(portfolio).reduce(
      (sum, weight) => sum + parseFloat(weight),
      0
    );
    if (Math.abs(totalWeight - 100) > 1e-9) {
      alert('Portfolio weights must sum to 100%.');
      setLoading(false);
      return;
    }

    const portfolioForApi = Object.fromEntries(
      Object.entries(portfolio).map(([asset, weight]) => [
        asset,
        parseFloat(weight) / 100,
      ])
    );

    fetch(`${API_URL}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assets: portfolioForApi }),
    })
      .then((response) => response.json())
      .then((data) => {
        setResults(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error:', error);
        setLoading(false);
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Retirement Simulator</h1>
      </header>
      <main>
        <form onSubmit={handleSubmit}>
          <h2>Create Your Portfolio</h2>
          <div className="portfolio-inputs">
            {Object.entries(portfolio).map(([asset, weight]) => (
              <div key={asset} className="portfolio-input">
                <label htmlFor={asset}>{asset.replace(/_/g, ' ')}</label>
                <input
                  type="number"
                  id={asset}
                  value={weight}
                  onChange={(e) => handlePortfolioChange(asset, e.target.value)}
                  min="0"
                  max="100"
                  step="0.01"
                />
                <span>%</span>
              </div>
            ))}
          </div>
          <button type="submit" disabled={loading}>
            {loading ? (
              <>
                Simulating...
                <div className="spinner"></div>
              </>
            ) : (
              'Run Simulation'
            )}
          </button>
        </form>
        {results && (
          <div className="results">
            <h2>Simulation Results</h2>
            <p>Success Rate: {(results.success_rate * 100).toFixed(2)}%</p>
            <p>
              Median Final Balance: $
              {results.median_final_balance.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;