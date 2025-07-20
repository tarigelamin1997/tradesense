import { api } from './client';

// Types
export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
}

export interface WidgetPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  position: WidgetPosition;
  data_source: string;
  data_config: Record<string, any>;
  refresh_interval?: number;
  interactive?: boolean;
  exportable?: boolean;
  linked_widgets?: string[];
  custom_styles?: Record<string, any>;
}

export interface DashboardLayout {
  id: string;
  name: string;
  columns: number;
  row_height: number;
  margin: number[];
  responsive_breakpoints: Record<string, number>;
}

export interface Dashboard {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  template: string;
  layout: DashboardLayout;
  widgets: WidgetConfig[];
  shared_with: string[];
  is_public: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
  last_accessed: string;
}

export interface DashboardFilter {
  template?: string;
  tags?: string[];
  is_public?: boolean;
  search?: string;
}

export interface WidgetType {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface DataSource {
  id: string;
  name: string;
  description: string;
}

// API Service
export const dashboardsApi = {
  // Dashboard Management
  async create(name: string, template: string = 'custom', description?: string): Promise<Dashboard> {
    return api.post('/api/v1/dashboards/', null, {
      params: { name, template, description }
    });
  },

  async list(filters?: DashboardFilter & { page?: number; page_size?: number }): Promise<{
    dashboards: Dashboard[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
      pages: number;
    };
  }> {
    return api.get('/api/v1/dashboards/', { params: filters });
  },

  async get(id: string): Promise<Dashboard> {
    return api.get(`/api/v1/dashboards/${id}`);
  },

  async update(id: string, updates: Partial<Dashboard>): Promise<Dashboard> {
    return api.put(`/api/v1/dashboards/${id}`, updates);
  },

  async delete(id: string): Promise<{ message: string }> {
    return api.delete(`/api/v1/dashboards/${id}`);
  },

  async clone(id: string, newName: string): Promise<Dashboard> {
    return api.post(`/api/v1/dashboards/${id}/clone`, null, {
      params: { new_name: newName }
    });
  },

  async share(id: string, userIds: string[]): Promise<Dashboard> {
    return api.post(`/api/v1/dashboards/${id}/share`, { user_ids: userIds });
  },

  // Widget Management
  async addWidget(dashboardId: string, widget: Omit<WidgetConfig, 'id'>): Promise<Dashboard> {
    return api.post(`/api/v1/dashboards/${dashboardId}/widgets`, widget);
  },

  async updateWidget(
    dashboardId: string, 
    widgetId: string, 
    updates: Partial<WidgetConfig>
  ): Promise<Dashboard> {
    return api.put(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`, updates);
  },

  async removeWidget(dashboardId: string, widgetId: string): Promise<Dashboard> {
    return api.delete(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`);
  },

  async reorderWidgets(
    dashboardId: string, 
    positions: Array<{ widget_id: string; position: WidgetPosition }>
  ): Promise<Dashboard> {
    return api.put(`/api/v1/dashboards/${dashboardId}/widgets/reorder`, positions);
  },

  // Widget Types and Data Sources
  async getWidgetTypes(): Promise<WidgetType[]> {
    return api.get('/api/v1/dashboards/widgets/types');
  },

  async getDataSources(): Promise<DataSource[]> {
    return api.get('/api/v1/dashboards/widgets/data-sources');
  },

  async getTemplates(): Promise<DashboardTemplate[]> {
    return api.get('/api/v1/dashboards/templates');
  },

  // Data Fetching
  async getWidgetData(
    dashboardId: string, 
    widgetId: string,
    options?: {
      time_range?: Record<string, any>;
      filters?: Record<string, any>;
      page?: number;
      page_size?: number;
    }
  ): Promise<any> {
    return api.post(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}/data`, options || {});
  },

  async getDashboardData(
    dashboardId: string,
    timeRange?: Record<string, any>
  ): Promise<{
    dashboard: Dashboard;
    widget_data: Record<string, any>;
  }> {
    return api.get(`/api/v1/dashboards/${dashboardId}/data`, {
      params: timeRange ? { time_range: JSON.stringify(timeRange) } : undefined
    });
  },

  // Real-time streaming
  streamDashboardData(dashboardId: string): EventSource {
    const token = localStorage.getItem('authToken');
    return new EventSource(
      `/api/v1/dashboards/${dashboardId}/data/stream?token=${token}`
    );
  },

  // Export
  async exportDashboard(
    dashboardId: string, 
    format: 'json' | 'csv' | 'excel' = 'json',
    includeConfig: boolean = false
  ): Promise<any> {
    return api.post(`/api/v1/dashboards/${dashboardId}/export`, null, {
      params: { format, include_config: includeConfig }
    });
  }
};