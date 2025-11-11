import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Button } from 'react-native';
import { useEffect, useState } from 'react';

function HomeScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text>Open up App.tsx to start working on your app!</Text>
      <Button
        title="Go to Health"
        onPress={() => navigation.navigate('Health')}
      />
      <StatusBar style="auto" />
    </View>
  );
}

function HealthScreen() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${process.env.EXPO_PUBLIC_API_BASE}/health`);
        const json = await res.json();
        setData(json);
      } catch (error) {
        setData({ error: error.message });
      }
    };

    fetchData();
  }, []);

  return (
    <View style={styles.container}>
      <Text>{data ? JSON.stringify(data, null, 2) : 'Loading...'}</Text>
    </View>
  );
}

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Health" component={HealthScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
