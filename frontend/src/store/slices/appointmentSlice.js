/**
 * Appointment slice -- booking, listing, cancellation, rescheduling.
 */
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import appointmentApi from '../../api/appointmentApi';
import { getErrorMessage } from '../../api/axiosConfig';

// ── Thunks ─────────────────────────────────────────────────────────────────

export const fetchAppointments = createAsyncThunk(
  'appointments/fetchAppointments',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.getAppointments(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchAppointment = createAsyncThunk(
  'appointments/fetchAppointment',
  async (appointmentId, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.getAppointment(appointmentId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const createAppointment = createAsyncThunk(
  'appointments/createAppointment',
  async (data, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.createAppointment(data);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const confirmAppointment = createAsyncThunk(
  'appointments/confirmAppointment',
  async (appointmentId, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.confirmAppointment(appointmentId);
      return { appointmentId, ...response.data };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const cancelAppointment = createAsyncThunk(
  'appointments/cancelAppointment',
  async ({ appointmentId, data }, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.cancelAppointment(appointmentId, data);
      return { appointmentId, ...response.data };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const rescheduleAppointment = createAsyncThunk(
  'appointments/rescheduleAppointment',
  async ({ appointmentId, data }, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.rescheduleAppointment(appointmentId, data);
      return { appointmentId, ...response.data };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchUpcomingAppointments = createAsyncThunk(
  'appointments/fetchUpcoming',
  async (_, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.getUpcoming();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchTimeSlots = createAsyncThunk(
  'appointments/fetchTimeSlots',
  async (params, { rejectWithValue }) => {
    try {
      const response = await appointmentApi.getTimeSlots(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

// ── Slice ──────────────────────────────────────────────────────────────────

const initialState = {
  appointments: [],
  selectedAppointment: null,
  upcoming: [],
  timeSlots: [],
  pagination: { count: 0, next: null, previous: null },
  loading: false,
  creating: false,
  error: null,
  successMessage: null,
};

const appointmentSlice = createSlice({
  name: 'appointments',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
    clearSuccess(state) {
      state.successMessage = null;
    },
    clearSelectedAppointment(state) {
      state.selectedAppointment = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch appointments
      .addCase(fetchAppointments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAppointments.fulfilled, (state, action) => {
        state.loading = false;
        const data = action.payload;
        state.appointments = data.results || data;
        state.pagination = {
          count: data.count || state.appointments.length,
          next: data.next || null,
          previous: data.previous || null,
        };
      })
      .addCase(fetchAppointments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch single
      .addCase(fetchAppointment.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchAppointment.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedAppointment = action.payload;
      })
      .addCase(fetchAppointment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Create
      .addCase(createAppointment.pending, (state) => {
        state.creating = true;
        state.error = null;
      })
      .addCase(createAppointment.fulfilled, (state, action) => {
        state.creating = false;
        state.appointments.unshift(action.payload);
        state.successMessage = 'Appointment booked successfully!';
      })
      .addCase(createAppointment.rejected, (state, action) => {
        state.creating = false;
        state.error = action.payload;
      })
      // Confirm
      .addCase(confirmAppointment.fulfilled, (state, action) => {
        const idx = state.appointments.findIndex(
          (a) => a.id === action.payload.appointmentId
        );
        if (idx !== -1) state.appointments[idx].status = 'confirmed';
        state.successMessage = 'Appointment confirmed.';
      })
      // Cancel
      .addCase(cancelAppointment.fulfilled, (state, action) => {
        const idx = state.appointments.findIndex(
          (a) => a.id === action.payload.appointmentId
        );
        if (idx !== -1) state.appointments[idx].status = 'cancelled';
        state.successMessage = 'Appointment cancelled.';
      })
      // Reschedule
      .addCase(rescheduleAppointment.fulfilled, (state, action) => {
        const idx = state.appointments.findIndex(
          (a) => a.id === action.payload.appointmentId
        );
        if (idx !== -1) state.appointments[idx].status = 'rescheduled';
        state.successMessage = 'Appointment rescheduled.';
      })
      // Upcoming
      .addCase(fetchUpcomingAppointments.fulfilled, (state, action) => {
        state.upcoming = action.payload;
      })
      // Time slots
      .addCase(fetchTimeSlots.fulfilled, (state, action) => {
        state.timeSlots = action.payload.results || action.payload;
      });
  },
});

export const { clearError, clearSuccess, clearSelectedAppointment } =
  appointmentSlice.actions;

export const selectAppointments = (state) => state.appointments.appointments;
export const selectSelectedAppointment = (state) => state.appointments.selectedAppointment;
export const selectUpcomingAppointments = (state) => state.appointments.upcoming;
export const selectTimeSlots = (state) => state.appointments.timeSlots;
export const selectAppointmentLoading = (state) => state.appointments.loading;
export const selectAppointmentCreating = (state) => state.appointments.creating;
export const selectAppointmentError = (state) => state.appointments.error;
export const selectAppointmentSuccess = (state) => state.appointments.successMessage;

export default appointmentSlice.reducer;
