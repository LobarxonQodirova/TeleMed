/**
 * Doctor slice -- doctor listing, profiles, schedules, reviews.
 */
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import doctorApi from '../../api/doctorApi';
import { getErrorMessage } from '../../api/axiosConfig';

// ── Thunks ─────────────────────────────────────────────────────────────────

export const fetchDoctors = createAsyncThunk(
  'doctors/fetchDoctors',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getDoctors(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchDoctorProfile = createAsyncThunk(
  'doctors/fetchDoctorProfile',
  async (doctorId, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getDoctor(doctorId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchSpecialties = createAsyncThunk(
  'doctors/fetchSpecialties',
  async (_, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getSpecialties();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchDoctorSchedules = createAsyncThunk(
  'doctors/fetchDoctorSchedules',
  async (doctorId, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getDoctorSchedules(doctorId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchAvailableSlots = createAsyncThunk(
  'doctors/fetchAvailableSlots',
  async ({ doctorId, date }, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getAvailableSlots(doctorId, date);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchDoctorReviews = createAsyncThunk(
  'doctors/fetchDoctorReviews',
  async (doctorId, { rejectWithValue }) => {
    try {
      const response = await doctorApi.getDoctorReviews(doctorId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

// ── Slice ──────────────────────────────────────────────────────────────────

const initialState = {
  doctors: [],
  selectedDoctor: null,
  specialties: [],
  schedules: [],
  availableSlots: [],
  reviews: [],
  pagination: { count: 0, next: null, previous: null },
  loading: false,
  error: null,
  filters: {
    specialty: '',
    city: '',
    available: false,
    minRating: 0,
    feeMax: '',
    search: '',
  },
};

const doctorSlice = createSlice({
  name: 'doctors',
  initialState,
  reducers: {
    setFilters(state, action) {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters(state) {
      state.filters = initialState.filters;
    },
    clearSelectedDoctor(state) {
      state.selectedDoctor = null;
      state.schedules = [];
      state.availableSlots = [];
      state.reviews = [];
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch doctors
      .addCase(fetchDoctors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDoctors.fulfilled, (state, action) => {
        state.loading = false;
        const data = action.payload;
        state.doctors = data.results || data;
        state.pagination = {
          count: data.count || state.doctors.length,
          next: data.next || null,
          previous: data.previous || null,
        };
      })
      .addCase(fetchDoctors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch doctor profile
      .addCase(fetchDoctorProfile.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchDoctorProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedDoctor = action.payload;
      })
      .addCase(fetchDoctorProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Specialties
      .addCase(fetchSpecialties.fulfilled, (state, action) => {
        state.specialties = action.payload.results || action.payload;
      })
      // Schedules
      .addCase(fetchDoctorSchedules.fulfilled, (state, action) => {
        state.schedules = action.payload.results || action.payload;
      })
      // Available slots
      .addCase(fetchAvailableSlots.fulfilled, (state, action) => {
        state.availableSlots = action.payload.slots || [];
      })
      // Reviews
      .addCase(fetchDoctorReviews.fulfilled, (state, action) => {
        state.reviews = action.payload.results || action.payload;
      });
  },
});

export const { setFilters, clearFilters, clearSelectedDoctor, clearError } =
  doctorSlice.actions;

// ── Selectors ──────────────────────────────────────────────────────────────

export const selectDoctors = (state) => state.doctors.doctors;
export const selectSelectedDoctor = (state) => state.doctors.selectedDoctor;
export const selectSpecialties = (state) => state.doctors.specialties;
export const selectDoctorSchedules = (state) => state.doctors.schedules;
export const selectAvailableSlots = (state) => state.doctors.availableSlots;
export const selectDoctorReviews = (state) => state.doctors.reviews;
export const selectDoctorPagination = (state) => state.doctors.pagination;
export const selectDoctorLoading = (state) => state.doctors.loading;
export const selectDoctorFilters = (state) => state.doctors.filters;

export default doctorSlice.reducer;
