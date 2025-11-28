// Mock for lucide-react icons
import React from 'react';

const createIconMock = (name) => {
  const Icon = (props) => <span data-testid={`icon-${name}`} {...props} />;
  Icon.displayName = name;
  return Icon;
};

export const AlertTriangle = createIconMock('alert-triangle');
export const Shield = createIconMock('shield');
export const MapPin = createIconMock('map-pin');
export const Info = createIconMock('info');
export const CheckCircle = createIconMock('check-circle');
export const XCircle = createIconMock('x-circle');
export const Wifi = createIconMock('wifi');
export const WifiOff = createIconMock('wifi-off');
export const RefreshCw = createIconMock('refresh');
export const Bell = createIconMock('bell');
export const Menu = createIconMock('menu');
export const X = createIconMock('x');
export const ChevronDown = createIconMock('chevron-down');
export const ChevronUp = createIconMock('chevron-up');
export const Filter = createIconMock('filter');
export const Search = createIconMock('search');
export const Clock = createIconMock('clock');
export const Globe = createIconMock('globe');
export const Activity = createIconMock('activity');
export const Users = createIconMock('users');
export const Settings = createIconMock('settings');
export const Home = createIconMock('home');
export const FileText = createIconMock('file-text');
export const Download = createIconMock('download');
export const Send = createIconMock('send');
export const Phone = createIconMock('phone');
export const Mail = createIconMock('mail');
export const Navigation = createIconMock('navigation');
export const Crosshair = createIconMock('crosshair');
export const Eye = createIconMock('eye');
export const EyeOff = createIconMock('eye-off');
export const Loader2 = createIconMock('loader-2');
export const AlertCircle = createIconMock('alert-circle');
export const CheckCircle2 = createIconMock('check-circle-2');
