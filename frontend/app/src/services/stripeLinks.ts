const readEnv = (key: string): string => {
  const value = (import.meta.env[key] as string | undefined) ?? "";
  return String(value).trim();
};

const firstNonEmpty = (...values: string[]): string => values.find((item) => item.trim().length > 0) ?? "";

export const getStripePaymentLink = (plan: "solo" | "team", maintenance: boolean, email: string): string => {
  const raw =
    plan === "team"
      ? firstNonEmpty(
          maintenance ? readEnv("VITE_STRIPE_TEAM_MAINTENANCE_LINK") : "",
          maintenance ? readEnv("NEXT_PUBLIC_STRIPE_TEAM_MAINTENANCE_LINK") : "",
          maintenance ? readEnv("STRIPE_TEAM_MAINTENANCE_LINK") : "",
          !maintenance ? readEnv("VITE_STRIPE_TEAM_LINK") : "",
          !maintenance ? readEnv("NEXT_PUBLIC_STRIPE_TEAM_LINK") : "",
          !maintenance ? readEnv("STRIPE_TEAM_LINK") : ""
        )
      : firstNonEmpty(
          maintenance ? readEnv("VITE_STRIPE_SOLO_MAINTENANCE_LINK") : "",
          maintenance ? readEnv("NEXT_PUBLIC_STRIPE_SOLO_MAINTENANCE_LINK") : "",
          maintenance ? readEnv("STRIPE_SOLO_MAINTENANCE_LINK") : "",
          !maintenance ? readEnv("VITE_STRIPE_SOLO_LINK") : "",
          !maintenance ? readEnv("NEXT_PUBLIC_STRIPE_SOLO_LINK") : "",
          !maintenance ? readEnv("STRIPE_SOLO_LINK") : ""
        );

  if (!raw) {
    return "";
  }
  try {
    const url = new URL(raw);
    if (email.trim()) {
      url.searchParams.set("prefilled_email", email.trim().toLowerCase());
      url.searchParams.set("client_reference_id", email.trim().toLowerCase());
    }
    return url.toString();
  } catch {
    return "";
  }
};
