import type { CloudUser, Entitlements } from "@/types";

const DEFAULT_REQUESTS_PER_HOUR = 100;

/**
 * This authorized fork unlocks capabilities that execute entirely on the local
 * machine. Set NEXT_PUBLIC_DONUT_LOCAL_FEATURES=0 at build time to produce an
 * upstream-compatible UI. Cloud-hosted services are never enabled here.
 */
export const LOCAL_FEATURES_ENABLED =
  process.env.NEXT_PUBLIC_DONUT_LOCAL_FEATURES !== "0";

interface Capabilities {
  browserAutomation: boolean;
  crossOsFingerprints: boolean;
  cloudBackup: boolean;
  teamCollaboration: boolean;
  cookieBot: boolean;
  remoteInteractive: boolean;
}

const NONE: Entitlements = {
  active: false,
  browserAutomation: false,
  crossOsFingerprints: false,
  cloudBackup: false,
  teamCollaboration: false,
  cookieBot: false,
  remoteInteractive: false,
  profileLimit: 0,
  requestsPerHour: 0,
  remoteBrowserHours: 0,
};

// Mirror of PLAN_CAPABILITIES in apps/backend/src/plans/entitlements.ts. Keep in
// sync — a new plan must be declared here too, or it falls back to DEFAULT_PAID.
const PLAN_CAPABILITIES: Record<string, Capabilities> = {
  // The one row where cookieBot, browserAutomation and remoteInteractive all
  // disagree: solo pays for a nightly bot and nothing else that drives a
  // browser. No fingerprint editing either.
  solo: {
    browserAutomation: false,
    crossOsFingerprints: false,
    cloudBackup: true,
    teamCollaboration: false,
    cookieBot: true,
    remoteInteractive: false,
  },
  pro: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: false,
    cookieBot: true,
    remoteInteractive: true,
  },
  team: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: true,
    cookieBot: true,
    remoteInteractive: true,
  },
  enterprise: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: true,
    cookieBot: true,
    remoteInteractive: true,
  },
};

// Unknown paid plan -> pro-level (never team), matching the backend default.
const DEFAULT_PAID: Capabilities = {
  browserAutomation: true,
  crossOsFingerprints: true,
  cloudBackup: true,
  teamCollaboration: false,
  cookieBot: true,
  remoteInteractive: true,
};

/**
 * The user's effective entitlements. Prefers the backend-resolved object the
 * desktop attaches to CloudUser; only falls back to deriving from the plan
 * fields when it's missing (older cached state). The fallback mirrors the
 * backend matrix in `apps/backend/src/plans/entitlements.ts`.
 */
export function getEntitlements(
  user: CloudUser | null | undefined,
): Entitlements {
  let result: Entitlements = NONE;

  if (user?.entitlements) {
    const server = user.entitlements;
    // A backend (or a cached login) older than the current release omits these
    // keys. Keep the cloud-service fallback identical to upstream behavior.
    result = {
      ...server,
      cookieBot: server.cookieBot ?? server.browserAutomation,
      remoteInteractive: server.remoteInteractive ?? server.browserAutomation,
      remoteBrowserHours: server.remoteBrowserHours ?? 0,
    };
  } else if (user) {
    const active =
      user.plan !== "free" &&
      (user.subscriptionStatus === "active" || user.planPeriod === "lifetime");

    if (active) {
      const caps = PLAN_CAPABILITIES[user.plan] ?? DEFAULT_PAID;
      result = {
        active: true,
        browserAutomation: caps.browserAutomation,
        crossOsFingerprints: caps.crossOsFingerprints,
        cloudBackup: caps.cloudBackup,
        teamCollaboration: caps.teamCollaboration,
        cookieBot: caps.cookieBot,
        remoteInteractive: caps.remoteInteractive,
        profileLimit: user.profileLimit,
        requestsPerHour: caps.browserAutomation ? DEFAULT_REQUESTS_PER_HOUR : 0,
        remoteBrowserHours: 0,
      };
    }
  }

  if (!LOCAL_FEATURES_ENABLED) return result;

  return {
    ...result,
    active: true,
    browserAutomation: true,
    crossOsFingerprints: true,
    profileLimit: Number.MAX_SAFE_INTEGER,
    requestsPerHour: 0,
  };
}

/**
 * Whether this user may enrol profiles in Cookie Bot. Every gate in the UI
 * goes through here so a plan change is one edit, and so the Pro badge and the
 * control it guards can never disagree.
 */
export function canUseCookieBot(user: CloudUser | null | undefined): boolean {
  const entitlements = getEntitlements(user);
  return entitlements.active && entitlements.cookieBot;
}

/**
 * Only a team owner sees per-member attribution. An admin can change team
 * settings but the pooled spend is the owner's bill.
 */
export function isTeamOwner(user: CloudUser | null | undefined): boolean {
  return (
    getEntitlements(user).teamCollaboration &&
    user?.teamRole === "owner" &&
    Boolean(user.teamId)
  );
}
