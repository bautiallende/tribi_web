# Tribi Mobile App

React Native mobile application for purchasing and managing eSIM plans worldwide. Built with Expo and TypeScript.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator, OR Expo Go app on your physical device

### Installation

```bash
# Install dependencies
cd apps/mobile
npm install

# Start development server
npm run start
```

Then:

- Press `i` to open iOS Simulator
- Press `a` to open Android Emulator
- Scan QR code with Expo Go app on your phone

## 🏗️ Project Structure

```
apps/mobile/
├── src/
│   ├── api/
│   │   └── client.ts           # API client with SecureStore auth
│   └── screens/
│       ├── AuthEmailScreen.tsx # Email input for OTP
│       ├── AuthCodeScreen.tsx  # 6-digit code verification
│       ├── CountriesScreen.tsx # Browse countries (Tab 1)
│       ├── PlansScreen.tsx     # View plans for country
│       ├── CheckoutScreen.tsx  # MOCK payment + eSIM activation
│       └── AccountScreen.tsx   # My orders + logout (Tab 2)
├── App.tsx                     # Navigation setup
├── app.json                    # Expo configuration
└── package.json
```

## 📱 Features

### Authentication Flow

- **Email OTP Login**: Passwordless authentication
- **Secure Token Storage**: JWT tokens stored in Expo SecureStore
- **Auto-navigation**: Redirects based on authentication state

### Main App (Bottom Tabs)

1. **Browse Tab** 🌐

   - Search and select countries
   - View available eSIM plans
   - Create orders

2. **My Account Tab** 👤
   - View all orders
   - Copy eSIM activation codes
   - Refresh orders (pull to refresh)
   - Logout

### Checkout Flow

- **Order Review**: Plan details, pricing
- **MOCK Payment**: Test payment provider
- **eSIM Activation**: Automatic activation with code
- **Instructions**: How to install eSIM on device

## 🔗 Deep Linking

The app supports deep linking with the scheme `tribi://`:

- `tribi://auth` - Login screen
- `tribi://browse` - Browse countries
- `tribi://account` - My orders
- `tribi://plans/US` - Plans for specific country (ISO2 code)
- `tribi://checkout/123` - Checkout for order ID

## 🔧 Configuration

### Environment Variables

Create a `.env` file (use `.env.example` as template):

```bash
EXPO_PUBLIC_API_BASE=http://localhost:8000
EXPO_PUBLIC_ENABLE_REMOTE_UPDATES=false
```

For production:

```bash
EXPO_PUBLIC_API_BASE=https://api.tribi.app
EXPO_PUBLIC_ENABLE_REMOTE_UPDATES=true
```

### Backend API

The mobile app connects to the FastAPI backend. Ensure it's running:

```bash
cd apps/backend
uvicorn app.main:app --reload
```

API Endpoints used:

- `POST /api/auth/request-code` - Request OTP
- `POST /api/auth/verify` - Verify OTP code
- `GET /api/countries` - List countries
- `GET /api/plans?country={iso2}` - Get plans by country
- `POST /api/orders` - Create order (requires auth)
- `GET /api/orders/mine` - My orders (requires auth)
- `POST /api/payments/create` - Create MOCK payment (requires auth)
- `POST /api/esims/activate` - Activate eSIM (requires auth)

## 🎨 Design System

- **Primary Color**: `#3B82F6` (Blue)
- **Background**: `#F8FAFC` (Light gray)
- **Text**: `#0F172A` (Dark slate)
- **Muted Text**: `#64748B` (Slate gray)
- **Border**: `#E2E8F0` (Light slate)

## 🧪 Testing Locally

### Test Authentication

1. Enter any email (e.g., `test@example.com`)
2. Check backend logs for OTP code
3. Enter the 6-digit code
4. JWT token is saved to SecureStore

### Test Order Flow

1. Browse countries → Select country
2. View plans → Select plan
3. Checkout → Confirm payment (MOCK)
4. Activation code displayed
5. View in My Account tab

## 📦 Dependencies

- **expo**: ~49.0.15 - Expo SDK
- **react-native**: 0.72.10 - React Native framework
- **@react-navigation/native**: ^6.1.9 - Navigation
- **@react-navigation/stack**: ^6.3.20 - Stack navigator
- **@react-navigation/bottom-tabs**: ^6.5.0 - Tab navigator
- **expo-secure-store**: - Secure JWT storage
- **expo-constants**: - Environment variables

## 🚢 Building for Production

### iOS

```bash
# Build for App Store
expo build:ios --release-channel production

# Or create IPA for TestFlight
eas build --platform ios
```

Requirements:

- Apple Developer account
- Update `ios.bundleIdentifier` in `app.json`

### Android

```bash
# Build APK for testing
expo build:android --release-channel production

# Or create AAB for Google Play
eas build --platform android
```

Requirements:

- Update `android.package` in `app.json`
- Configure signing keystore

## 🔒 Security

- JWT tokens stored in Expo SecureStore (encrypted)
- All authenticated requests use `Authorization: Bearer {token}`
- Token cleared on logout
- HTTPS required for production API

## 🐛 Troubleshooting

### "Cannot find module" errors

```bash
cd apps/mobile
rm -rf node_modules
npm install
```

### Metro bundler cache issues

```bash
expo start --clear
```

### "Failed to download remote update"

- OTA updates are disabled locally by default (`EXPO_PUBLIC_ENABLE_REMOTE_UPDATES=false`) to prevent Expo Go from waiting on remote bundles.
- If you intentionally publish OTA builds, set the flag to `true` and ensure the device has network access to Expo's update servers.

### SecureStore not working

- SecureStore requires physical device or simulator (not Expo Go web)
- Check expo-secure-store is installed

### API connection fails

- Verify `EXPO_PUBLIC_API_BASE` is set correctly
- Use `http://10.0.2.2:8000` for Android emulator (localhost)
- Use your computer's IP for physical devices: `http://192.168.x.x:8000`

## 📝 TODO

- [ ] Add loading state for order creation
- [ ] Implement error boundaries
- [ ] Add unit tests with Jest
- [ ] Optimize images and assets
- [ ] Add push notifications for order status
- [ ] Implement biometric authentication
- [ ] Add in-app purchases for premium features
- [ ] Support multiple languages (i18n)

## 📄 License

MIT License - see LICENSE file for details
