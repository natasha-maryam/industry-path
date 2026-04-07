import Dashboard from "./pages/Dashboard"
import { useAuth, AuthProvider } from "./context/AuthContext"
import { WorkspaceProvider } from "./context/WorkspaceContext"
import SandboxAccessGate from "./pages/SandboxAccessGate"
import { isSandboxAppUrl } from "./sandbox/isSandboxAppUrl"

const ACCOUNT_TYPE_KEY = "industrypath:access:account_type"

function MainSoftwareApp() {
  const { user, logout, acknowledgeTeamSetup } = useAuth()

  return <Dashboard authenticatedUser={user} onLogout={logout} onAcknowledgeTeamSetup={acknowledgeTeamSetup} />
}

function App() {
  const isSandboxRoute = isSandboxAppUrl()
  const storedAccountType =
    typeof window !== "undefined" ? window.localStorage.getItem(ACCOUNT_TYPE_KEY)?.trim().toLowerCase() ?? "" : ""
  const forceSandboxForFreeUser = storedAccountType === "sandbox"
  const shouldRenderSandbox = isSandboxRoute || forceSandboxForFreeUser

  return (
    <WorkspaceProvider>
      {shouldRenderSandbox ? (
        <SandboxAccessGate />
      ) : (
        <AuthProvider>
          <MainSoftwareApp />
        </AuthProvider>
      )}
    </WorkspaceProvider>
  )
}

export default App