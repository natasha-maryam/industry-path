import Dashboard from "./pages/Dashboard"
import { useAuth, AuthProvider } from "./context/AuthContext"
import { WorkspaceProvider } from "./context/WorkspaceContext"
import Sandbox from "./pages/Sandbox"
import { isSandboxAppUrl } from "./sandbox/isSandboxAppUrl"

function MainSoftwareApp() {
  const { user, logout, acknowledgeTeamSetup } = useAuth()

  return <Dashboard authenticatedUser={user} onLogout={logout} onAcknowledgeTeamSetup={acknowledgeTeamSetup} />
}

function App() {
  const isSandboxRoute = isSandboxAppUrl()

  return (
    <WorkspaceProvider>
      {isSandboxRoute ? (
        <Sandbox />
      ) : (
        <AuthProvider>
          <MainSoftwareApp />
        </AuthProvider>
      )}
    </WorkspaceProvider>
  )
}

export default App