const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

// Simply extend the default config without trying to block expo-updates
// since it's part of the Expo SDK and blocking it causes Metro to crash

module.exports = config;
