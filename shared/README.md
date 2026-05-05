# Shared TypeScript Types

Shared TypeScript type definitions for the Customer Churn Prediction Platform.

## Purpose

This package contains TypeScript interfaces and types that are shared between the frontend and backend to ensure type consistency across the entire application.

## Usage

### In Frontend (Next.js)

```typescript
import { User, ModelVersion, Prediction } from '@churn-prediction/shared';

const user: User = {
  id: '123',
  email: 'user@example.com',
  role: 'Data_Scientist',
  createdAt: new Date().toISOString(),
  emailVerified: true,
  emailNotificationsEnabled: false,
};
```

### In Backend (Python)

While this package is TypeScript-based, the types serve as a reference for Pydantic schemas in the backend.

## Building

```bash
npm install
npm run build
```

## Development

Watch mode for automatic rebuilding:
```bash
npm run watch
```

## Types Included

- **User & Authentication**: User, AuthTokens, LoginRequest, RegisterRequest
- **Dataset**: Dataset, CustomerRecord
- **Model**: ModelType, ModelMetrics, ModelVersion
- **Training**: TrainingJob, TrainingJobStatus, TrainingProgress
- **Prediction**: PredictionInput, Prediction, SHAPValue
- **Dashboard**: DashboardMetrics
- **EDA**: CorrelationMatrix, DistributionData, ChurnByCategory
- **Feature Engineering**: FeatureImportance, PCAResult
- **Reports**: Report
- **Notifications**: Notification
- **API**: ApiResponse, ApiError, PaginatedResponse
- **WebSocket**: WebSocketMessage
