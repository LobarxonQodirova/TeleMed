/**
 * API functions for doctor-related endpoints.
 */
import api from './axiosConfig';

export const doctorApi = {
  /** Fetch paginated list of doctors with optional filters. */
  getDoctors(params = {}) {
    return api.get('/auth/doctors/', { params });
  },

  /** Fetch a single doctor profile by ID. */
  getDoctor(doctorId) {
    return api.get(`/auth/doctors/${doctorId}/`);
  },

  /** Fetch the authenticated doctor's own profile. */
  getMyProfile() {
    return api.get('/auth/doctors/my_profile/');
  },

  /** Update a doctor profile. */
  updateProfile(doctorId, data) {
    return api.patch(`/auth/doctors/${doctorId}/`, data);
  },

  /** Fetch specialties list. */
  getSpecialties(params = {}) {
    return api.get('/auth/specialties/', { params });
  },

  /** Fetch sub-specializations. */
  getSpecializations(params = {}) {
    return api.get('/doctors/specializations/', { params });
  },

  // ── Schedules ────────────────────────────────────────────────────────────

  /** Fetch schedules for a specific doctor. */
  getDoctorSchedules(doctorId) {
    return api.get(`/doctors/${doctorId}/schedules/`);
  },

  /** Fetch the authenticated doctor's schedules. */
  getMySchedules() {
    return api.get('/doctors/schedules/');
  },

  /** Create a schedule entry. */
  createSchedule(data) {
    return api.post('/doctors/schedules/', data);
  },

  /** Update a schedule entry. */
  updateSchedule(scheduleId, data) {
    return api.patch(`/doctors/schedules/${scheduleId}/`, data);
  },

  /** Delete a schedule entry. */
  deleteSchedule(scheduleId) {
    return api.delete(`/doctors/schedules/${scheduleId}/`);
  },

  /** Bulk-create schedule entries. */
  bulkCreateSchedules(data) {
    return api.post('/doctors/schedules/bulk_create/', data);
  },

  /** Fetch available slots for a doctor on a date. */
  getAvailableSlots(doctorId, date) {
    return api.get('/doctors/schedules/available_slots/', {
      params: { doctor_id: doctorId, date },
    });
  },

  // ── Reviews ──────────────────────────────────────────────────────────────

  /** Fetch reviews for a doctor. */
  getDoctorReviews(doctorId) {
    return api.get(`/doctors/${doctorId}/reviews/`);
  },

  /** Submit a review for a doctor. */
  createReview(doctorId, data) {
    return api.post(`/doctors/${doctorId}/reviews/`, data);
  },

  /** Doctor responds to a review. */
  respondToReview(reviewId, response) {
    return api.post(`/doctors/reviews/${reviewId}/respond/`, { response });
  },

  /** Fetch review summary/stats for a doctor. */
  getReviewSummary(doctorId) {
    return api.get('/doctors/reviews/summary/', {
      params: { doctor_id: doctorId },
    });
  },
};

export default doctorApi;
