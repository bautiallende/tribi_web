const localApiBase =
  process.env.EXPO_PUBLIC_API_BASE || "http://192.168.1.102:8000";
const disableRemoteUpdates =
  process.env.EXPO_PUBLIC_DISABLE_REMOTE_UPDATES !== "false";

export default {
  expo: {
    name: "Tribi",
    slug: "tribi-mobile",
    version: "1.0.0",
    orientation: "portrait",
    userInterfaceStyle: "light",
    scheme: "tribi",
    splash: {
      resizeMode: "contain",
      backgroundColor: "#3B82F6",
    },
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "app.tribi.mobile",
      infoPlist: disableRemoteUpdates
        ? {
            EXUpdatesEnabled: false,
            EXUpdatesCheckOnLaunch: "NEVER",
          }
        : undefined,
    },
    android: {
      package: "app.tribi.mobile",
      usesCleartextTraffic: true,
      softwareKeyboardLayoutMode: "pan",
      manifestPlaceholders: disableRemoteUpdates
        ? {
            "expo.modules.updates.ENABLED": "false",
            "expo.modules.updates.EXPO_RUNTIME_VERSION": "1.0.0",
            "expo.modules.updates.EXPO_UPDATES_CHECK_ON_LAUNCH": "NEVER",
          }
        : undefined,
    },
    extra: {
      apiBase: localApiBase,
      eas: {
        projectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID,
      },
      disableRemoteUpdates,
    },
    updates: disableRemoteUpdates
      ? {
          enabled: false,
          checkAutomatically: "ON_ERROR_RECOVERY",
          fallbackToCacheTimeout: 0,
          url: undefined,
        }
      : {
          enabled: true,
          checkAutomatically: "ON_LOAD",
          fallbackToCacheTimeout: 30000,
        },
    runtimeVersion: {
      policy: "nativeVersion",
    },
  },
};
