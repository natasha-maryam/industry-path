import Dashboard from "./pages/Dashboard"
import { WorkspaceProvider } from "./context/WorkspaceContext"
import Sandbox from "./pages/Sandbox"
import { isSandboxAppUrl } from "./sandbox/isSandboxAppUrl"

function App() {
  const isSandboxRoute = isSandboxAppUrl()

  return (
    <WorkspaceProvider>
      {isSandboxRoute ? <Sandbox /> : <Dashboard />}
    </WorkspaceProvider>
  )
}

export default App