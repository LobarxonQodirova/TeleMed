/**
 * API functions for consultation-related endpoints.
 */
import api from './axiosConfig';

export const consultationApi = {
  /** Fetch paginated list of consultations. */
  getConsultations(params = {}) {
    return api.get('/consultations/', { params });
  },

  /** Fetch a single consultation by ID. */
  getConsultation(consultationId) {
    return api.get(`/consultations/${consultationId}/`);
  },

  /** Create a new consultation. */
  createConsultation(data) {
    return api.post('/consultations/', data);
  },

  /** Update a consultation. */
  updateConsultation(consultationId, data) {
    return api.patch(`/consultations/${consultationId}/`, data);
  },

  // ── Workflow Actions ─────────────────────────────────────────────────

  /** Patient joins the waiting room. */
  joinWaitingRoom(consultationId) {
    return api.post(`/consultations/${consultationId}/join_waiting_room/`);
  },

  /** Doctor starts a consultation. */
  startConsultation(consultationId) {
    return api.post(`/consultations/${consultationId}/start/`);
  },

  /** End an active consultation. */
  endConsultation(consultationId) {
    return api.post(`/consultations/${consultationId}/end/`);
  },

  /** Cancel a consultation. */
  cancelConsultation(consultationId) {
    return api.post(`/consultations/${consultationId}/cancel/`);
  },

  /** Check queue status for a waiting consultation. */
  getQueueStatus(consultationId) {
    return api.get(`/consultations/${consultationId}/queue_status/`);
  },

  // ── Notes ────────────────────────────────────────────────────────────

  /** Fetch notes for a consultation. */
  getNotes(consultationId) {
    return api.get(`/consultations/${consultationId}/notes/`);
  },

  /** Create a note for a consultation. */
  createNote(consultationId, data) {
    return api.post(`/consultations/${consultationId}/notes/`, data);
  },

  /** Update a consultation note. */
  updateNote(consultationId, noteId, data) {
    return api.patch(`/consultations/${consultationId}/notes/${noteId}/`, data);
  },

  /** Delete a consultation note. */
  deleteNote(consultationId, noteId) {
    return api.delete(`/consultations/${consultationId}/notes/${noteId}/`);
  },

  // ── Files ────────────────────────────────────────────────────────────

  /** Fetch files for a consultation. */
  getFiles(consultationId) {
    return api.get(`/consultations/${consultationId}/files/`);
  },

  /** Upload a file for a consultation. */
  uploadFile(consultationId, formData) {
    return api.post(`/consultations/${consultationId}/files/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /** Delete a file from a consultation. */
  deleteFile(consultationId, fileId) {
    return api.delete(`/consultations/${consultationId}/files/${fileId}/`);
  },
};

export default consultationApi;
