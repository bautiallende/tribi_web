import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    Clipboard,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { esimAPI, ordersAPI, paymentsAPI } from '../api/client';

interface PlanSnapshot {
  id?: number;
  name?: string;
  country_name?: string;
  country_iso2?: string;
  carrier_name?: string;
  data_gb?: number;
  duration_days?: number;
  price_minor_units?: number;
  currency?: string;
}

interface Order {
  id: number;
  plan_id?: number;
  status: string;
  currency: string;
  amount_minor_units: number;
  amount_major?: string;
  plan_snapshot?: PlanSnapshot | null;
}

interface CheckoutScreenProps {
  navigation: any;
  route: {
    params: {
      orderId: number;
      planName: string;
      amount: string;
    };
  };
}

type CheckoutState = 'review' | 'processing' | 'success' | 'error';

interface ActivationData {
  activation_code: string | null;
  iccid: string | null;
  qr_payload?: string | null;
  instructions?: string | null;
  status: string;
}

export default function CheckoutScreen({ navigation, route }: CheckoutScreenProps) {
  const { orderId, planName, amount } = route.params;
  const [state, setState] = useState<CheckoutState>('review');
  const [order, setOrder] = useState<Order | null>(null);
  const [activationData, setActivationData] = useState<ActivationData | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadOrder = async () => {
      try {
        setIsLoading(true);
        const orders = await ordersAPI.getMyOrders();
        const found = orders.find((o) => o.id === orderId);
        if (!found) {
          throw new Error('Order not found');
        }
        setOrder(found);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Failed to load order');
        setState('error');
      } finally {
        setIsLoading(false);
      }
    };

    loadOrder();
  }, [orderId]);

  const handlePayment = async () => {
    if (!order) {
      setErrorMessage('Order not ready');
      return;
    }

    setState('processing');
    setErrorMessage('');

    try {
      // Step 1: Create MOCK payment
      await paymentsAPI.createPayment(orderId, 'MOCK');
      
      // Wait 1 second to simulate payment processing
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Step 2: Activate eSIM
      const activation = await esimAPI.activate(orderId);
      setActivationData(activation);
      setOrder({ ...order, status: 'paid' });
      setState('success');
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Payment or activation failed'
      );
      setState('error');
    }
  };

  const copyActivationCode = () => {
    if (activationData?.activation_code) {
      Clipboard.setString(activationData.activation_code);
      Alert.alert('Copied!', 'Activation code copied to clipboard');
    }
  };

  const handleGoToAccount = () => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'MainTabs', params: { screen: 'Account' } }],
    });
  };

  const handleRetry = () => {
    setState('review');
    setErrorMessage('');
  };

  const formatOrderAmount = (data?: Order | null) => {
    if (data) {
      if (data.amount_major) {
        return `${data.amount_major} ${data.currency}`;
      }
      return `${(data.amount_minor_units / 100).toFixed(2)} ${data.currency}`;
    }
    return `$${amount} USD`;
  };

  // Review State
  if (state === 'review') {
    if (isLoading) {
      return (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.processingSubtext}>Loading order...</Text>
        </View>
      );
    }

    const displayPlanName = order?.plan_snapshot?.name || planName;
    const displayDestination = order?.plan_snapshot?.country_name
      ? `${order.plan_snapshot.country_name}${order.plan_snapshot.country_iso2 ? ` (${order.plan_snapshot.country_iso2.toUpperCase()})` : ''}`
      : null;

    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.emoji}>💳</Text>
            <Text style={styles.title}>Review Your Order</Text>
          </View>

          {/* Order Summary */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Order Summary</Text>
            <View style={styles.orderRow}>
              <Text style={styles.orderLabel}>Plan</Text>
              <Text style={styles.orderValue}>{displayPlanName}</Text>
            </View>
            {displayDestination && (
              <>
                <View style={styles.divider} />
                <View style={styles.orderRow}>
                  <Text style={styles.orderLabel}>Destination</Text>
                  <Text style={styles.orderValue}>{displayDestination}</Text>
                </View>
              </>
            )}
            {order?.plan_snapshot?.data_gb && (
              <>
                <View style={styles.divider} />
                <View style={styles.orderRow}>
                  <Text style={styles.orderLabel}>Data</Text>
                  <Text style={styles.orderValue}>{order.plan_snapshot.data_gb} GB</Text>
                </View>
              </>
            )}
            {order?.plan_snapshot?.duration_days && (
              <>
                <View style={styles.divider} />
                <View style={styles.orderRow}>
                  <Text style={styles.orderLabel}>Duration</Text>
                  <Text style={styles.orderValue}>{order.plan_snapshot.duration_days} days</Text>
                </View>
              </>
            )}
            <View style={styles.divider} />
            <View style={styles.orderRow}>
              <Text style={styles.orderLabel}>Order ID</Text>
              <Text style={styles.orderValue}>#{orderId}</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.orderRow}>
              <Text style={styles.orderLabelBold}>Total</Text>
              <Text style={styles.orderValueBold}>{formatOrderAmount(order)}</Text>
            </View>
          </View>

          {/* Payment Method */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Payment Method</Text>
            <View style={styles.paymentMethod}>
              <Text style={styles.paymentEmoji}>🧪</Text>
              <View style={styles.paymentInfo}>
                <Text style={styles.paymentTitle}>MOCK Payment</Text>
                <Text style={styles.paymentSubtitle}>Test payment for development</Text>
              </View>
            </View>
          </View>

          {/* Action Buttons */}
          <TouchableOpacity style={styles.button} onPress={handlePayment}>
            <Text style={styles.buttonText}>Confirm & Pay</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.buttonSecondary}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.buttonSecondaryText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  // Processing State
  if (state === 'processing') {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.processingText}>Processing payment...</Text>
        <Text style={styles.processingSubtext}>This may take a few seconds</Text>
      </View>
    );
  }

  // Success State
  if (state === 'success' && activationData) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          {/* Success Header */}
          <View style={styles.successHeader}>
            <Text style={styles.successEmoji}>✅</Text>
            <Text style={styles.successTitle}>Payment Successful!</Text>
            <Text style={styles.successSubtitle}>
              Your eSIM has been activated
            </Text>
          </View>

          {/* Activation Code Card */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Activation Code</Text>
            <View style={styles.activationCodeContainer}>
              <Text style={styles.activationCode}>
                {activationData.activation_code || 'Activation code not available yet'}
              </Text>
              <TouchableOpacity
                style={styles.copyButton}
                disabled={!activationData.activation_code}
                onPress={copyActivationCode}
              >
                <Text style={[styles.copyButtonText, !activationData.activation_code && { opacity: 0.6 }]}>
                  Copy
                </Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.instructions}>
              Status: {activationData.status}
            </Text>
            {activationData.iccid && (
              <Text style={styles.instructions}>ICCID: {activationData.iccid}</Text>
            )}
            {activationData.qr_payload && (
              <Text style={styles.qrPayload}>{activationData.qr_payload}</Text>
            )}
          </View>

          {/* Instructions */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Activation Instructions</Text>
            <Text style={styles.instructions}>
              {activationData.instructions ||
                '1. Go to Settings > Cellular/Mobile Data\n' +
                  '2. Tap "Add eSIM"\n' +
                  '3. Choose "Enter Details Manually"\n' +
                  '4. Enter the activation code above\n' +
                  '5. Follow the on-screen instructions'}
            </Text>
          </View>

          {/* Actions */}
          <TouchableOpacity style={styles.button} onPress={handleGoToAccount}>
            <Text style={styles.buttonText}>View My Orders</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.buttonSecondary}
            onPress={() => navigation.navigate('Countries')}
          >
            <Text style={styles.buttonSecondaryText}>Browse More Plans</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  // Error State
  if (state === 'error') {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorEmoji}>❌</Text>
        <Text style={styles.errorTitle}>Payment Failed</Text>
        <Text style={styles.errorMessage}>
          {errorMessage || 'An unexpected error occurred'}
        </Text>
        <TouchableOpacity style={styles.button} onPress={handleRetry}>
          <Text style={styles.buttonText}>Try Again</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.buttonSecondary}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.buttonSecondaryText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  content: {
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
    marginTop: 20,
  },
  emoji: {
    fontSize: 60,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0F172A',
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 16,
  },
  orderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  orderLabel: {
    fontSize: 16,
    color: '#64748B',
  },
  orderValue: {
    fontSize: 16,
    color: '#0F172A',
    fontWeight: '500',
  },
  orderLabelBold: {
    fontSize: 18,
    color: '#0F172A',
    fontWeight: '700',
  },
  orderValueBold: {
    fontSize: 18,
    color: '#3B82F6',
    fontWeight: '700',
  },
  divider: {
    height: 1,
    backgroundColor: '#E2E8F0',
    marginVertical: 8,
  },
  paymentMethod: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  paymentEmoji: {
    fontSize: 32,
    marginRight: 16,
  },
  paymentInfo: {
    flex: 1,
  },
  paymentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0F172A',
    marginBottom: 4,
  },
  paymentSubtitle: {
    fontSize: 14,
    color: '#64748B',
  },
  button: {
    height: 48,
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  buttonSecondary: {
    height: 48,
    backgroundColor: 'transparent',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
  },
  buttonSecondaryText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748B',
  },
  processingText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#0F172A',
    marginTop: 24,
  },
  processingSubtext: {
    fontSize: 16,
    color: '#64748B',
    marginTop: 8,
  },
  successHeader: {
    alignItems: 'center',
    marginBottom: 32,
    marginTop: 20,
  },
  successEmoji: {
    fontSize: 80,
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  successSubtitle: {
    fontSize: 16,
    color: '#64748B',
  },
  activationCodeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 16,
  },
  activationCode: {
    flex: 1,
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  copyButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  copyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  instructions: {
    fontSize: 15,
    color: '#475569',
    lineHeight: 24,
  },
  qrPayload: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#0F172A',
  },
  errorEmoji: {
    fontSize: 80,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 16,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 20,
  },
});
