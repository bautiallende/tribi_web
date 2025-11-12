import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { countriesAPI } from '../api/client';

interface Country {
  id: number;
  iso2: string;
  name: string;
}

interface CountriesScreenProps {
  navigation: any;
}

export default function CountriesScreen({ navigation }: CountriesScreenProps) {
  const [countries, setCountries] = useState<Country[]>([]);
  const [filteredCountries, setFilteredCountries] = useState<Country[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      const data = await countriesAPI.getAll();
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
      (c) =>
        c.name.toLowerCase().includes(text.toLowerCase()) ||
        c.iso2.toLowerCase().includes(text.toLowerCase())
    );
    setFilteredCountries(filtered);
  };

  const renderCountry = ({ item }: { item: Country }) => (
    <TouchableOpacity
      style={styles.countryItem}
      onPress={() =>
        navigation.navigate('Plans', { iso2: item.iso2, countryName: item.name })
      }
    >
      <Text style={styles.countryName}>{item.name}</Text>
      <Text style={styles.countryCode}>{item.iso2}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🌐 Tribi</Text>
        <Text style={styles.subtitle}>Find eSIM Plans Worldwide</Text>
      </View>
      <TextInput
        style={styles.searchInput}
        placeholder="Search countries..."
        placeholderTextColor="#94A3B8"
        value={search}
        onChangeText={handleSearch}
      />
      {isLoading ? (
        <ActivityIndicator size="large" color="#3B82F6" style={styles.loader} />
      ) : (
        <FlatList
          data={filteredCountries}
          renderItem={renderCountry}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 24,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
  },
  searchInput: {
    margin: 16,
    padding: 14,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    fontSize: 16,
    color: '#0F172A',
  },
  loader: {
    marginTop: 40,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  countryItem: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  countryName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0F172A',
  },
  countryCode: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 4,
  },
});
