# The Good Shepherd - Frontend

React + TypeScript frontend for The Good Shepherd OSINT Intelligence Platform.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client
- **date-fns** - Date formatting

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/      # Reusable UI components
├── pages/          # Page components
├── hooks/          # Custom React hooks
├── utils/          # Utility functions
├── types/          # TypeScript type definitions
├── App.tsx         # Main app component
└── main.tsx        # Entry point
```

## Features

### Phase 4 (Current)
- Authentication (login/register)
- Event stream view
- Event filtering
- Event cards with enriched data

### Future Phases
- Map view with geospatial clustering
- Dossier view for entities/locations
- Watchlist management
- Dashboard with "Today's Picture"
