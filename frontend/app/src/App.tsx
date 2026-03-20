import Dashboard from "./pages/Dashboard"
import { WorkspaceProvider } from "./context/WorkspaceContext"

function App() {
  return (
    <WorkspaceProvider>
      <Dashboard />
    </WorkspaceProvider>
  )
}

export default App