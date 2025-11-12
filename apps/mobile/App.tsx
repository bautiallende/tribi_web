import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { getToken } from './src/api/client';

// Import screens
import AuthEmailScreen from './src/screens/AuthEmailScreen';
import AuthCodeScreen from './src/screens/AuthCodeScreen';
import CheckoutScreen from './src/screens/CheckoutScreen';
import AccountScreen from './src/screens/AccountScreen';
import CountriesScreen from './src/screens/CountriesScreen';
import PlansScreen from './src/screens/PlansScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Tab Navigator for main authenticated app
function MainTabs() {
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
          paddingBottom: 8,
          height: 60,
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
    <>
      <StatusBar style="dark" />
      <NavigationContainer
        linking={{
          prefixes: ['tribi://', 'https://tribi.app'],
          config: {
            screens: {
              AuthEmail: 'auth',
              AuthCode: 'auth/code',
              MainTabs: {
                screens: {
                  Countries: 'browse',
                  Account: 'account',
                },
              },
              Plans: 'plans/:iso2',
              Checkout: 'checkout/:orderId',
            },
          },
        }}
      >
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
    </>
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
