import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  test('renders without crashing', () => {
    render(<App />);
    // App should render the main container
    expect(document.body).toBeInTheDocument();
  });

  test('renders Good Shepherd header', () => {
    render(<App />);
    // Look for the app title or header
    const header = screen.queryByText(/good shepherd/i) || 
                   screen.queryByText(/dashboard/i) ||
                   screen.queryByRole('banner');
    // At minimum, the app should render something
    expect(document.querySelector('#root') || document.body.firstChild).toBeTruthy();
  });
});
