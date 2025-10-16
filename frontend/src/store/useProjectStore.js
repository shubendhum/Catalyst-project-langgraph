import { create } from 'zustand';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const useProjectStore = create((set, get) => ({
  projects: [],
  currentProject: null,
  tasks: [],
  currentTask: null,
  logs: [],
  
  fetchProjects: async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      set({ projects: response.data });
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  },
  
  createProject: async (name, description) => {
    try {
      const response = await axios.post(`${API}/projects`, { name, description });
      set((state) => ({ projects: [...state.projects, response.data] }));
      return response.data;
    } catch (error) {
      console.error('Failed to create project:', error);
      return null;
    }
  },
  
  fetchProject: async (projectId) => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}`);
      set({ currentProject: response.data });
    } catch (error) {
      console.error('Failed to fetch project:', error);
    }
  },
  
  fetchTasks: async (projectId) => {
    try {
      const response = await axios.get(`${API}/tasks?project_id=${projectId}`);
      set({ tasks: response.data });
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  },
  
  createTask: async (projectId, prompt) => {
    try {
      const response = await axios.post(`${API}/tasks`, { project_id: projectId, prompt });
      set((state) => ({ tasks: [...state.tasks, response.data] }));
      return response.data;
    } catch (error) {
      console.error('Failed to create task:', error);
      return null;
    }
  },
  
  fetchTask: async (taskId) => {
    try {
      const response = await axios.get(`${API}/tasks/${taskId}`);
      set({ currentTask: response.data });
    } catch (error) {
      console.error('Failed to fetch task:', error);
    }
  },
  
  fetchLogs: async (taskId) => {
    try {
      const response = await axios.get(`${API}/logs/${taskId}`);
      set({ logs: response.data });
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  },
  
  addLog: (log) => {
    set((state) => ({ logs: [...state.logs, log] }));
  },
  
  updateTaskStatus: (taskId, status, graphState) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, status, graph_state: graphState } : t
      ),
      currentTask:
        state.currentTask?.id === taskId
          ? { ...state.currentTask, status, graph_state: graphState }
          : state.currentTask,
    }));
  },
}));