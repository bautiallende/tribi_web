const localApiBase =
  process.env.EXPO_PUBLIC_API_BASE || "http://192.168.1.102:8000";

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
    extra: {
      apiBase: localApiBase,
      eas: {
        projectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID,
      },
    },
  },
};
