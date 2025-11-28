// Mock for react-map-gl/maplibre
import React from 'react';

const Map = ({ children, ...props }) => (
  <div data-testid="mock-map" {...props}>
    {children}
  </div>
);

const Marker = ({ children, ...props }) => (
  <div data-testid="mock-marker" {...props}>
    {children}
  </div>
);

const Popup = ({ children, ...props }) => (
  <div data-testid="mock-popup" {...props}>
    {children}
  </div>
);

const NavigationControl = () => <div data-testid="mock-nav-control" />;
const ScaleControl = () => <div data-testid="mock-scale-control" />;

export default Map;
export { Marker, Popup, NavigationControl, ScaleControl };
