import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { plansAPI, ordersAPI, getToken } from '../api/client';

interface Plan {
  id: number;
  name: string;
  data_gb: string;
  duration_days: number;
  price_usd: string;
  description: string;
  is_unlimited: boolean;
}

interface PlansScreenProps {
  route: {
    params: {
      iso2: string;
      countryName: string;
    };
  };
  navigation: any;
}

export default function PlansScreen({ route, navigation }: PlansScreenProps) {
  const { iso2, countryName } = route.params;
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, [iso2]);

  const fetchPlans = async () => {
    try {
      const data = await plansAPI.getByCountry(iso2);
      setPlans(data);
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Failed to load plans');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPlan = async (plan: Plan) => {
    // Check if user is authenticated
    const token = await getToken();
    if (!token) {
      Alert.alert(
        'Login Required',
        'Please login to purchase this plan',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Login',
            onPress: () =>
              navigation.reset({
                index: 0,
                routes: [{ name: 'AuthEmail' }],
              }),
          },
        ]
      );
      return;
    }

    // Create order
    try {
      const order = await ordersAPI.create(plan.id);
      navigation.navigate('Checkout', {
        orderId: order.id,
        planName: plan.name,
        amount: plan.price_usd,
      });
    } catch (error) {
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to create order'
      );
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
          <Text style={styles.detailValue}>
            {item.is_unlimited ? 'Unlimited' : `${item.data_gb} GB`}
          </Text>
        </View>
        <View style={styles.planDetail}>
          <Text style={styles.detailLabel}>Duration:</Text>
          <Text style={styles.detailValue}>{item.duration_days} days</Text>
        </View>
      </View>
      {item.description && (
        <Text style={styles.planDescription}>{item.description}</Text>
      )}
      <TouchableOpacity
        style={styles.selectButton}
        onPress={() => handleSelectPlan(item)}
      >
        <Text style={styles.selectButtonText}>Select Plan</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.countryTitle}>{countryName}</Text>
        <Text style={styles.countrySubtitle}>
          {plans.length} plan{plans.length !== 1 ? 's' : ''} available
        </Text>
      </View>
      {isLoading ? (
        <ActivityIndicator
          size="large"
          color="#3B82F6"
          style={styles.loader}
        />
      ) : plans.length > 0 ? (
        <FlatList
          data={plans}
          renderItem={renderPlan}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
        />
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>📭</Text>
          <Text style={styles.emptyText}>No plans available</Text>
        </View>
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
    paddingVertical: 16,
    paddingHorizontal: 24,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  countryTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  countrySubtitle: {
    fontSize: 14,
    color: '#64748B',
  },
  loader: {
    marginTop: 40,
  },
  listContent: {
    padding: 16,
  },
  planCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    flex: 1,
  },
  planPrice: {
    fontSize: 20,
    fontWeight: '700',
    color: '#3B82F6',
  },
  planDetails: {
    marginBottom: 12,
  },
  planDetail: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  detailLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
  },
  planDescription: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    lineHeight: 20,
  },
  selectButton: {
    backgroundColor: '#3B82F6',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  selectButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyEmoji: {
    fontSize: 60,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748B',
  },
});
