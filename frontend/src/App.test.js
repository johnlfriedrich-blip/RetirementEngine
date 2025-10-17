
import React from 'react';
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
      json: () => Promise.resolve(['VFINX', 'VBMFX']),
    });
    render(<App />);
    expect(screen.getByText('Retirement Simulator')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText('VFINX')).toBeInTheDocument());
  });

  test('fetches and displays assets', async () => {
    const assets = ['Asset1', 'Asset2', 'Asset3'];
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(assets),
    });
    render(<App />);
    await waitFor(() => {
      assets.forEach((asset) => {
        expect(screen.getByLabelText(asset)).toBeInTheDocument();
      });
    });
  });

  test('handles portfolio input change', async () => {
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(['VFINX', 'VBMFX']),
    });
    render(<App />);
    await waitFor(() => expect(screen.getByLabelText('VFINX')).toBeInTheDocument());

    const vfinxInput = screen.getByLabelText('VFINX');
    fireEvent.change(vfinxInput, { target: { value: '60' } });
    expect(vfinxInput.value).toBe('60');

    const vbmfxInput = screen.getByLabelText('VBMFX');
    fireEvent.change(vbmfxInput, { target: { value: '40' } });
    expect(vbmfxInput.value).toBe('40');
  });

  test('submits the portfolio and displays results', async () => {
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(['VFINX', 'VBMFX']),
    });
    render(<App />);
    await waitFor(() => expect(screen.getByLabelText('VFINX')).toBeInTheDocument());

    const vfinxInput = screen.getByLabelText('VFINX');
    fireEvent.change(vfinxInput, { target: { value: '60' } });

    const vbmfxInput = screen.getByLabelText('VBMFX');
    fireEvent.change(vbmfxInput, { target: { value: '40' } });

    const simulationResults = {
      success_rate: 0.95,
      median_final_balance: 1000000,
    };
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(simulationResults),
    });

    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('Success Rate: 95.00%')).toBeInTheDocument();
      expect(screen.getByText(/Median Final Balance: \$1,000,000.00/)).toBeInTheDocument();
    });
  });

  test('shows an alert if portfolio weights do not sum to 100', async () => {
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(['VFINX', 'VBMFX']),
    });
    render(<App />);
    await waitFor(() => expect(screen.getByLabelText('VFINX')).toBeInTheDocument());

    const vfinxInput = screen.getByLabelText('VFINX');
    fireEvent.change(vfinxInput, { target: { value: '50' } });

    const vbmfxInput = screen.getByLabelText('VBMFX');
    fireEvent.change(vbmfxInput, { target: { value: '40' } });

    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(alert).toHaveBeenCalledWith('Portfolio weights must sum to 100%.');
    });
  });
});
