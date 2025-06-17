// Using @/api alias now that tsconfig is updated
import apiClient from '@/api';

// Define interfaces manually as OpenAPI spec is just a placeholder
interface LoginRequest {
  username?: string;
  password?: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const loginUser = async (credentials: LoginRequest): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username || '');
  formData.append('password', credentials.password || '');

  // Using the manually configured apiClient for this specific /auth/token call
  // as it uses 'application/x-www-form-urlencoded'
  const response = await apiClient.post<TokenResponse>('/auth/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};
