const localApiBase =
  process.env.EXPO_PUBLIC_API_BASE || "http://192.168.1.102:8000";

const otaEnabled =
  (process.env.EXPO_PUBLIC_ENABLE_REMOTE_UPDATES || "false").toLowerCase() ===
  "true";

const updatesConfig = otaEnabled
  ? {
      fallbackToCacheTimeout: 0,
      checkAutomatically:
        process.env.EXPO_PUBLIC_UPDATES_CHECK_AUTOMATICALLY ||
        "ON_ERROR_RECOVERY",
    }
  : {
      enabled: false,
    };

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
    },
    android: {
      package: "app.tribi.mobile",
      usesCleartextTraffic: true,
      softwareKeyboardLayoutMode: "pan",
    },
    plugins: ["expo-secure-store"],
    updates: updatesConfig,
    extra: {
      apiBase: localApiBase,
      eas: {
        projectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID,
      },
    },
  },
};
