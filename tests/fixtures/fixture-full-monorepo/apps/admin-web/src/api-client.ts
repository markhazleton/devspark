// This import references another registered app path for inference testing
import { AdminService } from '../../admin-api/src/services';
import { AuthToken } from '../../../libs/shared-auth/src/auth';

export class ApiClient {
  private adminService: AdminService;

  constructor(token: AuthToken) {
    this.adminService = new AdminService(token);
  }
}
