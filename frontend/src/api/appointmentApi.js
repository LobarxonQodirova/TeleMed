/**
 * API functions for appointment-related endpoints.
 */
import api from './axiosConfig';

export const appointmentApi = {
  /** Fetch paginated list of appointments with optional filters. */
  getAppointments(params = {}) {
    return api.get('/appointments/', { params });
  },

  /** Fetch a single appointment by ID. */
  getAppointment(appointmentId) {
    return api.get(`/appointments/${appointmentId}/`);
  },

  /** Create a new appointment. */
  createAppointment(data) {
    return api.post('/appointments/', data);
  },

  /** Update an appointment. */
  updateAppointment(appointmentId, data) {
    return api.patch(`/appointments/${appointmentId}/`, data);
  },

  /** Confirm an appointment (doctor action). */
  confirmAppointment(appointmentId) {
    return api.post(`/appointments/${appointmentId}/confirm/`);
  },

  /** Check in for an appointment (patient action). */
  checkInAppointment(appointmentId) {
    return api.post(`/appointments/${appointmentId}/check_in/`);
  },

  /** Cancel an appointment with a reason. */
  cancelAppointment(appointmentId, data) {
    return api.post(`/appointments/${appointmentId}/cancel/`, data);
  },

  /** Reschedule an appointment. */
  rescheduleAppointment(appointmentId, data) {
    return api.post(`/appointments/${appointmentId}/reschedule/`, data);
  },

  /** Fetch upcoming appointments. */
  getUpcoming() {
    return api.get('/appointments/upcoming/');
  },

  // ── Time Slots ────────────────────────────────────────────────────────

  /** Fetch time slots with optional filters. */
  getTimeSlots(params = {}) {
    return api.get('/appointments/slots/', { params });
  },

  /** Generate time slots from schedule (doctor action). */
  generateSlots(data) {
    return api.post('/appointments/slots/generate/', data);
  },

  /** Block/unblock a time slot. */
  updateSlot(slotId, data) {
    return api.patch(`/appointments/slots/${slotId}/`, data);
  },
};

export default appointmentApi;
