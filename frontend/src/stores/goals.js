import { defineStore } from 'pinia'
import api from '../services/api'

export const useGoalStore = defineStore('goals', {
  state: () => ({
    currentSheet: null,
    windows: [],
    loading: false,
    error: null,
  }),
  getters: {
    goals: (state) => state.currentSheet?.goals || [],
    sheetStatus: (state) => state.currentSheet?.status || 'none',
    totalWeightage: (state) => {
      if (!state.currentSheet?.goals) return 0
      return state.currentSheet.goals.reduce((sum, g) => sum + g.weightage, 0)
    },
    remainingWeightage() { return 100 - this.totalWeightage },
    goalCount: (state) => state.currentSheet?.goals?.length || 0,
  },
  actions: {
    async fetchSheet(cycleId) {
      this.loading = true
      try {
        const params = cycleId ? { cycle_id: cycleId } : {}
        const { data } = await api.get('/goals/sheet', { params })
        this.currentSheet = data.sheet
        this.windows = data.windows || []
      } catch (e) {
        this.error = e.response?.data?.error || 'Failed to fetch goals'
      } finally {
        this.loading = false
      }
    },
    async createSheet(cycleId) {
      const { data } = await api.post('/goals/sheet', { cycle_id: cycleId })
      this.currentSheet = data.sheet
      return data.sheet
    },
    async addGoal(sheetId, goal) {
      const { data } = await api.post(`/goals/sheet/${sheetId}/goals`, goal)
      await this.fetchSheet()
      return data.goal
    },
    async updateGoal(goalId, updates) {
      const { data } = await api.put(`/goals/goals/${goalId}`, updates)
      await this.fetchSheet()
      return data.goal
    },
    async deleteGoal(goalId) {
      await api.delete(`/goals/goals/${goalId}`)
      await this.fetchSheet()
    },
    async submitSheet(sheetId) {
      const { data } = await api.post(`/goals/sheet/${sheetId}/submit`)
      this.currentSheet = data.sheet
      return data.sheet
    },
    async logAchievement(payload) {
      const { data } = await api.post('/goals/achievements', payload)
      return data.achievement
    },
  },
})
