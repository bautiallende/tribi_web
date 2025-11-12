import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Button, FlatList, TextInput, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useEffect, useState } from 'react';

const API_BASE = process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8000';

interface Country {
  id: number;
  iso2: string;
  name: string;
}

interface Plan {
  id: number;
  name: string;
  data_gb: string;
  duration_days: number;
  price_usd: string;
  description: string;
  is_unlimited: boolean;
}

function CountriesScreen({ navigation }) {
  const [countries, setCountries] = useState<Country[]>([]);
  const [filteredCountries, setFilteredCountries] = useState<Country[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/countries`);
      const data = await res.json();
      setCountries(data);
      setFilteredCountries(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (text: string) => {
    setSearch(text);
    const filtered = countries.filter(
      (c) => c.name.toLowerCase().includes(text.toLowerCase()) ||
             c.iso2.toLowerCase().includes(text.toLowerCase())
    );
    setFilteredCountries(filtered);
  };

  const renderCountry = ({ item }: { item: Country }) => (
    <TouchableOpacity
      style={styles.countryItem}
      onPress={() => navigation.navigate('Plans', { iso2: item.iso2, countryName: item.name })}
    >
      <Text style={styles.countryName}>{item.name}</Text>
      <Text style={styles.countryCode}>{item.iso2}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Tribi - Find eSIM Plans</Text>
      <TextInput
        style={styles.searchInput}
        placeholder="Search countries..."
        value={search}
        onChangeText={handleSearch}
      />
      {isLoading ? (
        <ActivityIndicator size="large" color="#0000ff" />
      ) : (
        <FlatList
          data={filteredCountries}
          renderItem={renderCountry}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
        />
      )}
      <StatusBar style="auto" />
    </View>
  );
}

function PlansScreen({ route, navigation }) {
  const { iso2, countryName } = route.params;
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, [iso2]);

  const fetchPlans = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/plans?country=${iso2}`);
      const data = await res.json();
      setPlans(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderPlan = ({ item }: { item: Plan }) => (
    <View style={styles.planCard}>
      <View style={styles.planHeader}>
        <Text style={styles.planName}>{item.name}</Text>
        <Text style={styles.planPrice}>${item.price_usd}</Text>
      </View>
      <View style={styles.planDetails}>
        <View style={styles.planDetail}>
          <Text style={styles.detailLabel}>Data:</Text>
          <Text style={styles.detailValue}>{item.is_unlimited ? 'Unlimited' : `${item.data_gb}GB`}</Text>
        </View>
        <View style={styles.planDetail}>
          <Text style={styles.detailLabel}>Duration:</Text>
          <Text style={styles.detailValue}>{item.duration_days} days</Text>
        </View>
      </View>
      {item.description && (
        <Text style={styles.planDescription}>{item.description}</Text>
      )}
      <TouchableOpacity style={styles.selectButton}>
        <Text style={styles.selectButtonText}>Select Plan</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.screenTitle}>{countryName}</Text>
      {isLoading ? (
        <ActivityIndicator size="large" color="#0000ff" />
      ) : plans.length > 0 ? (
        <FlatList
          data={plans}
          renderItem={renderPlan}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
        />
      ) : (
        <Text style={styles.emptyText}>No plans available</Text>
      )}
      <StatusBar style="auto" />
    </View>
  );
}

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen 
          name="Countries" 
          component={CountriesScreen}
          options={{ title: 'Browse Countries' }}
        />
        <Stack.Screen 
          name="Plans" 
          component={PlansScreen}
          options={{ title: 'Plans' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
    marginTop: 16,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
    marginTop: 16,
  },
  searchInput: {
    margin: 16,
    padding: 10,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    fontSize: 16,
  },
  listContent: {
    paddingHorizontal: 16,
  },
  countryItem: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  countryName: {
    fontSize: 16,
    fontWeight: '600',
  },
  countryCode: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  planCard: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planName: {
    fontSize: 16,
    fontWeight: '600',
  },
  planPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  planDetails: {
    marginBottom: 8,
  },
  planDetail: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: '#666',
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  planDescription: {
    fontSize: 12,
    color: '#555',
    marginBottom: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingTop: 8,
  },
  selectButton: {
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  selectButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 24,
  },
});