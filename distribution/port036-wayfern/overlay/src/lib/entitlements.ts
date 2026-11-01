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
  remoteControl: boolean;
  scheduledAutomation: boolean;
}

const NONE: Entitlements = {
  active: false,
  browserAutomation: false,
  crossOsFingerprints: false,
  cloudBackup: false,
  teamCollaboration: false,
  cookieBot: false,
  remoteInteractive: false,
  remoteControl: false,
  scheduledAutomation: false,
  profileLimit: 0,
  requestsPerHour: 0,
  remoteBrowserHours: 0,
};

// Mirror of the plan capability matrix the API resolves. Keep in sync — a new
// plan must be declared here too, or it falls back to DEFAULT_PAID.
const PLAN_CAPABILITIES: Record<string, Capabilities> = {
  // Solo pays for a nightly bot and MCP without browser automation. No
  // fingerprint editing either.
  solo: {
    browserAutomation: false,
    crossOsFingerprints: false,
    cloudBackup: true,
    teamCollaboration: false,
    cookieBot: true,
    remoteInteractive: false,
    remoteControl: true,
    scheduledAutomation: true,
  },
  pro: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: false,
    cookieBot: true,
    remoteInteractive: true,
    remoteControl: true,
    scheduledAutomation: true,
  },
  team: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: true,
    cookieBot: true,
    remoteInteractive: true,
    remoteControl: true,
    scheduledAutomation: true,
  },
  enterprise: {
    browserAutomation: true,
    crossOsFingerprints: true,
    cloudBackup: true,
    teamCollaboration: true,
    cookieBot: true,
    remoteInteractive: true,
    remoteControl: true,
    scheduledAutomation: true,
  },
};

// Unknown paid plan -> pro-level (never team), the conservative reading.
// remoteControl is the one exception and is withheld: an unrecognised plan
// string must not open an internet-facing hook into this machine.
const DEFAULT_PAID: Capabilities = {
  browserAutomation: true,
  crossOsFingerprints: true,
  cloudBackup: true,
  teamCollaboration: false,
  cookieBot: true,
  remoteInteractive: true,
  remoteControl: false,
  scheduledAutomation: false,
};

/**
 * The user's effective entitlements. Prefers the backend-resolved object the
 * desktop attaches to CloudUser; only falls back to deriving from the plan
 * fields when it's missing (older cached state). The fallback mirrors the
 * capability matrix the API resolves.
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
      // Not back-filled from anything. A backend too old to send this key is a
      // backend with no remote-control endpoint to be entitled to, so `false`
      // is the true answer rather than a conservative guess.
      remoteControl: server.remoteControl ?? false,
      scheduledAutomation: server.scheduledAutomation ?? false,
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
        remoteControl: caps.remoteControl,
        scheduledAutomation: caps.scheduledAutomation,
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
 * The plan this account is served under. A team member's own `plan` is
 * `"free"` (the owner pays) while the backend resolves `effectivePlan` to the
 * owner's tier. The login response and an older backend omit the key, and then
 * the row's own plan is the only answer there is. Every "what plan is this?"
 * label or gate goes through here; billing surfaces keep reading `plan`,
 * because a seat has no subscription of its own.
 */
export function effectivePlanOf(user: CloudUser | null | undefined): string {
  return user?.effectivePlan ?? user?.plan ?? "free";
}

/**
 * Whether this user may enrol profiles in Cookie Bot. Every gate in the UI
 * goes through here so a plan change is one edit, and so the Pro badge and the
 * control it guards can never disagree.
 */
/** Recipes on a schedule: Solo, Pro, Team and Enterprise. */
export function canUseScheduledAutomation(
  user: CloudUser | null | undefined,
): boolean {
  const entitlements = getEntitlements(user);
  return entitlements.active && entitlements.scheduledAutomation;
}

export function canUseCookieBot(user: CloudUser | null | undefined): boolean {
  const entitlements = getEntitlements(user);
  return entitlements.active && entitlements.cookieBot;
}

/**
 * Whether this user may drive this desktop from donutbrowser.com.
 *
 * The bridge itself does not read this, the server decides who may send work,
 * and a cached entitlement that is a refresh cycle out of date must not be what
 * refuses a customer their own machine. This is what the UI reads to explain
 * WHY a connected desktop cannot be driven.
 */
export function canUseRemoteControl(
  user: CloudUser | null | undefined,
): boolean {
  const entitlements = getEntitlements(user);
  return entitlements.active && entitlements.remoteControl;
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

/**
 * A team seat that may open the team's profiles and keep what a session
 * changes, but not change the team's profiles, proxies or groups.
 */
export function isTeamLauncher(user: CloudUser | null | undefined): boolean {
  return Boolean(user?.teamId) && user?.teamRole === "launcher";
}

/** Owners and admins read the team's activity log. The cloud checks again. */
export function canViewTeamActivity(
  user: CloudUser | null | undefined,
): boolean {
  return (
    getEntitlements(user).teamCollaboration &&
    Boolean(user?.teamId) &&
    (user?.teamRole === "owner" || user?.teamRole === "admin")
  );
}
