/**
 * Consultation slice -- listing, active call state, notes, queue.
 */
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import consultationApi from '../../api/consultationApi';
import { getErrorMessage } from '../../api/axiosConfig';

// ── Thunks ─────────────────────────────────────────────────────────────────

export const fetchConsultations = createAsyncThunk(
  'consultations/fetchConsultations',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await consultationApi.getConsultations(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchConsultation = createAsyncThunk(
  'consultations/fetchConsultation',
  async (consultationId, { rejectWithValue }) => {
    try {
      const response = await consultationApi.getConsultation(consultationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const joinWaitingRoom = createAsyncThunk(
  'consultations/joinWaitingRoom',
  async (consultationId, { rejectWithValue }) => {
    try {
      const response = await consultationApi.joinWaitingRoom(consultationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const startConsultation = createAsyncThunk(
  'consultations/startConsultation',
  async (consultationId, { rejectWithValue }) => {
    try {
      const response = await consultationApi.startConsultation(consultationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const endConsultation = createAsyncThunk(
  'consultations/endConsultation',
  async (consultationId, { rejectWithValue }) => {
    try {
      const response = await consultationApi.endConsultation(consultationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const fetchQueueStatus = createAsyncThunk(
  'consultations/fetchQueueStatus',
  async (consultationId, { rejectWithValue }) => {
    try {
      const response = await consultationApi.getQueueStatus(consultationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const createConsultationNote = createAsyncThunk(
  'consultations/createNote',
  async ({ consultationId, data }, { rejectWithValue }) => {
    try {
      const response = await consultationApi.createNote(consultationId, data);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

// ── Slice ──────────────────────────────────────────────────────────────────

const initialState = {
  consultations: [],
  activeConsultation: null,
  sessionToken: null,
  queuePosition: null,
  estimatedWait: null,
  notes: [],
  chatMessages: [],
  callStatus: 'idle', // idle | connecting | connected | ended
  isAudioMuted: false,
  isVideoMuted: false,
  pagination: { count: 0, next: null, previous: null },
  loading: false,
  error: null,
};

const consultationSlice = createSlice({
  name: 'consultations',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
    setCallStatus(state, action) {
      state.callStatus = action.payload;
    },
    toggleAudioMute(state) {
      state.isAudioMuted = !state.isAudioMuted;
    },
    toggleVideoMute(state) {
      state.isVideoMuted = !state.isVideoMuted;
    },
    addChatMessage(state, action) {
      state.chatMessages.push(action.payload);
    },
    clearChatMessages(state) {
      state.chatMessages = [];
    },
    setQueuePosition(state, action) {
      state.queuePosition = action.payload.queue_position;
      state.estimatedWait = action.payload.estimated_wait_minutes;
    },
    resetConsultationState(state) {
      state.activeConsultation = null;
      state.sessionToken = null;
      state.queuePosition = null;
      state.estimatedWait = null;
      state.notes = [];
      state.chatMessages = [];
      state.callStatus = 'idle';
      state.isAudioMuted = false;
      state.isVideoMuted = false;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch consultations
      .addCase(fetchConsultations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchConsultations.fulfilled, (state, action) => {
        state.loading = false;
        const data = action.payload;
        state.consultations = data.results || data;
        state.pagination = {
          count: data.count || state.consultations.length,
          next: data.next || null,
          previous: data.previous || null,
        };
      })
      .addCase(fetchConsultations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch single
      .addCase(fetchConsultation.fulfilled, (state, action) => {
        state.activeConsultation = action.payload;
        state.notes = action.payload.notes || [];
      })
      // Join waiting room
      .addCase(joinWaitingRoom.fulfilled, (state, action) => {
        state.queuePosition = action.payload.queue_position;
        state.callStatus = 'connecting';
      })
      // Start consultation
      .addCase(startConsultation.fulfilled, (state, action) => {
        state.sessionToken = action.payload.session_token;
        state.callStatus = 'connected';
        if (state.activeConsultation) {
          state.activeConsultation.status = 'in_progress';
        }
      })
      // End consultation
      .addCase(endConsultation.fulfilled, (state) => {
        state.callStatus = 'ended';
        if (state.activeConsultation) {
          state.activeConsultation.status = 'completed';
        }
      })
      // Queue status
      .addCase(fetchQueueStatus.fulfilled, (state, action) => {
        state.queuePosition = action.payload.queue_position;
        state.estimatedWait = action.payload.estimated_wait_minutes;
      })
      // Notes
      .addCase(createConsultationNote.fulfilled, (state, action) => {
        state.notes.push(action.payload);
      });
  },
});

export const {
  clearError,
  setCallStatus,
  toggleAudioMute,
  toggleVideoMute,
  addChatMessage,
  clearChatMessages,
  setQueuePosition,
  resetConsultationState,
} = consultationSlice.actions;

export const selectConsultations = (state) => state.consultations.consultations;
export const selectActiveConsultation = (state) => state.consultations.activeConsultation;
export const selectSessionToken = (state) => state.consultations.sessionToken;
export const selectCallStatus = (state) => state.consultations.callStatus;
export const selectQueuePosition = (state) => state.consultations.queuePosition;
export const selectEstimatedWait = (state) => state.consultations.estimatedWait;
export const selectChatMessages = (state) => state.consultations.chatMessages;
export const selectConsultationNotes = (state) => state.consultations.notes;
export const selectIsAudioMuted = (state) => state.consultations.isAudioMuted;
export const selectIsVideoMuted = (state) => state.consultations.isVideoMuted;
export const selectConsultationLoading = (state) => state.consultations.loading;

export default consultationSlice.reducer;
