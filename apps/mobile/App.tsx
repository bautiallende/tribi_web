import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
    LinkingOptions,
    NavigationContainer,
    NavigatorScreenParams,
} from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, LogBox, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { getToken } from './src/api/client';

// Import screens
import AccountScreen from './src/screens/AccountScreen';
import AuthCodeScreen from './src/screens/AuthCodeScreen';
import AuthEmailScreen from './src/screens/AuthEmailScreen';
import CheckoutScreen from './src/screens/CheckoutScreen';
import CountriesScreen from './src/screens/CountriesScreen';
import PlansScreen from './src/screens/PlansScreen';

declare const ErrorUtils: {
  getGlobalHandler?: () => ((error: unknown, isFatal?: boolean) => void) | undefined;
  setGlobalHandler?: (handler: (error: unknown, isFatal?: boolean) => void) => void;
} | undefined;

const suppressExpoUpdateCrashes = () => {
  const messageSubstring = 'failed to download remote updates';

  LogBox.ignoreLogs([messageSubstring]);

  if (!ErrorUtils?.getGlobalHandler || !ErrorUtils?.setGlobalHandler) {
    return;
  }

  const previousHandler = ErrorUtils.getGlobalHandler?.();
  ErrorUtils.setGlobalHandler?.((error, isFatal) => {
    const normalizedError = (error ?? {}) as { message?: string };
    const errorMessage =
      normalizedError && typeof normalizedError.message === 'string' ? normalizedError.message : '';
    if (errorMessage.includes(messageSubstring)) {
      console.log('🚫 OTA update error ignored in dev build:', errorMessage);
      return;
    }

    if (previousHandler) {
      previousHandler(error, isFatal);
    }
  });
};

suppressExpoUpdateCrashes();

type MainTabParamList = {
  Countries: undefined;
  Account: undefined;
};

type RootStackParamList = {
  AuthEmail: undefined;
  AuthCode: undefined;
  MainTabs: NavigatorScreenParams<MainTabParamList>;
  Plans: { iso2: string; countryName?: string };
  Checkout: { orderId: string };
};

const linking: LinkingOptions<RootStackParamList> = {
  prefixes: ['tribi://', 'https://tribi.app'],
  config: {
    screens: {
      AuthEmail: 'auth',
      AuthCode: 'auth/code',
      MainTabs: 'app',
      Plans: 'plans/:iso2',
      Checkout: 'checkout/:orderId',
    },
  },
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// Tab Navigator for main authenticated app
function MainTabs() {
  const insets = useSafeAreaInsets();
  
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#3B82F6',
        tabBarInactiveTintColor: '#94A3B8',
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        tabBarStyle: {
          borderTopWidth: 1,
          borderTopColor: '#E2E8F0',
          paddingTop: 8,
          paddingBottom: Math.max(insets.bottom, 8),
          height: 60 + Math.max(insets.bottom, 8),
        },
      }}
    >
      <Tab.Screen
        name="Countries"
        component={CountriesScreen}
        options={{
          title: 'Browse',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🌐</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Account"
        component={AccountScreen}
        options={{
          title: 'My Account',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>👤</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on app start
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await getToken();
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Error checking auth:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <NavigationContainer linking={linking}>
        <Stack.Navigator
          initialRouteName={isAuthenticated ? 'MainTabs' : 'AuthEmail'}
          screenOptions={{
            headerShown: false,
            cardStyle: { backgroundColor: '#FFFFFF' },
          }}
        >
          {/* Auth Flow */}
          <Stack.Screen name="AuthEmail" component={AuthEmailScreen} />
          <Stack.Screen name="AuthCode" component={AuthCodeScreen} />

          {/* Main App */}
          <Stack.Screen name="MainTabs" component={MainTabs} />
          <Stack.Screen
            name="Plans"
            component={PlansScreen}
            options={{ headerShown: true, title: 'eSIM Plans' }}
          />
          <Stack.Screen
            name="Checkout"
            component={CheckoutScreen}
            options={{ headerShown: true, title: 'Checkout' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748B',
  },
});
