/**
 * Redux store configuration with RTK.
 */
import { configureStore } from '@reduxjs/toolkit';

import appointmentReducer from './slices/appointmentSlice';
import authReducer from './slices/authSlice';
import consultationReducer from './slices/consultationSlice';
import doctorReducer from './slices/doctorSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    doctors: doctorReducer,
    appointments: appointmentReducer,
    consultations: consultationReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['consultations/setLocalStream'],
        ignoredPaths: ['consultations.localStream', 'consultations.remoteStream'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
