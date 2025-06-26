
import { api } from './api';

export interface TradingAccount {
  id: string;
  user_id: string;
  name: string;
  broker?: string;
  account_type?: 'sim' | 'funded' | 'live' | 'demo';
  account_number?: string;
  is_active: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAccountData {
  name: string;
  broker?: string;
  account_type?: 'sim' | 'funded' | 'live' | 'demo';
  account_number?: string;
}

export interface UpdateAccountData {
  name?: string;
  broker?: string;
  account_type?: 'sim' | 'funded' | 'live' | 'demo';
  account_number?: string;
  is_active?: string;
}

export const accountsService = {
  async getAccounts(): Promise<TradingAccount[]> {
    const response = await api.get('/accounts/');
    return response.data;
  },

  async getAccount(accountId: string): Promise<TradingAccount> {
    const response = await api.get(`/accounts/${accountId}`);
    return response.data;
  },

  async createAccount(accountData: CreateAccountData): Promise<TradingAccount> {
    const response = await api.post('/accounts/', accountData);
    return response.data;
  },

  async updateAccount(accountId: string, updateData: UpdateAccountData): Promise<TradingAccount> {
    const response = await api.put(`/accounts/${accountId}`, updateData);
    return response.data;
  },

  async deleteAccount(accountId: string): Promise<void> {
    await api.delete(`/accounts/${accountId}`);
  }
};
