import { AuthProvider } from './contexts/AuthContext'
import AppRoutes from './AppRoutes'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AppRoutes />
      </div>
    </AuthProvider>
  )
}

export default App