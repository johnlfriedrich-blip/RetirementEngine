// src/App.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock the fetch function
global.fetch = jest.fn();

// Mock window.alert
global.alert = jest.fn();

describe('App', () => {
  beforeEach(() => {
    fetch.mockClear();
    alert.mockClear();
  });

  test('renders the App component', async () => {
    fetch.mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          us_equities: 0.3333,
          intl_equities: 0.3333,
          fixed_income: 0.3334,
        }),
    });

    render(<App />);
    expect(screen.getByText('Retirement Simulator')).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByLabelText(/us equities/i)).toBeInTheDocument()
    );
  });

  test('fetches and displays assets', async () => {
    const defaults = {
      us_equities: 0.3333,
      intl_equities: 0.3333,
      fixed_income: 0.3334,
    };
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(defaults),
    });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByLabelText(/us equities/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/intl equities/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/fixed income/i)).toBeInTheDocument();
    });
  });

  test('handles portfolio input change', async () => {
    fetch.mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          us_equities: 0.3333,
          intl_equities: 0.3333,
        }),
    });

    render(<App />);
    await waitFor(() =>
      expect(screen.getByLabelText(/us equities/i)).toBeInTheDocument()
    );

    const equitiesInput = screen.getByLabelText(/us equities/i);
    fireEvent.change(equitiesInput, { target: { value: '60' } });
    expect(equitiesInput.value).toBe('60');

    const intlInput = screen.getByLabelText(/intl equities/i);
    fireEvent.change(intlInput, { target: { value: '40' } });
    expect(intlInput.value).toBe('40');
  });

  test('submits the portfolio and displays results', async () => {
    fetch
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            us_equities: 0.5,
            fixed_income: 0.5,
          }),
      })
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            success_rate: 0.95,
            median_final_balance: 1000000,
          }),
      });

    render(<App />);
    await waitFor(() =>
      expect(screen.getByLabelText(/us equities/i)).toBeInTheDocument()
    );

    const equitiesInput = screen.getByLabelText(/us equities/i);
    fireEvent.change(equitiesInput, { target: { value: '60' } });

    const bondsInput = screen.getByLabelText(/fixed income/i);
    fireEvent.change(bondsInput, { target: { value: '40' } });

    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('Success Rate: 95.00%')).toBeInTheDocument();
      expect(
        screen.getByText(/Median Final Balance: \$1,000,000.00/)
      ).toBeInTheDocument();
    });
  });

  test('shows an alert if portfolio weights do not sum to 100', async () => {
    fetch.mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          us_equities: 0.5,
          fixed_income: 0.5,
        }),
    });

    render(<App />);
    await waitFor(() =>
      expect(screen.getByLabelText(/us equities/i)).toBeInTheDocument()
    );

    const equitiesInput = screen.getByLabelText(/us equities/i);
    fireEvent.change(equitiesInput, { target: { value: '50' } });

    const bondsInput = screen.getByLabelText(/fixed income/i);
    fireEvent.change(bondsInput, { target: { value: '40' } });

    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(alert).toHaveBeenCalledWith(
        'Portfolio weights must sum to 100%.'
      );
    });
  });
});