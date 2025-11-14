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
      backgroundColor: "#3B82F6"
    },
    assetBundlePatterns: [
      "**/*"
    ],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "app.tribi.mobile"
    },
    android: {
      package: "app.tribi.mobile",
      usesCleartextTraffic: true
    },
    extra: {
      apiBase: "http://192.168.1.102:8000"
    },
    // Deshabilitar completamente el sistema de actualizaciones para desarrollo
    updates: {
      enabled: false,
      checkAutomatically: "OFF",
      fallbackToCacheTimeout: 0
    },
    runtimeVersion: {
      policy: "nativeVersion"
    }
  }
};
